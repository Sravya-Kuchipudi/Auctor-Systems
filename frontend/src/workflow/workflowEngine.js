// Auctor Systems — Orchestrator Workflow Engine
// Controls execution, state machine transitions, handoffs, and interactive user prompts

import { AGENT_STATES, ORCHESTRATOR_STATES } from './workflowTypes';
import {
  getScenarioForPrompt,
  DEFAULT_STUDENT_PRODUCTIVITY_HTML,
  DEFAULT_STUDENT_PRODUCTIVITY_CSS,
  DEFAULT_STUDENT_PRODUCTIVITY_JS,
  DEFAULT_README_MD,
  DEFAULT_ARCHITECTURE_MD,
  DEFAULT_LAUNCH_COPY_MD,
  DEFAULT_VERCEL_JSON,
} from './demoScenarios';
import { AGENTS } from '../components/office/agentData';

export class WorkflowEngine {
  constructor(handlers = {}) {
    this.handlers = handlers;
    this.isRunning = false;
    this.timer = null;
    this.currentStepIndex = 0;
    this.scenario = [];
    this.isWaitingUser = false;
    this.userPrompt = '';

    // Internal State
    this.agentStatuses = {};
    AGENTS.forEach((a) => {
      this.agentStatuses[a.backendName] = AGENT_STATES.IDLE;
    });

    this.orchestratorState = {
      status: ORCHESTRATOR_STATES.IDLE,
      statusText: 'Orchestrator Ready',
      currentAgent: null,
      activeHandoff: null,
      completedAgents: [],
      pendingAgents: AGENTS.map((a) => a.backendName),
      userInputRequired: false,
      pendingQuestion: null,
    };
  }

  // Start the deterministic 8-agent workflow
  start(prompt) {
    this.cancel();
    this.isRunning = true;
    this.userPrompt = prompt;
    this.scenario = getScenarioForPrompt(prompt);
    this.currentStepIndex = 0;
    this.isWaitingUser = false;

    // Reset agent statuses
    this.agentStatuses = {};
    AGENTS.forEach((a) => {
      this.agentStatuses[a.backendName] = AGENT_STATES.IDLE;
    });

    this.orchestratorState = {
      status: ORCHESTRATOR_STATES.ORCHESTRATING,
      statusText: 'Orchestrator analyzing directive...',
      currentAgent: null,
      activeHandoff: null,
      completedAgents: [],
      pendingAgents: AGENTS.map((a) => a.backendName),
      userInputRequired: false,
      pendingQuestion: null,
    };

    this._notifyOrchestrator();
    this._notifyAgents();

    // Kick off first step after brief orchestrator planning delay
    this.timer = setTimeout(() => {
      this._runNextStep();
    }, 600);
  }

  // User submits answer to a pending question
  answerQuestion(answerText) {
    if (!this.isWaitingUser) return;
    this.isWaitingUser = false;

    // Log answer event
    const answerEvent = {
      id: `evt-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      from: 'user',
      to: this.orchestratorState.currentAgent || 'requirements',
      type: 'answer',
      message: `User responded: "${answerText}"`,
      status: 'completed',
    };

    if (this.handlers.onActivityEvent) {
      this.handlers.onActivityEvent(answerEvent);
    }

    // Update Orchestrator state back to working
    this.orchestratorState.status = ORCHESTRATOR_STATES.WORKING;
    this.orchestratorState.statusText = 'Client input received. Resuming workflow...';
    this.orchestratorState.userInputRequired = false;
    this.orchestratorState.pendingQuestion = null;
    this._notifyOrchestrator();

    // Set Beatrice back to working
    const currAgent = this.orchestratorState.currentAgent || 'requirements';
    this.agentStatuses[currAgent] = AGENT_STATES.WORKING;
    this._notifyAgents();

    // Continue next step
    this.currentStepIndex++;
    this.timer = setTimeout(() => {
      this._runNextStep();
    }, 500);
  }

  _runNextStep() {
    if (!this.isRunning || this.currentStepIndex >= this.scenario.length) {
      this._finish();
      return;
    }

    const step = this.scenario[this.currentStepIndex];
    const agentId = step.agentId;
    const agentObj = AGENTS.find((a) => a.id === agentId);
    const backendName = agentObj ? agentObj.backendName : agentId;

    // Handle Question Event
    if (step.type === 'question') {
      this.isWaitingUser = true;
      this.agentStatuses[backendName] = AGENT_STATES.COMMUNICATING;
      this._notifyAgents();

      this.orchestratorState.status = ORCHESTRATOR_STATES.WAITING_USER;
      this.orchestratorState.statusText = `${step.agentName} awaiting client clarification`;
      this.orchestratorState.userInputRequired = true;
      this.orchestratorState.pendingQuestion = {
        agentId: step.agentId,
        agentName: step.agentName,
        role: step.role,
        question: step.question,
        options: step.options || [],
      };
      this._notifyOrchestrator();

      // Emit question event to activity log
      const questionEvent = {
        id: `evt-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        from: step.agentId,
        fromName: step.agentName,
        type: 'question',
        message: `${step.agentName}: "${step.question}"`,
        status: 'thinking',
      };
      if (this.handlers.onActivityEvent) {
        this.handlers.onActivityEvent(questionEvent);
      }

      if (this.handlers.onQuestionPrompt) {
        this.handlers.onQuestionPrompt(this.orchestratorState.pendingQuestion);
      }
      return; // Execution pauses until answerQuestion is invoked!
    }

    // Handle Handoff Event
    if (step.type === 'handoff') {
      this.agentStatuses[backendName] = AGENT_STATES.COMPLETED;
      if (!this.orchestratorState.completedAgents.includes(backendName)) {
        this.orchestratorState.completedAgents.push(backendName);
      }

      const toAgentId = step.toAgentId;
      const toAgentObj = AGENTS.find((a) => a.id === toAgentId);
      const toBackendName = toAgentObj ? toAgentObj.backendName : toAgentId;

      this.orchestratorState.status = ORCHESTRATOR_STATES.ORCHESTRATING;
      this.orchestratorState.statusText = `Handoff: ${step.agentName} → ${step.toAgentName}...`;
      this.orchestratorState.activeHandoff = {
        from: agentId,
        to: toAgentId,
        fromIndex: AGENTS.findIndex((a) => a.id === agentId),
        toIndex: AGENTS.findIndex((a) => a.id === toAgentId),
      };
      this._notifyOrchestrator();

      // Activate handoff indicator on next agent
      if (toBackendName) {
        this.agentStatuses[toBackendName] = AGENT_STATES.COMMUNICATING;
      }
      this._notifyAgents();

      // Log handoff event
      const handoffEvent = {
        id: `evt-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        from: agentId,
        fromName: step.agentName,
        to: toAgentId,
        toName: step.toAgentName,
        type: 'handoff',
        message: step.message,
        status: 'communicating',
      };
      if (this.handlers.onActivityEvent) {
        this.handlers.onActivityEvent(handoffEvent);
      }

      // Transition to next agent working after brief handoff duration
      this.currentStepIndex++;
      this.timer = setTimeout(() => {
        this.orchestratorState.activeHandoff = null;
        this._runNextStep();
      }, step.delay || 1000);
      return;
    }

    // Handle Review / QA Loop Event
    if (step.type === 'review') {
      this.agentStatuses[backendName] = AGENT_STATES.COMMUNICATING;
      this._notifyAgents();

      const toAgentId = step.toAgentId;
      const reviewEvent = {
        id: `evt-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        from: agentId,
        fromName: step.agentName,
        to: toAgentId,
        toName: step.toAgentName,
        type: 'review',
        message: step.message,
        status: 'error',
      };
      if (this.handlers.onActivityEvent) {
        this.handlers.onActivityEvent(reviewEvent);
      }

      this.currentStepIndex++;
      this.timer = setTimeout(() => {
        this._runNextStep();
      }, step.delay || 1100);
      return;
    }

    // Standard Agent Activity (Thinking, Working, Dialogue, Completed)
    const agentIndex = AGENTS.findIndex((a) => a.id === agentId);
    this.orchestratorState.currentAgent = backendName;
    this.orchestratorState.status = ORCHESTRATOR_STATES.WORKING;
    this.orchestratorState.statusText = `${step.agentName} (${step.role}) is active`;

    if (step.type === 'thinking') {
      this.agentStatuses[backendName] = AGENT_STATES.THINKING;
    } else if (step.type === 'working') {
      this.agentStatuses[backendName] = AGENT_STATES.WORKING;
    } else if (step.type === 'completed') {
      this.agentStatuses[backendName] = AGENT_STATES.COMPLETED;
      if (!this.orchestratorState.completedAgents.includes(backendName)) {
        this.orchestratorState.completedAgents.push(backendName);
      }
    }

    this._notifyOrchestrator();
    this._notifyAgents(agentIndex, backendName, step.message);

    // Record activity log event
    const logEvent = {
      id: `evt-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      from: agentId,
      fromName: step.agentName,
      type: step.type,
      message: step.message,
      status: this.agentStatuses[backendName],
    };
    if (this.handlers.onActivityEvent) {
      this.handlers.onActivityEvent(logEvent);
    }

    this.currentStepIndex++;
    this.timer = setTimeout(() => {
      this._runNextStep();
    }, step.delay || 1000);
  }

  _finish() {
    this.isRunning = false;
    this.orchestratorState.status = ORCHESTRATOR_STATES.COMPLETED;
    this.orchestratorState.statusText = 'All 8 Agents Concluded. Website is Live.';
    this.orchestratorState.currentAgent = null;
    this.orchestratorState.activeHandoff = null;

    // Mark all agents as completed
    AGENTS.forEach((a) => {
      this.agentStatuses[a.backendName] = AGENT_STATES.COMPLETED;
    });

    this._notifyOrchestrator();
    this._notifyAgents(-1, null, null);

    // Emit final completion event
    const completionEvent = {
      id: `evt-${Date.now()}-complete`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      from: 'orchestrator',
      fromName: 'Auctor Orchestrator',
      type: 'completed',
      message: 'Website generation and testing finished successfully. Ready for inspection and export.',
      status: 'completed',
    };
    if (this.handlers.onActivityEvent) {
      this.handlers.onActivityEvent(completionEvent);
    }

    // Provide generated mock files payload so Live Preview & Code Inspector render
    if (this.handlers.onFilesGenerated) {
      this.handlers.onFilesGenerated([
        { filename: 'index.html', path: 'src/index.html', content: DEFAULT_STUDENT_PRODUCTIVITY_HTML },
        { filename: 'style.css', path: 'src/style.css', content: DEFAULT_STUDENT_PRODUCTIVITY_CSS },
        { filename: 'script.js', path: 'src/script.js', content: DEFAULT_STUDENT_PRODUCTIVITY_JS },
        { filename: 'README.md', path: 'README.md', content: DEFAULT_README_MD },
        { filename: 'README.md', path: 'docs/README.md', content: DEFAULT_README_MD },
        { filename: 'ARCHITECTURE.md', path: 'docs/ARCHITECTURE.md', content: DEFAULT_ARCHITECTURE_MD },
        { filename: 'vercel.json', path: 'deploy/vercel.json', content: DEFAULT_VERCEL_JSON },
        { filename: 'LAUNCH_COPY.md', path: 'marketing/LAUNCH_COPY.md', content: DEFAULT_LAUNCH_COPY_MD },
      ]);
    }
  }

  cancel() {
    this.isRunning = false;
    this.isWaitingUser = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  _notifyOrchestrator() {
    if (this.handlers.onOrchestratorUpdate) {
      this.handlers.onOrchestratorUpdate({ ...this.orchestratorState });
    }
  }

  _notifyAgents(currIndex = -1, currName = null, snippet = null) {
    if (this.handlers.onAgentStateChange) {
      this.handlers.onAgentStateChange({ ...this.agentStatuses }, currIndex, currName, snippet);
    }
  }
}
