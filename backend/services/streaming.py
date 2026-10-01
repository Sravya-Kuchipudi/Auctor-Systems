"""
Auctor Systems — SSE Streaming Service

Handles real-time event streaming from CrewAI agent execution
to the React frontend via Server-Sent Events (SSE).

Every event represents REAL agent activity — never fabricated.
"""

import json
import logging
from queue import Queue, Empty
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator

from models import AgentEvent, EventType, AgentName, AGENT_ORDER

logger = logging.getLogger("auctor.streaming")


class StreamingEventHandler:
    """
    Intercepts CrewAI execution callbacks and pushes structured
    events to a queue that the SSE endpoint reads from.
    
    This is the bridge between synchronous CrewAI execution
    (running in a thread) and async FastAPI SSE streaming.
    """

    def __init__(self):
        self.queue: Queue = Queue()
        self.current_agent_index: int = 0
        self.agent_names: list[str] = [agent.value for agent in AGENT_ORDER]
        self.is_complete: bool = False
        self.has_error: bool = False

    @property
    def current_agent_name(self) -> str:
        if self.current_agent_index < len(self.agent_names):
            return self.agent_names[self.current_agent_index]
        return "Orchestrator"

    def _emit(self, event_type: EventType, data: Optional[str] = None,
              agent_name: Optional[str] = None, agent_index: Optional[int] = None):
        """Push an event to the queue."""
        event = AgentEvent(
            event_type=event_type,
            agent_name=agent_name or self.current_agent_name,
            agent_index=agent_index if agent_index is not None else self.current_agent_index,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.queue.put(event)
        logger.info(f"Event: {event_type.value} | Agent: {event.agent_name} | Data length: {len(data) if data else 0}")

    def emit_pipeline_started(self, prompt: str):
        """Emit when the full pipeline begins."""
        self._emit(EventType.PIPELINE_STARTED, data=prompt, agent_name="Orchestrator", agent_index=-1)
        # Also emit that the first agent is starting
        self._emit(EventType.AGENT_STARTED)

    def on_step(self, step_output):
        """
        CrewAI step_callback — called after each intermediate LLM step.
        Emits a progress event with the step content.
        """
        try:
            # Extract meaningful text from the step output
            if hasattr(step_output, "output"):
                text = str(step_output.output)
            elif hasattr(step_output, "text"):
                text = str(step_output.text)
            else:
                text = str(step_output)

            # Truncate very long outputs for streaming (full output saved on task complete)
            display_text = text[:500] + "..." if len(text) > 500 else text
            self._emit(EventType.AGENT_PROGRESS, data=display_text)
        except Exception as e:
            logger.warning(f"Error processing step callback: {e}")

    def on_task_complete(self, task_output):
        """
        CrewAI task_callback — called when an agent's task completes.
        Emits completion for current agent and starts the next one.
        """
        try:
            # Extract the task output
            if hasattr(task_output, "raw"):
                output_text = str(task_output.raw)
            elif hasattr(task_output, "output"):
                output_text = str(task_output.output)
            else:
                output_text = str(task_output)

            # Emit completion for current agent
            self._emit(EventType.AGENT_COMPLETED, data=output_text)

            # Special events for specific agents
            if self.current_agent_name == AgentName.DEVELOPMENT.value:
                self._emit(EventType.CODE_GENERATED, data=output_text)
            elif self.current_agent_name == AgentName.TESTING.value:
                self._emit(EventType.TEST_RESULT, data=output_text)

            # Move to next agent
            self.current_agent_index += 1
            if self.current_agent_index < len(self.agent_names):
                self._emit(EventType.AGENT_STARTED)

        except Exception as e:
            logger.error(f"Error processing task callback: {e}")
            self._emit(EventType.AGENT_ERROR, data=str(e))

    def emit_pipeline_complete(self, result: Optional[str] = None):
        """Emit when the entire pipeline finishes successfully."""
        self.is_complete = True
        self._emit(
            EventType.PIPELINE_COMPLETE,
            data=result or "Pipeline completed successfully.",
            agent_name="Orchestrator",
            agent_index=-1,
        )

    def emit_error(self, error: str):
        """Emit a critical error."""
        self.has_error = True
        self.is_complete = True
        self._emit(
            EventType.ERROR,
            data=error,
            agent_name=self.current_agent_name,
        )

    async def stream(self, timeout: float = 1.0) -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted events.
        Used by the FastAPI SSE endpoint.
        """
        while not self.is_complete:
            try:
                event = self.queue.get(timeout=timeout)
                yield format_sse_event(event)

                if event.event_type in (EventType.PIPELINE_COMPLETE, EventType.ERROR):
                    break
            except Empty:
                # Send heartbeat to keep connection alive
                heartbeat = AgentEvent(
                    event_type=EventType.HEARTBEAT,
                    agent_name="Orchestrator",
                    agent_index=-1,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                yield format_sse_event(heartbeat)

        # Drain any remaining events in the queue
        while not self.queue.empty():
            try:
                event = self.queue.get_nowait()
                yield format_sse_event(event)
            except Empty:
                break


def format_sse_event(event: AgentEvent) -> str:
    """Format an AgentEvent as an SSE string for the browser EventSource API."""
    data = json.dumps(event.model_dump(), default=str)
    return f"event: {event.event_type.value}\ndata: {data}\n\n"
