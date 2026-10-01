import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client';
import { SSEStreamListener } from '../api/sse';
import { AGENTS } from '../components/office/agentData';
import { WorkflowEngine } from '../workflow/workflowEngine';
import { AGENT_STATES, ORCHESTRATOR_STATES } from '../workflow/workflowTypes';

const ProjectContext = createContext(null);

// Helper to resolve an agent object from ID, backendName, or display name
const findAgent = (query) => {
  if (!query) return null;
  const q = String(query).toLowerCase();
  return (
    AGENTS.find(
      (a) =>
        a.id.toLowerCase() === q ||
        a.backendName.toLowerCase() === q ||
        a.name.toLowerCase() === q ||
        a.name.toLowerCase().includes(q)
    ) || null
  );
};

export function ProjectProvider({ children }) {
  // ── Application & Connection State ─────────────────────────────────────────
  const [backendStatus, setBackendStatus] = useState({
    healthy: false,
    model: '',
    geminiConfigured: false,
    vercelConfigured: false,
    loading: true,
  });

  // ── Project State ──────────────────────────────────────────────────────────
  const [projectId, setProjectId] = useState(null);
  const [userPrompt, setUserPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState(null);
  const [projectState, setProjectState] = useState(null);
  const [projectsList, setProjectsList] = useState([]);
  const [revisions, setRevisions] = useState([]);
  const [revisionCount, setRevisionCount] = useState(0);

  // ── Orchestrator State (Living Office & Header & Chat) ─────────────────────
  const [orchestratorState, setOrchestratorState] = useState({
    status: ORCHESTRATOR_STATES.IDLE,
    statusText: 'Orchestrator Ready',
    currentAgent: null,
    activeHandoff: null,
    completedAgents: [],
    pendingAgents: AGENTS.map((a) => a.backendName),
    userInputRequired: false,
    pendingQuestion: null,
  });

  // ── Activity Stream & Event Log ────────────────────────────────────────────
  const [activityLog, setActivityLog] = useState([]);
  const [eventLogs, setEventLogs] = useState([]);
  const [completionSummary, setCompletionSummary] = useState(null);

  // ── 8 Agents Workflow State ────────────────────────────────────────────────
  const [currentAgentIndex, setCurrentAgentIndex] = useState(-1);
  const [currentAgentName, setCurrentAgentName] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState(() => {
    const initial = {};
    AGENTS.forEach((agent) => {
      initial[agent.backendName] = AGENT_STATES.IDLE;
    });
    return initial;
  });
  const [agentSnippets, setAgentSnippets] = useState({});

  // ── Output, Files & Preview ────────────────────────────────────────────────
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [codeCache, setCodeCache] = useState({});
  const [activeCodeFilename, setActiveCodeFilename] = useState('index.html');
  const [previewDevice, setPreviewDevice] = useState('desktop'); // desktop | tablet | mobile
  const [previewRefreshKey, setPreviewRefreshKey] = useState(Date.now());
  const [activeTab, setActiveTab] = useState('preview'); // preview | code

  // ── Documentation Viewer & Download ───────────────────────────────────────
  const [isDocViewerOpen, setIsDocViewerOpen] = useState(false);
  const [docViewerDoc, setDocViewerDoc] = useState('README.md');

  const openDocViewer = useCallback((docName = 'README.md') => {
    setDocViewerDoc(docName);
    setIsDocViewerOpen(true);
  }, []);

  const closeDocViewer = useCallback(() => {
    setIsDocViewerOpen(false);
  }, []);

  // References
  const sseRef = useRef(null);
  const workflowEngineRef = useRef(null);

  // ── Check Backend Health on Mount ──────────────────────────────────────────
  const fetchHealth = useCallback(async () => {
    try {
      const data = await api.getHealth();
      setBackendStatus({
        healthy: data.status === 'healthy',
        model: data.config?.model || 'configured model',
        geminiConfigured: Boolean(data.config?.gemini_configured),
        vercelConfigured: Boolean(data.config?.vercel_configured),
        loading: false,
      });
    } catch (err) {
      setBackendStatus({
        healthy: false,
        model: '',
        geminiConfigured: false,
        vercelConfigured: false,
        loading: false,
      });
    }
  }, []);


  // ── Refresh Files and Preview from Backend ─────────────────────────────────
  const loadProjectFiles = useCallback(async (pid) => {
    if (!pid || pid === 'kairos-academic-studio') return;
    try {
      const res = await api.getProjectFiles(pid);
      const files = res.files || res || [];
      if (Array.isArray(files) && files.length > 0) {
        setGeneratedFiles(files);

        const cache = {};
        for (const file of files) {
          const fname = file.filename || (file.path ? file.path.split('/').pop() : '');
          let content = file.content;
          if (!content) {
            try {
              content = await api.getFileContent(pid, file.path || fname);
            } catch {
              // ignore single file fetch error
            }
          }
          if (content !== undefined) {
            if (fname) cache[fname] = content;
            if (file.path) cache[file.path] = content;
          }
        }
        setCodeCache((prev) => ({ ...prev, ...cache }));
        setPreviewRefreshKey(Date.now());
      }
    } catch (err) {
      console.warn('[ProjectContext] Failed to load files from backend:', err);
    }
  }, []);

  // ── Server-Sent Events (SSE) Stream Connection ─────────────────────────────
  const connectSSE = useCallback((pid) => {
    if (sseRef.current) {
      sseRef.current.disconnect();
    }

    const listener = new SSEStreamListener(pid, {
      onOpen: () => {
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'info', text: 'Real-time agent stream connected.' },
        ]);
      },

      onWorkflowEvent: (event) => {
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        // Add to activityLog if message is present
        if (event.message && event.type !== 'heartbeat') {
          const targetAgent = findAgent(event.agent || event.agent_name || event.from);
          setActivityLog((prev) => [
            ...prev,
            {
              id: event.id || `act-${Date.now()}-${Math.random()}`,
              type: event.type,
              agent: targetAgent?.id || event.agent || 'orchestrator',
              agentName: targetAgent?.name || event.agent_name || 'Auctor Orchestrator',
              message: event.message,
              timestamp: time,
              data: event.data,
            },
          ]);
        }
      },

      onWorkflowStarted: (event) => {
        setIsGenerating(true);
        setOrchestratorState((prev) => ({
          ...prev,
          status: ORCHESTRATOR_STATES.ORCHESTRATING,
          statusText: '8-Agent Pipeline Initiated',
        }));
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'started', text: event.message || 'Pipeline started.' },
        ]);
      },

      onAgentStarted: (event) => {
        const targetAgent = findAgent(event.agent || event.agent_name);
        if (targetAgent) {
          const key = targetAgent.backendName;
          setCurrentAgentIndex(targetAgent.index);
          setCurrentAgentName(key);
          setAgentStatuses((prev) => ({
            ...prev,
            [key]: AGENT_STATES.WORKING,
          }));
          setOrchestratorState((prev) => ({
            ...prev,
            status: ORCHESTRATOR_STATES.WORKING,
            currentAgent: targetAgent.id,
            statusText: `${targetAgent.name} Working`,
          }));
        }
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'agent', text: event.message },
        ]);
      },

      onAgentThinking: (event) => {
        const targetAgent = findAgent(event.agent || event.agent_name);
        if (targetAgent) {
          const key = targetAgent.backendName;
          setAgentStatuses((prev) => ({
            ...prev,
            [key]: AGENT_STATES.THINKING,
          }));
          const thought = event.data?.thought || event.message;
          if (thought) {
            setAgentSnippets((prev) => ({ ...prev, [key]: thought }));
          }
        }
      },

      onAgentWorking: (event) => {
        const targetAgent = findAgent(event.agent || event.agent_name);
        if (targetAgent) {
          const key = targetAgent.backendName;
          setAgentStatuses((prev) => ({
            ...prev,
            [key]: AGENT_STATES.WORKING,
          }));
          const snippet = event.data?.snippet || event.message;
          if (snippet) {
            setAgentSnippets((prev) => ({ ...prev, [key]: snippet }));
          }
        }
      },

      onAgentHandoff: (event) => {
        const fromAgent = findAgent(event.from || event.from_agent || event.agent);
        const toAgent = findAgent(event.to || event.to_agent);
        if (fromAgent) {
          setAgentStatuses((prev) => ({
            ...prev,
            [fromAgent.backendName]: AGENT_STATES.COMMUNICATING,
          }));
        }
        setOrchestratorState((prev) => ({
          ...prev,
          activeHandoff: {
            from: fromAgent?.id || event.from,
            to: toAgent?.id || event.to,
            message: event.message,
          },
          statusText: `Handoff: ${fromAgent?.name || 'Agent'} → ${toAgent?.name || 'Agent'}`,
        }));
      },

      onAgentCompleted: (event) => {
        const targetAgent = findAgent(event.agent || event.agent_name);
        if (targetAgent) {
          const key = targetAgent.backendName;
          setAgentStatuses((prev) => ({
            ...prev,
            [key]: AGENT_STATES.COMPLETED,
          }));
          setOrchestratorState((prev) => ({
            ...prev,
            completedAgents: [...new Set([...prev.completedAgents, key])],
            activeHandoff: null,
          }));
        }
        loadProjectFiles(pid);
      },

      onUserInputRequired: (event) => {
        const questionData = event.data || {
          question: event.message,
          options: [],
          agentName: 'Beatrice Stone',
          agentRole: 'Systems Requirements Analyst',
        };
        setOrchestratorState((prev) => ({
          ...prev,
          status: ORCHESTRATOR_STATES.WAITING_USER,
          statusText: 'Awaiting User Clarification',
          userInputRequired: true,
          pendingQuestion: questionData,
        }));
        setAgentStatuses((prev) => ({
          ...prev,
          Requirements: AGENT_STATES.THINKING,
        }));
      },

      onTestFailed: (event) => {
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'test', text: `QA Audit Flag: ${event.message}` },
        ]);
        loadProjectFiles(pid);
      },

      onTestPassed: (event) => {
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'test', text: `QA Passed: ${event.message}` },
        ]);
      },

      onProjectGenerated: (event) => {
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'code', text: event.message || 'Codebase compiled.' },
        ]);
        loadProjectFiles(pid);
      },

      onRevisionStarted: (event) => {
        setIsGenerating(true);
        setOrchestratorState((prev) => ({
          ...prev,
          status: ORCHESTRATOR_STATES.WORKING,
          statusText: `Revision In Progress: ${event.message || 'Targeted modifications'}`,
        }));
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'started', text: event.message || 'Revision directive received.' },
        ]);
      },

      onCodeModified: (event) => {
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'code', text: event.message || 'Files modified by Maya.' },
        ]);
        loadProjectFiles(pid);
      },

      onQaVerified: (event) => {
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'test', text: event.message || 'Astrid differential QA verified.' },
        ]);
      },

      onRevisionCompleted: (event) => {
        setIsGenerating(false);
        setCurrentAgentIndex(-1);
        setCurrentAgentName(null);
        setOrchestratorState((prev) => ({
          ...prev,
          status: ORCHESTRATOR_STATES.COMPLETED,
          statusText: 'Revision Applied Successfully',
          userInputRequired: false,
          pendingQuestion: null,
        }));
        if (event.data?.revision_number !== undefined) {
          setRevisionCount(event.data.revision_number);
        } else if (event.data?.revision_count !== undefined) {
          setRevisionCount(event.data.revision_count);
        } else {
          setRevisionCount((prev) => prev + 1);
        }
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'success', text: event.message || 'Revision complete.' },
        ]);
        loadProjectFiles(pid);
        api.getProjectRevisions(pid).then((r) => setRevisions(r?.revisions || [])).catch(() => {});
        api.listProjects().then((l) => setProjectsList(l || [])).catch(() => {});
      },

      onWorkflowCompleted: (event) => {
        setIsGenerating(false);
        setCurrentAgentIndex(-1);
        setCurrentAgentName(null);
        setAgentStatuses((prev) => {
          const allDone = { ...prev };
          AGENTS.forEach((a) => {
            allDone[a.backendName] = AGENT_STATES.COMPLETED;
          });
          return allDone;
        });
        setOrchestratorState((prev) => ({
          ...prev,
          status: ORCHESTRATOR_STATES.COMPLETED,
          statusText: 'Website Generated Successfully',
          activeHandoff: null,
          userInputRequired: false,
          pendingQuestion: null,
        }));

        const summary = event.data?.completion_summary || {
          product_name: event.data?.project_name || userPrompt || 'Auctor Production Studio',
          agents_completed: '8 / 8 completed',
          qa_status: 'Passed',
          revisions_count: event.data?.qa_revision_count || 1,
          files_count: event.data?.file_count || 7,
          documentation_status: 'Complete',
          deployment_status: 'Ready',
          marketing_status: 'Complete',
        };
        setCompletionSummary(summary);

        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'success', text: event.message || 'Generation complete.' },
        ]);
        loadProjectFiles(pid);
        api.listProjects().then((l) => setProjectsList(l || [])).catch(() => {});
      },

      onError: (event) => {
        const errorText = event.message || event.error || 'Pipeline encountered an issue.';
        setGenerationError(errorText);
        setIsGenerating(false);
        setOrchestratorState((prev) => ({
          ...prev,
          status: ORCHESTRATOR_STATES.ERROR,
          statusText: 'Pipeline Stalled',
        }));
        setEventLogs((prev) => [
          ...prev,
          { time: new Date().toLocaleTimeString(), type: 'error', text: `Error: ${errorText}` },
        ]);
      },
    });

    listener.connect();
    sseRef.current = listener;
  }, [loadProjectFiles]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (sseRef.current) {
        sseRef.current.disconnect();
      }
    };
  }, []);

  // ── Reset Context ──────────────────────────────────────────────────────────
  const resetWorkspace = useCallback(() => {
    if (sseRef.current) {
      sseRef.current.disconnect();
    }
    if (workflowEngineRef.current) {
      workflowEngineRef.current.cancel();
    }
    localStorage.removeItem('auctor_active_project_id');
    setProjectId(null);
    setUserPrompt('');
    setIsGenerating(false);
    setGenerationError(null);
    setGeneratedFiles([]);
    setCodeCache({});
    setActivityLog([]);
    setCurrentAgentIndex(-1);
    setCurrentAgentName(null);
    const resetStatuses = {};
    AGENTS.forEach((a) => {
      resetStatuses[a.backendName] = AGENT_STATES.IDLE;
    });
    setAgentStatuses(resetStatuses);
    setOrchestratorState({
      status: ORCHESTRATOR_STATES.IDLE,
      statusText: 'Orchestrator Ready',
      currentAgent: null,
      activeHandoff: null,
      completedAgents: [],
      pendingAgents: AGENTS.map((a) => a.backendName),
      userInputRequired: false,
      pendingQuestion: null,
    });
    setCompletionSummary(null);
    setEventLogs([]);
    setRevisions([]);
    setRevisionCount(0);
  }, []);

  // ── Projects List & Selection (Phase 4A) ──────────────────────────────────
  const loadProjectsList = useCallback(async () => {
    try {
      const list = await api.listProjects();
      setProjectsList(list || []);
      return list || [];
    } catch (err) {
      console.warn('[ProjectContext] Failed to load projects list:', err);
      return [];
    }
  }, []);

  const selectProject = useCallback(async (targetPid) => {
    if (!targetPid) return;
    try {
      if (sseRef.current) {
        sseRef.current.disconnect();
      }

      setProjectId(targetPid);
      localStorage.setItem('auctor_active_project_id', targetPid);

      const [project, actRes, revRes] = await Promise.all([
        api.getProject(targetPid),
        api.getProjectActivities(targetPid).catch(() => ({ activities: [] })),
        api.getProjectRevisions(targetPid).catch(() => ({ revisions: [] })),
      ]);

      if (!project) return;

      setUserPrompt(project.prompt || '');
      setProjectState(project);
      const revList = revRes?.revisions || project.revisions || [];
      setRevisions(revList);
      const revCount = project.revision_count ?? project.qa_revision_count ?? revList.length;
      setRevisionCount(revCount);

      const isCompleted = project.status === 'completed' || project.status === 'generated';
      const isGeneratingStatus = project.status === 'generating' || project.status === 'running';

      setIsGenerating(isGeneratingStatus);
      setGenerationError(project.status === 'error' ? (project.error_message || 'Project error') : null);

      // Restore 8 agent statuses exactly
      const restoredStatuses = {};
      AGENTS.forEach((a) => {
        const s = (project.agent_statuses?.[a.backendName] || (isCompleted ? 'completed' : 'idle')).toLowerCase();
        if (s === 'completed') {
          restoredStatuses[a.backendName] = AGENT_STATES.COMPLETED;
        } else if (s === 'active' || s === 'working') {
          restoredStatuses[a.backendName] = AGENT_STATES.WORKING;
        } else if (s === 'thinking') {
          restoredStatuses[a.backendName] = AGENT_STATES.THINKING;
        } else if (s === 'communicating') {
          restoredStatuses[a.backendName] = AGENT_STATES.COMMUNICATING;
        } else if (s === 'error') {
          restoredStatuses[a.backendName] = AGENT_STATES.ERROR;
        } else {
          restoredStatuses[a.backendName] = AGENT_STATES.IDLE;
        }
      });
      setAgentStatuses(restoredStatuses);

      // Restore orchestrator state
      setOrchestratorState({
        status: isCompleted
          ? ORCHESTRATOR_STATES.COMPLETED
          : isGeneratingStatus
          ? ORCHESTRATOR_STATES.RUNNING
          : ORCHESTRATOR_STATES.IDLE,
        statusText: isCompleted
          ? 'Website Generated & Tested'
          : isGeneratingStatus
          ? 'Orchestrating Agents'
          : 'Orchestrator Ready',
        currentAgent: isCompleted ? null : project.current_agent,
        activeHandoff: null,
        completedAgents: isCompleted ? AGENTS.map((a) => a.backendName) : [],
        pendingAgents: isCompleted ? [] : AGENTS.map((a) => a.backendName),
        userInputRequired: Boolean(
          project.clarification && !project.clarification.user_response && project.status === 'waiting_user'
        ),
        pendingQuestion: project.clarification || null,
      });

      // Restore completion summary
      setCompletionSummary(project.completion_summary || null);

      // Restore generated files and code cache
      const files = project.files || [];
      setGeneratedFiles(files);
      const cache = {};
      files.forEach((f) => {
        if (f.filename) cache[f.filename] = f.content;
        if (f.path) cache[f.path] = f.content;
      });
      setCodeCache(cache);
      setActiveCodeFilename('index.html');
      setPreviewRefreshKey(Date.now());

      // Restore persisted activity stream directly (Zero fake events)
      const rawActivities = actRes?.activities || project.activities || [];
      const formattedActivities = rawActivities.map((act, idx) => ({
        id: act.id || `act-${idx}`,
        timestamp: act.timestamp ? new Date(act.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString(),
        agentId: act.agent_id || act.agent || 'system',
        agentName: act.agent_name || 'Auctor Studio',
        type: act.event_type || act.type || 'info',
        message: act.message || '',
        data: act.data,
      }));
      setActivityLog(formattedActivities);
      setEventLogs(rawActivities);

      // Reconnect SSE if currently generating
      if (isGeneratingStatus) {
        connectSSE(targetPid);
      }
    } catch (err) {
      console.error('[ProjectContext] Failed to select project:', err);
    }
  }, [connectSSE]);

  const deleteProject = useCallback(async (targetPid) => {
    if (!targetPid) return;
    try {
      await api.deleteProject(targetPid);
      const updatedList = await loadProjectsList();
      if (projectId === targetPid) {
        if (updatedList && updatedList.length > 0) {
          await selectProject(updatedList[0].id);
        } else {
          resetWorkspace();
        }
      }
    } catch (err) {
      console.error('[ProjectContext] Failed to delete project:', err);
    }
  }, [projectId, loadProjectsList, selectProject, resetWorkspace]);

  // Initial Workspace Mount Effect: Restore active project from SQLite
  useEffect(() => {
    let active = true;
    const initWorkspace = async () => {
      await fetchHealth();
      const list = await loadProjectsList();
      if (!active) return;
      const savedPid = localStorage.getItem('auctor_active_project_id');
      if (savedPid && list && list.some((p) => p.id === savedPid)) {
        await selectProject(savedPid);
      } else if (list && list.length > 0) {
        await selectProject(list[0].id);
      }
    };
    initWorkspace();
    return () => {
      active = false;
    };
  }, [fetchHealth, loadProjectsList, selectProject]);

  // ── Answer Clarification Question from Agent (Human-in-the-Loop) ───────────
  const answerAgentQuestion = useCallback(async (answerText) => {
    if (!answerText) return;

    // Immediately update UI to show resumed state
    setOrchestratorState((prev) => ({
      ...prev,
      userInputRequired: false,
      pendingQuestion: null,
      status: ORCHESTRATOR_STATES.WORKING,
      statusText: 'Beatrice Resumed With Input',
    }));

    // Local deterministic engine
    if (workflowEngineRef.current) {
      workflowEngineRef.current.answerQuestion(answerText);
    }

    // Live Backend Project
    if (projectId && projectId !== 'kairos-academic-studio') {
      try {
        await api.submitClarification(projectId, answerText);
      } catch (err) {
        console.error('[ProjectContext] Error submitting clarification to backend:', err);
      }
    }
  }, [projectId]);

  // ── Start Website Generation ───────────────────────────────────────────────
  const startGeneration = useCallback(async (promptText, mode = 'demo') => {
    if (!promptText || !promptText.trim()) return;

    setUserPrompt(promptText);
    setGenerationError(null);
    setIsGenerating(true);
    setGeneratedFiles([]);
    setCodeCache({});
    setActivityLog([]);
    setEventLogs([
      { time: new Date().toLocaleTimeString(), type: 'user', text: `Directive received: "${promptText}"` },
    ]);

    // Reset agent statuses to idle
    const resetStatuses = {};
    AGENTS.forEach((a) => {
      resetStatuses[a.backendName] = AGENT_STATES.IDLE;
    });
    setAgentStatuses(resetStatuses);

    // If backend is completely offline or user explicitly wants client-side demo
    if (!backendStatus.healthy && mode === 'demo') {
      const engine = new WorkflowEngine({
        onOrchestratorUpdate: (state) => {
          setOrchestratorState(state);
          if (state.status === ORCHESTRATOR_STATES.COMPLETED) {
            setIsGenerating(false);
          }
        },
        onAgentStateChange: (statuses, currIdx, currName, snippet) => {
          setAgentStatuses(statuses);
          setCurrentAgentIndex(currIdx);
          setCurrentAgentName(currName);
          if (currName && snippet) {
            setAgentSnippets((prev) => ({ ...prev, [currName]: snippet }));
          }
        },
        onActivityEvent: (event) => {
          setActivityLog((prev) => [...prev, event]);
          setEventLogs((prev) => [
            ...prev,
            { time: event.timestamp, type: event.type, text: event.message },
          ]);
        },
        onQuestionPrompt: (questionData) => {
          setOrchestratorState((prev) => ({
            ...prev,
            status: ORCHESTRATOR_STATES.WAITING_USER,
            userInputRequired: true,
            pendingQuestion: questionData,
          }));
        },
        onFilesGenerated: (files) => {
          setProjectId('kairos-academic-studio');
          setGeneratedFiles(files);
          const cache = {};
          files.forEach((f) => {
            if (f.filename) cache[f.filename] = f.content;
            if (f.path) cache[f.path] = f.content;
          });
          setCodeCache(cache);
          setActiveCodeFilename('index.html');
          setPreviewRefreshKey(Date.now());
          setIsGenerating(false);
        },
        onError: (err) => {
          setGenerationError(err);
          setIsGenerating(false);
        },
      });

      workflowEngineRef.current = engine;
      engine.start(promptText);
      return;
    }

    // Connect to live backend FastAPI service
    try {
      const response = await api.generateProject(promptText, mode);
      const newProjectId = response.project_id;
      setProjectId(newProjectId);
      localStorage.setItem('auctor_active_project_id', newProjectId);
      loadProjectsList();
      connectSSE(newProjectId);
    } catch (err) {
      console.warn('[ProjectContext] Backend generate call failed, switching to local demo:', err);
      // Graceful fallback to client-side demo if backend request fails
      const engine = new WorkflowEngine({
        onOrchestratorUpdate: (state) => {
          setOrchestratorState(state);
          if (state.status === ORCHESTRATOR_STATES.COMPLETED) {
            setIsGenerating(false);
          }
        },
        onAgentStateChange: (statuses, currIdx, currName, snippet) => {
          setAgentStatuses(statuses);
          setCurrentAgentIndex(currIdx);
          setCurrentAgentName(currName);
          if (currName && snippet) {
            setAgentSnippets((prev) => ({ ...prev, [currName]: snippet }));
          }
        },
        onActivityEvent: (event) => {
          setActivityLog((prev) => [...prev, event]);
          setEventLogs((prev) => [
            ...prev,
            { time: event.timestamp, type: event.type, text: event.message },
          ]);
        },
        onQuestionPrompt: (questionData) => {
          setOrchestratorState((prev) => ({
            ...prev,
            status: ORCHESTRATOR_STATES.WAITING_USER,
            userInputRequired: true,
            pendingQuestion: questionData,
          }));
        },
        onFilesGenerated: (files) => {
          setProjectId('kairos-academic-studio');
          setGeneratedFiles(files);
          const cache = {};
          files.forEach((f) => {
            if (f.filename) cache[f.filename] = f.content;
            if (f.path) cache[f.path] = f.content;
          });
          setCodeCache(cache);
          setActiveCodeFilename('index.html');
          setPreviewRefreshKey(Date.now());
          setIsGenerating(false);
        },
        onError: (e) => {
          setGenerationError(e);
          setIsGenerating(false);
        },
      });

      workflowEngineRef.current = engine;
      engine.start(promptText);
    }
  }, [backendStatus.healthy, connectSSE]);

  // ── Multi-Turn Targeted Revision (Phase 4B) ────────────────────────────────
  const modifyProject = useCallback(async (promptText, mode = 'demo') => {
    if (!promptText || !promptText.trim()) return;
    const targetPid = projectId;
    if (!targetPid || targetPid === 'kairos-academic-studio') {
      console.warn('[ProjectContext] modifyProject called without active backend project');
      return;
    }

    setIsGenerating(true);
    setGenerationError(null);
    setOrchestratorState((prev) => ({
      ...prev,
      userInputRequired: false,
      pendingQuestion: null,
      status: ORCHESTRATOR_STATES.WORKING,
      statusText: 'Applying Revision...',
    }));

    // Make sure SSE stream listener is connected for revision events
    connectSSE(targetPid);

    setEventLogs((prev) => [
      ...prev,
      { time: new Date().toLocaleTimeString(), type: 'user', text: `Revision directive: "${promptText}"` },
    ]);

    try {
      await api.modifyProject(targetPid, promptText, mode);
    } catch (err) {
      console.error('[ProjectContext] modifyProject failed:', err);
      setGenerationError(err.message || 'Failed to apply revision.');
      setIsGenerating(false);
    }
  }, [projectId, connectSSE]);

  // ── Deploy Current Project ─────────────────────────────────────────────────
  const deployCurrentProject = useCallback(async () => {
    if (!projectId) return null;
    try {
      const result = await api.deployProject(projectId, 'vercel');
      return result;
    } catch (err) {
      throw err;
    }
  }, [projectId]);

  // ── Download File Helper ───────────────────────────────────────────────────
  const downloadFile = useCallback(async (filename, explicitContent = null) => {
    let content = explicitContent;
    const baseName = filename.split('/').pop();
    if (!content && codeCache) {
      content = codeCache[filename] || codeCache[baseName] || codeCache[`docs/${baseName}`] || codeCache[`src/${baseName}`];
    }
    if (!content && projectId && projectId !== 'kairos-academic-studio') {
      try {
        content = await api.getFileContent(projectId, filename);
      } catch (err) {
        console.warn(`[ProjectContext] Failed to fetch content for download ${filename}:`, err);
      }
    }
    if (!content) {
      console.warn(`[ProjectContext] Cannot download ${filename}: empty content`);
      return;
    }
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = baseName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [codeCache, projectId]);

  const value = {
    // Connection
    backendStatus,
    fetchHealth,
    // Project
    projectId,
    projectsList,
    loadProjectsList,
    selectProject,
    deleteProject,
    userPrompt,
    isGenerating,
    generationError,
    projectState,
    startGeneration,
    modifyProject,
    revisions,
    revisionCount,
    resetWorkspace,
    deployCurrentProject,
    completionSummary,
    // Phase 3A/3B/3C Orchestrator & Activity Stream
    orchestratorState,
    activityLog,
    answerAgentQuestion,
    // Agent workflow
    currentAgentIndex,
    currentAgentName,
    agentStatuses,
    agentSnippets,
    eventLogs,
    // Output & Preview
    generatedFiles,
    codeCache,
    activeCodeFilename,
    setActiveCodeFilename,
    previewDevice,
    setPreviewDevice,
    previewRefreshKey,
    refreshPreview: () => setPreviewRefreshKey(Date.now()),
    activeTab,
    setActiveTab,
    // Documentation Viewer & Download
    isDocViewerOpen,
    docViewerDoc,
    openDocViewer,
    closeDocViewer,
    downloadFile,
  };

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
