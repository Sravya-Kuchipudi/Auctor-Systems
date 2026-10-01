"""
Auctor Systems — Data Models

Pydantic models and enums for API contracts, project state,
agent events, and deployment status.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class AgentName(str, Enum):
    """The 8 specialized agents in Auctor Systems."""
    PLANNING = "Planning"
    REQUIREMENTS = "Requirements"
    DESIGN = "Design"
    DEVELOPMENT = "Development"
    TESTING = "Testing"
    DOCUMENTATION = "Documentation"
    DEPLOYMENT = "Deployment"
    MARKETING = "Marketing"


class AgentStatus(str, Enum):
    """Current execution state of an individual agent."""
    IDLE = "idle"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


class ProjectStatus(str, Enum):
    """
    Lifecycle status of a generated project.
    The UI must clearly distinguish these states — no faking.
    """
    IDLE = "idle"
    GENERATING = "generating"
    GENERATED = "generated"
    TESTED = "tested"
    READY_TO_DEPLOY = "ready_to_deploy"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"


class DeploymentStatus(str, Enum):
    """
    Deployment-specific status.
    NOT_CONFIGURED = Vercel credentials not set.
    """
    NOT_CONFIGURED = "not_configured"
    READY = "ready"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"


class EventType(str, Enum):
    """SSE event types streamed to the frontend."""
    PIPELINE_STARTED = "pipeline_started"
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    CODE_GENERATED = "code_generated"
    TEST_RESULT = "test_result"
    DEPLOYMENT_STATUS = "deployment_status"
    PIPELINE_COMPLETE = "pipeline_complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


# ── Agent Ordering ────────────────────────────────────────────────────────────

AGENT_ORDER: List[AgentName] = [
    AgentName.PLANNING,
    AgentName.REQUIREMENTS,
    AgentName.DESIGN,
    AgentName.DEVELOPMENT,
    AgentName.TESTING,
    AgentName.DOCUMENTATION,
    AgentName.DEPLOYMENT,
    AgentName.MARKETING,
]


# ── Request / Response Models ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    """Incoming request to generate a website."""
    prompt: str = Field(..., min_length=5, description="User's website description")
    mode: Optional[str] = Field(default="real", description="Execution mode: 'real' or 'demo'")
    name: Optional[str] = Field(default=None, description="Optional website / project name")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Optional generation settings")


class ProjectUpdateRequest(BaseModel):
    """Update payload for project metadata."""
    name: Optional[str] = None
    prompt: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ClarificationInput(BaseModel):
    """User input for human-in-the-loop clarification."""
    answer: Optional[str] = None
    input: Optional[str] = None
    option: Optional[str] = None

    def get_text(self) -> str:
        return self.answer or self.input or self.option or ""


class ModifyRequest(BaseModel):
    """Follow-up modification request for an existing project."""
    prompt: str = Field(..., min_length=3, description="Modification instruction")
    mode: Optional[str] = Field(default="real", description="Execution mode: 'real' or 'demo'")
    project_id: Optional[str] = Field(default=None, description="Optional ID of the project to modify")


class RevisionRecord(BaseModel):
    """A record of a single completed revision in SQLite."""
    revision_number: int
    prompt: str
    modified_files: List[str]
    status: str = "completed"
    snapshot_status: str = "VERIFIED_IMMUTABLE"  # VERIFIED_IMMUTABLE or LEGACY_UNAVAILABLE
    qa_summary: Optional[str] = None
    timestamp: str


class RollbackRequest(BaseModel):
    """Request payload to rollback to a historical revision snapshot."""
    target_revision: int


# ── Project File Model ────────────────────────────────────────────────────────

class ProjectFile(BaseModel):
    """A single generated file in the project."""
    filename: str
    content: str
    file_type: str  # html, css, js, md, json, txt


# ── Agent Event Model ─────────────────────────────────────────────────────────

class AgentEvent(BaseModel):
    """
    A single SSE event emitted during pipeline execution.
    Every event is tied to real agent activity — never fabricated.
    """
    event_type: EventType
    agent_name: str
    agent_index: int
    data: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Project State Model ───────────────────────────────────────────────────────

class ProjectState(BaseModel):
    """
    Complete state of a generated project.
    This is the single source of truth for a project's lifecycle.
    """
    project_id: str
    status: ProjectStatus = ProjectStatus.IDLE
    prompt: str = ""
    current_agent: Optional[str] = None
    agent_statuses: Dict[str, AgentStatus] = Field(default_factory=lambda: {
        agent.value: AgentStatus.IDLE for agent in AgentName
    })
    files: List[ProjectFile] = Field(default_factory=list)
    outputs: Dict[str, str] = Field(default_factory=dict)
    deployment_url: Optional[str] = None
    deployment_status: DeploymentStatus = DeploymentStatus.NOT_CONFIGURED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc).isoformat()
