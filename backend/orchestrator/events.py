"""
Auctor Systems — Event Schema for Multi-Agent Workflow
Compatible with existing frontend Activity Feed, Living Office, and Orchestrator state machine.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EventType(str, Enum):
    WORKFLOW_STARTED = "workflow_started"
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_WORKING = "agent_working"
    AGENT_MESSAGE = "agent_message"
    AGENT_HANDOFF = "agent_handoff"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    USER_INPUT_REQUIRED = "user_input_required"
    TEST_FAILED = "test_failed"
    TEST_PASSED = "test_passed"
    PROJECT_GENERATED = "project_generated"
    WORKFLOW_COMPLETED = "workflow_completed"
    REVISION_STARTED = "revision_started"
    CODE_MODIFIED = "code_modified"
    QA_VERIFIED = "qa_verified"
    REVISION_COMPLETED = "revision_completed"
    HEARTBEAT = "heartbeat"


class WorkflowEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(
        default_factory=lambda: f"evt-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    )
    type: str
    project_id: str
    agent: Optional[str] = None
    agent_name: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = Field(default=None, alias="to")
    from_agent: Optional[str] = None
    to_agent: Optional[str] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def model_dump_compat(self) -> Dict[str, Any]:
        """Dump dictionary with both 'from'/'to' and 'from_agent'/'to_agent'."""
        d = self.model_dump(by_alias=True)
        # Ensure 'from' and 'from_agent' are synchronized
        source = self.from_ or self.from_agent
        target = self.to or self.to_agent
        if source:
            d["from"] = source
            d["from_agent"] = source
        if target:
            d["to"] = target
            d["to_agent"] = target
        return d

    def format_sse(self) -> str:
        """Format as Server-Sent Event frame for browser EventSource."""
        import json
        payload = json.dumps(self.model_dump_compat())
        return f"event: {self.type}\ndata: {payload}\n\n"
