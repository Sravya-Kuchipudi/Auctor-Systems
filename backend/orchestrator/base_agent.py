"""
Auctor Systems — Base Agent Definition
Defines the abstract base contract for all 8 specialized agents.
"""

import abc
import logging
from typing import Callable, Awaitable, Optional, Dict, Any

from orchestrator.context import ProjectContext
from orchestrator.events import WorkflowEvent, EventType

logger = logging.getLogger("auctor.base_agent")


class BaseAgent(abc.ABC):
    """
    Abstract Base Class for Auctor specialized agents.
    Every agent interacts with the shared ProjectContext and communicates
    via the event callback with well-typed events.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        backend_name: str,
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.backend_name = backend_name
        self.logger = logging.getLogger(f"auctor.agent.{agent_id}")

    @abc.abstractmethod
    async def execute(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
    ) -> None:
        """
        Execute agent logic, modifying the context and emitting real-time events.
        """
        pass

    # ── Event Helper Methods ──────────────────────────────────────────────────

    async def emit_started(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        message: Optional[str] = None,
    ) -> None:
        msg = message or f"{self.name} ({self.role}) initiated task."
        self.logger.info(f"[{self.agent_id}] Started: {msg}")
        await emit(
            WorkflowEvent(
                type=EventType.AGENT_STARTED.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=msg,
                data={"role": self.role, "backend_name": self.backend_name},
            )
        )

    async def emit_thinking(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        thought: str,
    ) -> None:
        self.logger.info(f"[{self.agent_id}] Thinking: {thought[:80]}...")
        await emit(
            WorkflowEvent(
                type=EventType.AGENT_THINKING.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=thought,
                data={"thought": thought},
            )
        )

    async def emit_working(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        message: str,
        snippet: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.logger.info(f"[{self.agent_id}] Working: {message}")
        payload = {"snippet": snippet} if snippet else {}
        if data:
            payload.update(data)
        await emit(
            WorkflowEvent(
                type=EventType.AGENT_WORKING.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=message,
                data=payload,
            )
        )

    async def emit_message(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.logger.info(f"[{self.agent_id}] Message: {message}")
        await emit(
            WorkflowEvent(
                type=EventType.AGENT_MESSAGE.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=message,
                data=data or {},
            )
        )

    async def emit_handoff(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        to_agent_id: str,
        to_agent_name: str,
        message: str,
    ) -> None:
        self.logger.info(f"[{self.agent_id}] Handoff -> [{to_agent_id}]: {message}")
        await emit(
            WorkflowEvent(
                type=EventType.AGENT_HANDOFF.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                from_=self.agent_id,
                to=to_agent_id,
                from_agent=self.agent_id,
                to_agent=to_agent_id,
                message=message,
                data={"to_agent_name": to_agent_name},
            )
        )

    async def emit_completed(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        msg = message or f"{self.name} completed assignments successfully."
        self.logger.info(f"[{self.agent_id}] Completed: {msg}")
        await emit(
            WorkflowEvent(
                type=EventType.AGENT_COMPLETED.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=msg,
                data=data or {},
            )
        )

    async def emit_error(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        error: str,
    ) -> None:
        self.logger.error(f"[{self.agent_id}] Error: {error}")
        await emit(
            WorkflowEvent(
                type=EventType.AGENT_ERROR.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=error,
                data={"error": error},
            )
        )
