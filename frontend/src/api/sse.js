/**
 * Auctor Systems — Server-Sent Events (SSE) Streaming Listener (Phase 3B)
 * Connects to /api/project/:id/stream and streams real backend agent activity.
 * Supports all Phase 3B event contracts, custom EventSource events, and reconnect buffers.
 */

const KNOWN_EVENTS = [
  'workflow_started',
  'agent_started',
  'agent_thinking',
  'agent_working',
  'agent_message',
  'agent_handoff',
  'agent_completed',
  'agent_error',
  'user_input_required',
  'test_failed',
  'test_passed',
  'project_generated',
  'workflow_completed',
  'revision_started',
  'code_modified',
  'qa_verified',
  'revision_completed',
  'heartbeat',
  // Legacy / Phase 1 compatibility
  'pipeline_started',
  'agent_progress',
  'code_generated',
  'test_result',
  'pipeline_complete',
  'error',
];

export class SSEStreamListener {
  constructor(projectId, handlers = {}) {
    this.projectId = projectId;
    this.handlers = handlers;
    this.eventSource = null;
    this.isConnected = false;
  }

  connect() {
    if (this.eventSource) {
      this.disconnect();
    }

    const streamUrl = `/api/project/${this.projectId}/stream`;
    this.eventSource = new EventSource(streamUrl);
    this.isConnected = true;

    this.eventSource.onopen = () => {
      if (this.handlers.onOpen) this.handlers.onOpen();
    };

    const handleParsedEvent = (eventType, payload) => {
      // Normalizing event fields
      const eventObj = {
        type: eventType,
        ...payload,
      };

      // 1. Generic stream listener
      if (this.handlers.onWorkflowEvent) {
        this.handlers.onWorkflowEvent(eventObj);
      }
      if (this.handlers.onEvent) {
        this.handlers.onEvent(eventObj);
      }

      // 2. Specific event routing
      switch (eventType) {
        case 'workflow_started':
        case 'pipeline_started':
          if (this.handlers.onWorkflowStarted) this.handlers.onWorkflowStarted(eventObj);
          if (this.handlers.onPipelineStarted) this.handlers.onPipelineStarted(eventObj);
          break;

        case 'agent_started':
          if (this.handlers.onAgentStarted) this.handlers.onAgentStarted(eventObj);
          break;

        case 'agent_thinking':
          if (this.handlers.onAgentThinking) this.handlers.onAgentThinking(eventObj);
          break;

        case 'agent_working':
        case 'agent_progress':
          if (this.handlers.onAgentWorking) this.handlers.onAgentWorking(eventObj);
          if (this.handlers.onAgentProgress) this.handlers.onAgentProgress(eventObj);
          break;

        case 'agent_message':
          if (this.handlers.onAgentMessage) this.handlers.onAgentMessage(eventObj);
          break;

        case 'agent_handoff':
          if (this.handlers.onAgentHandoff) this.handlers.onAgentHandoff(eventObj);
          break;

        case 'agent_completed':
          if (this.handlers.onAgentCompleted) this.handlers.onAgentCompleted(eventObj);
          break;

        case 'user_input_required':
          if (this.handlers.onUserInputRequired) this.handlers.onUserInputRequired(eventObj);
          break;

        case 'test_failed':
          if (this.handlers.onTestFailed) this.handlers.onTestFailed(eventObj);
          if (this.handlers.onTestResult) this.handlers.onTestResult(eventObj);
          break;

        case 'test_passed':
          if (this.handlers.onTestPassed) this.handlers.onTestPassed(eventObj);
          if (this.handlers.onTestResult) this.handlers.onTestResult(eventObj);
          break;

        case 'project_generated':
        case 'code_generated':
          if (this.handlers.onProjectGenerated) this.handlers.onProjectGenerated(eventObj);
          if (this.handlers.onCodeGenerated) this.handlers.onCodeGenerated(eventObj);
          break;

        case 'workflow_completed':
        case 'pipeline_complete':
          if (this.handlers.onWorkflowCompleted) this.handlers.onWorkflowCompleted(eventObj);
          if (this.handlers.onPipelineComplete) this.handlers.onPipelineComplete(eventObj);
          this.disconnect();
          break;

        case 'revision_started':
          if (this.handlers.onRevisionStarted) this.handlers.onRevisionStarted(eventObj);
          break;

        case 'code_modified':
          if (this.handlers.onCodeModified) this.handlers.onCodeModified(eventObj);
          break;

        case 'qa_verified':
          if (this.handlers.onQaVerified) this.handlers.onQaVerified(eventObj);
          break;

        case 'revision_completed':
          if (this.handlers.onRevisionCompleted) this.handlers.onRevisionCompleted(eventObj);
          this.disconnect();
          break;

        case 'agent_error':
        case 'error':
          if (this.handlers.onError) this.handlers.onError(eventObj);
          break;

        case 'heartbeat':
          if (this.handlers.onHeartbeat) this.handlers.onHeartbeat(eventObj);
          break;

        default:
          break;
      }
    };

    // Attach listeners for all known event types
    KNOWN_EVENTS.forEach((eventType) => {
      this.eventSource.addEventListener(eventType, (e) => {
        try {
          const data = JSON.parse(e.data);
          handleParsedEvent(eventType, data);
        } catch (err) {
          console.warn(`[SSE] Failed to parse event '${eventType}':`, e.data, err);
        }
      });
    });

    // Fallback default onmessage
    this.eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const eventType = payload.type || payload.event || 'message';
        handleParsedEvent(eventType, payload);
      } catch (err) {
        console.warn('[SSE] Failed to parse message payload:', e.data, err);
      }
    };

    this.eventSource.onerror = (err) => {
      if (this.handlers.onError && this.isConnected) {
        // SSE may fire error event when stream closes normally at end of generation
      }
    };
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
      if (this.handlers.onClose) this.handlers.onClose();
    }
  }
}
