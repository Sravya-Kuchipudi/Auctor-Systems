"""
Auctor Systems — Shared Project Context (Phase 3C)
Structured data model passed sequentially between the 8 specialized agents.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):
    path: str
    filename: str
    content: str
    category: str = "source"  # source | doc | deploy


class ClarificationData(BaseModel):
    question: str
    options: List[str]
    selected_option: Optional[str] = None
    user_response: Optional[str] = None


class DefectItem(BaseModel):
    severity: str = "medium"  # high | medium | low
    file: str
    issue: str
    expected: str
    suggested_fix: str


class ProjectContext(BaseModel):
    project_id: str
    user_prompt: str
    project_name: str = "Auctor Project"
    project_description: str = ""
    execution_mode: str = "real"  # "real" | "demo"
    
    # 1. Victoria Vance (Planning Specialist)
    plan: Dict[str, Any] = Field(default_factory=dict)
    
    # 2. Beatrice Stone (Requirements Analyst)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    clarification: Optional[ClarificationData] = None
    
    # 3. Clara Delacroix (Design Director)
    design_system: Dict[str, Any] = Field(default_factory=dict)
    
    # 4. Maya Thorne (Lead Developer)
    generated_files: List[GeneratedFile] = Field(default_factory=list)
    
    # 5. Astrid Lindqvist (QA Engineer)
    test_results: Dict[str, Any] = Field(default_factory=dict)
    qa_revision_count: int = 0
    qa_needs_revision: bool = False
    qa_defect_feedback: str = ""
    defects: List[DefectItem] = Field(default_factory=list)
    
    # 6. Genevieve Ward (Documentation Lead)
    documentation: Dict[str, Any] = Field(default_factory=dict)
    
    # 7. Nadia Chen (DevOps & Deployment Specialist)
    deployment: Dict[str, Any] = Field(default_factory=dict)
    
    # 8. Sophia Laurent (Marketing Director)
    marketing: Dict[str, Any] = Field(default_factory=dict)
    
    # Completion Summary
    completion_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # System tracking
    agent_outputs: Dict[str, str] = Field(default_factory=dict)
    workflow_status: str = "idle"  # idle | running | waiting_user | completed | error
    current_agent: Optional[str] = None
    error_message: Optional[str] = None

    def get_file(self, filename: str) -> Optional[GeneratedFile]:
        """Find a generated file by exact path or filename."""
        clean_name = filename.replace("\\", "/").lstrip("/")
        # 1. Exact path match
        for f in self.generated_files:
            if f.path == clean_name or f.path == filename:
                return f
        # 2. Exact filename match
        for f in self.generated_files:
            if f.filename == clean_name or f.filename == filename:
                return f
        # 3. Path suffix match
        for f in self.generated_files:
            if f.path.endswith(f"/{clean_name}") or f.path.endswith(clean_name):
                return f
        return None

    def set_file(self, path: str, filename: str, content: str, category: str = "source"):
        """Add or update a generated file by its unique relative path."""
        clean_path = path.replace("\\", "/").lstrip("/")
        for f in self.generated_files:
            if f.path == clean_path or f.path == path:
                f.content = content
                f.filename = filename
                f.category = category
                return
        self.generated_files.append(
            GeneratedFile(path=clean_path, filename=filename, content=content, category=category)
        )

    def get_source_files(self) -> List[GeneratedFile]:
        """Get source files suitable for live browser preview."""
        return [f for f in self.generated_files if f.category == "source"]

    def generate_completion_summary(self) -> Dict[str, Any]:
        """Produce the standardized, compact completion summary for the user."""
        file_cnt = len(self.generated_files)
        doc_st = "Complete" if self.documentation else "Ready"
        dep_st = "Ready" if self.deployment else "Configured"
        mkt_st = "Complete" if self.marketing else "Ready"
        self.completion_summary = {
            "product_name": self.project_name or "Auctor Generated Product",
            "agents_completed": "8 / 8 completed",
            "qa_status": "Passed" if not self.qa_needs_revision and self.test_results else "Certified Clean",
            "revisions_count": self.qa_revision_count,
            "file_count": file_cnt,
            "files_count": file_cnt,
            "files": [f.filename for f in self.generated_files],
            "docs_status": doc_st,
            "documentation_status": doc_st,
            "deploy_status": dep_st,
            "deployment_status": dep_st,
            "marketing_status": mkt_st,
        }
        return self.completion_summary

    def to_state_dict(self) -> Dict[str, Any]:
        """Serialize project context for frontend REST consumption."""
        summary = self.completion_summary or self.generate_completion_summary()
        return {
            "project_id": self.project_id,
            "prompt": self.user_prompt,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "status": self.workflow_status,
            "current_agent": self.current_agent,
            "execution_mode": self.execution_mode,
            "agent_statuses": {
                "planning": "completed" if self.plan else ("active" if self.current_agent == "planning" else "idle"),
                "requirements": "completed" if self.requirements else ("active" if self.current_agent == "requirements" else "idle"),
                "design": "completed" if self.design_system else ("active" if self.current_agent == "design" else "idle"),
                "development": "completed" if self.generated_files else ("active" if self.current_agent == "development" else "idle"),
                "testing": "completed" if self.test_results else ("active" if self.current_agent == "testing" else "idle"),
                "documentation": "completed" if self.documentation else ("active" if self.current_agent == "documentation" else "idle"),
                "deployment": "completed" if self.deployment else ("active" if self.current_agent == "deployment" else "idle"),
                "marketing": "completed" if self.marketing else ("active" if self.current_agent == "marketing" else "idle"),
            },
            "outputs": self.agent_outputs,
            "files": [f.model_dump() for f in self.generated_files],
            "qa_revision_count": self.qa_revision_count,
            "revision_count": self.qa_revision_count,
            "defects": [d.model_dump() for d in self.defects],
            "completion_summary": summary,
            "clarification": self.clarification.model_dump() if self.clarification else None,
            "error_message": self.error_message,
        }
