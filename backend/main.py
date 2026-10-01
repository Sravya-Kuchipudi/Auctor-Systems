"""
Auctor Systems — FastAPI Backend Application (Phase 3B)

The main entry point for the Auctor backend.
Provides REST API and SSE streaming endpoints for:
- Website generation (POST /api/generate, POST /api/projects)
- Human clarification input (POST /api/project/{id}/clarification, POST /api/projects/{id}/input)
- Real-time agent streaming (GET /api/project/{id}/stream)
- Project retrieval (GET /api/project/{id}, GET /api/projects/{id})
- File content (GET /api/project/{id}/files/{filename})
- Live preview (GET /api/project/{id}/preview)
- ZIP export (GET /api/project/{id}/export)
- Real deployment (POST /api/project/{id}/deploy)
- Deployment provider info (GET /api/deployment/providers)
- Health check (GET /api/health)
"""

import shutil
import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse

from config import FRONTEND_URL, HOST, PORT, PROJECTS_DIR, validate_config
from models import GenerateRequest, ModifyRequest, RollbackRequest, ProjectUpdateRequest, ClarificationInput, ProjectState, ProjectStatus
from database import db
from services.llm_service import llm_service
from agents.orchestrator import AuctorOrchestrator
from orchestrator.engine import OrchestratorEngine
from services.project_manager import ProjectManager
from services.export_service import ExportService
from services.deployment_service import DeploymentService

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("auctor.main")

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Auctor Systems API",
    description="AI-powered website generation platform with 8 specialized agents.",
    version="1.1.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-Memory State ──────────────────────────────────────────────────────────
# Active Phase 3B Orchestrator engines: project_id -> OrchestratorEngine
active_engines: Dict[str, OrchestratorEngine] = {}

# Legacy CrewAI orchestrators for backward compatibility
active_orchestrators: Dict[str, AuctorOrchestrator] = {}

# Deployment service (singleton)
deployment_service = DeploymentService()


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    config_status = validate_config()
    logger.info("=" * 60)
    logger.info("  AUCTOR SYSTEMS — Backend Starting (Phase 3B)")
    logger.info("=" * 60)
    logger.info(f"  Gemini API configured: {config_status['gemini_configured']}")
    logger.info(f"  Gemini model: {config_status['model']}")
    logger.info(f"  Vercel configured: {config_status['vercel_configured']}")
    logger.info(f"  Projects directory: {config_status['projects_dir']}")
    logger.info(f"  Frontend URL: {FRONTEND_URL}")
    logger.info("=" * 60)

    if not config_status["gemini_configured"]:
        logger.info(
            "ℹ  GEMINI_API_KEY is not set. "
            "Auctor will operate with graceful local deterministic synthesis."
        )


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint with configuration status."""
    config = validate_config()
    return {
        "status": "healthy",
        "service": "Auctor Systems",
        "phase": "3B",
        "config": config,
    }


# ── Projects Management (Phase 4A) ────────────────────────────────────────────

@app.get("/api/projects")
async def list_projects():
    """List all persisted projects from SQLite."""
    return db.list_projects()


# ── Generate Website ──────────────────────────────────────────────────────────

@app.post("/api/generate")
@app.post("/api/projects")
async def generate_project(request: GenerateRequest):
    """
    Start the 8-agent pipeline to generate a website.
    Supports 'real' and 'demo' modes.
    If Gemini is unavailable or not configured, gracefully falls back to local deterministic mode.
    """
    logger.info(f"New generation request (mode={request.mode}): {request.prompt[:100]}...")

    config = validate_config()
    effective_mode = request.mode or "real"
    if effective_mode == "real" and not config["gemini_configured"]:
        logger.info("Gemini key not configured; routing to high-fidelity deterministic local fallback.")
        effective_mode = "demo"

    # Initialize Phase 3B/4A orchestrator engine
    engine = OrchestratorEngine()
    project_id = engine.start(request.prompt, mode=effective_mode, name=request.name)
    active_engines[project_id] = engine

    return {
        "project_id": project_id,
        "id": project_id,
        "status": "generating",
        "mode": effective_mode,
        "message": f"8-agent pipeline started in {effective_mode.upper()} mode.",
        "stream_url": f"/api/project/{project_id}/stream",
    }


# ── Human-in-the-Loop Clarification ───────────────────────────────────────────

@app.post("/api/project/{project_id}/clarification")
@app.post("/api/project/{project_id}/input")
@app.post("/api/projects/{project_id}/input")
async def provide_project_input(project_id: str, input_data: ClarificationInput):
    """
    Genuine backend-driven human clarification endpoint.
    Answers Beatrice Stone's pending question and resumes workflow execution.
    """
    engine = active_engines.get(project_id)
    if not engine:
        raise HTTPException(
            status_code=404,
            detail=f"No active pipeline found for project {project_id}",
        )

    text = input_data.get_text()
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Clarification answer or input text is required.",
        )

    logger.info(f"Human input received for project {project_id}: '{text}'")
    success = engine.provide_user_input(text)

    if not success:
        return {
            "status": "unhandled",
            "project_id": project_id,
            "message": "Orchestrator was not waiting for user clarification.",
        }

    return {
        "status": "resumed",
        "project_id": project_id,
        "message": "User clarification submitted. Beatrice Stone resuming workflow.",
        "input": text,
    }


# ── Phase 4B: Targeted Project Revision ───────────────────────────────────────

@app.post("/api/project/{project_id}/modify")
@app.post("/api/projects/{project_id}/modify")
@app.post("/api/modify")
async def modify_project(
    request: ModifyRequest,
    project_id: Optional[str] = None,
):
    """
    Phase 4B: Targeted natural-language revision on existing project.
    Triggers Maya -> Astrid -> Genevieve modification pipeline without full regeneration.
    """
    target_pid = project_id or request.project_id
    if not target_pid:
        raise HTTPException(status_code=400, detail="Project ID is required.")

    # Check if project exists
    project_data = db.get_project(target_pid)
    if not project_data:
        raise HTTPException(status_code=404, detail=f"Project {target_pid} not found")

    # Determine mode
    req_mode = (request.mode or "real").lower()
    effective_mode = "demo" if req_mode == "demo" or not llm_service.is_available else "real"

    # Retrieve or instantiate engine for this project
    engine = active_engines.get(target_pid)
    if not engine:
        engine = OrchestratorEngine(project_id=target_pid)
        active_engines[target_pid] = engine

    # Launch modification pipeline
    engine.modify(request.prompt, mode=effective_mode)

    return {
        "project_id": target_pid,
        "id": target_pid,
        "status": "generating",
        "mode": effective_mode,
        "message": f"Revision pipeline started in {effective_mode.upper()} mode.",
        "stream_url": f"/api/project/{target_pid}/stream",
    }


@app.get("/api/project/{project_id}/revisions")
@app.get("/api/projects/{project_id}/revisions")
async def get_project_revisions(project_id: str):
    """Return historical revision records for a project from SQLite."""
    revisions = db.get_revisions(project_id)
    return {
        "project_id": project_id,
        "revisions": revisions,
        "revision_count": len(revisions),
        "count": len(revisions),
    }


# ── Phase 4C Stage 1: Safe Revision Rollback Engine ───────────────────────────

@app.post("/api/project/{project_id}/rollback")
@app.post("/api/projects/{project_id}/rollback")
async def rollback_project(
    project_id: str,
    request: RollbackRequest,
):
    """
    Phase 4C Stage 1: Safe Revision Rollback.
    Restores exact historical revision snapshot without LLM regeneration or historical mutation.
    Creates a new forward revision (e.g. Rev 2 -> Rev 1 creates Rev 3).
    """
    # 1. Verify project exists
    project_data = db.get_project(project_id)
    if not project_data:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    # 2. Verify target revision exists
    target_rev = db.get_revision(project_id, request.target_revision)
    if not target_rev:
        raise HTTPException(
            status_code=404,
            detail=f"Target Revision {request.target_revision} not found for project {project_id}."
        )

    # 3. Verify snapshot status is VERIFIED_IMMUTABLE
    if target_rev.get("snapshot_status") != "VERIFIED_IMMUTABLE":
        status_val = target_rev.get("snapshot_status", "LEGACY_UNAVAILABLE")
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot rollback to Revision {request.target_revision}: historical snapshot status is '{status_val}'. "
                f"Legacy revisions without verified snapshots cannot be restored."
            ),
        )

    # 4. Retrieve or instantiate orchestrator engine
    engine = active_engines.get(project_id)
    if not engine:
        engine = OrchestratorEngine(project_id=project_id)
        active_engines[project_id] = engine

    # 5. Execute rollback
    try:
        result = await engine.rollback_revision(request.target_revision)
        if result.get("status") == "blocked":
            raise HTTPException(
                status_code=422,
                detail=result,
            )
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Rollback failed for project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Rollback execution failed: {str(e)}")


# ── Phase 4C: Filesystem Reconciliation ───────────────────────────────────────

@app.post("/api/project/{project_id}/reconcile")
@app.post("/api/projects/{project_id}/reconcile")
async def reconcile_project(
    project_id: str,
    revision_number: Optional[int] = None,
):
    """
    Durable recovery mechanism: Reconciles disk filesystem with immutable SQLite snapshot.
    Clears 'filesystem_desync' state once integrity verification passes.
    """
    project_data = db.get_project(project_id)
    if not project_data:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    engine = active_engines.get(project_id)
    if not engine:
        engine = OrchestratorEngine(project_id=project_id)
        active_engines[project_id] = engine

    try:
        res = engine.reconcile_filesystem(revision_number=revision_number)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Reconciliation failed for project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Filesystem reconciliation failed: {str(e)}")


# ── Project Update & Deletion (Phase 4A) ──────────────────────────────────────

@app.put("/api/project/{project_id}")
@app.put("/api/projects/{project_id}")
@app.patch("/api/project/{project_id}")
@app.patch("/api/projects/{project_id}")
async def update_project(project_id: str, request: ProjectUpdateRequest):
    """Update project metadata in SQLite."""
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.prompt is not None:
        updates["prompt"] = request.prompt
    if request.description is not None:
        updates["description"] = request.description
    if request.status is not None:
        updates["status"] = request.status

    updated = db.update_project(project_id, **updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # If active in memory, update context name as well
    engine = active_engines.get(project_id)
    if engine and engine.context:
        if request.name:
            engine.context.project_name = request.name

    return updated


@app.delete("/api/project/{project_id}")
@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project from SQLite and disk storage."""
    # Cancel running task if active
    engine = active_engines.pop(project_id, None)
    if engine and engine._task and not engine._task.done():
        engine._task.cancel()

    # Delete from SQLite
    deleted_db = db.delete_project(project_id)

    # Delete disk directory if exists
    proj_dir = PROJECTS_DIR / project_id
    if proj_dir.exists():
        shutil.rmtree(proj_dir, ignore_errors=True)

    if not deleted_db and not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    return {
        "status": "deleted",
        "project_id": project_id,
        "message": f"Project {project_id} successfully deleted.",
    }


# ── SSE Stream ────────────────────────────────────────────────────────────────

@app.get("/api/project/{project_id}/stream")
@app.get("/api/projects/{project_id}/stream")
async def stream_project_events(project_id: str):
    """
    Server-Sent Events endpoint for real-time agent activity.
    Streams progressive events with reconnect-safe history replay and heartbeats.
    """
    engine = active_engines.get(project_id)
    if engine:
        return StreamingResponse(
            engine.stream_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Check if project exists in SQLite (replay persisted events)
    persisted = db.get_project(project_id)
    if persisted:
        temp_engine = OrchestratorEngine(project_id=project_id)
        return StreamingResponse(
            temp_engine.stream_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Fallback to legacy orchestrator if present
    legacy = active_orchestrators.get(project_id)
    if legacy:
        async def event_generator():
            async for event in legacy.event_handler.stream():
                yield event

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    raise HTTPException(
        status_code=404,
        detail=f"No active pipeline found for project {project_id}",
    )


# ── Get Project State ─────────────────────────────────────────────────────────

@app.get("/api/project/{project_id}")
@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get the current state of a generated project."""
    engine = active_engines.get(project_id)
    if engine and engine.context:
        state = engine.context.to_state_dict()
        # Merge with persisted activities from SQLite to ensure full activity history
        persisted = db.get_complete_project_state(project_id)
        if persisted:
            state["activities"] = persisted.get("activities", [])
            if not state.get("files") and persisted.get("files"):
                state["files"] = persisted.get("files")
            state["revisions"] = persisted.get("revisions", [])
            state["revision_count"] = persisted.get("revision_count", len(state["revisions"]))
        return state

    # Fallback to SQLite complete state
    persisted_state = db.get_complete_project_state(project_id)
    if persisted_state:
        return persisted_state

    # Fallback to legacy ProjectManager
    pm = ProjectManager(project_id)
    state = pm.load_state()

    if not state.prompt:
        raise HTTPException(
            status_code=404,
            detail=f"Project {project_id} not found",
        )

    return state.model_dump()


# ── Get Project Activities (Phase 4A) ─────────────────────────────────────────

@app.get("/api/project/{project_id}/activities")
@app.get("/api/projects/{project_id}/activities")
async def get_project_activities(project_id: str):
    """Get chronological activity history for a project."""
    activities = db.get_activities(project_id)
    if not activities:
        engine = active_engines.get(project_id)
        if engine and engine.events_history:
            activities = [
                {
                    "event_type": e.type,
                    "agent_id": e.agent,
                    "agent_name": e.agent_name,
                    "message": e.message,
                    "data": e.data,
                    "timestamp": e.timestamp,
                }
                for e in engine.events_history
            ]
    return {
        "project_id": project_id,
        "activities": activities,
    }


# ── Get Project Files ─────────────────────────────────────────────────────────

@app.get("/api/project/{project_id}/files")
@app.get("/api/projects/{project_id}/files")
async def get_project_files(project_id: str):
    """Get list of all generated files for a project."""
    engine = active_engines.get(project_id)
    if engine and engine.context and engine.context.generated_files:
        return {
            "project_id": project_id,
            "files": [
                {
                    "path": f.path,
                    "filename": f.filename,
                    "content": f.content,
                    "file_type": f.filename.rsplit(".", 1)[-1] if "." in f.filename else "txt",
                    "category": f.category,
                }
                for f in engine.context.generated_files
            ],
        }

    # Check SQLite
    db_files = db.get_files(project_id)
    if db_files:
        return {
            "project_id": project_id,
            "files": [
                {
                    "path": f["path"],
                    "filename": f["filename"],
                    "content": f["content"],
                    "file_type": f["file_type"],
                    "category": f.get("category", "source"),
                }
                for f in db_files
            ],
        }

    pm = ProjectManager(project_id)
    state = pm.load_state()

    if not state.prompt:
        raise HTTPException(status_code=404, detail="Project not found")

    files = pm.get_all_files()
    return {
        "project_id": project_id,
        "files": [
            {
                "path": f.filename if "/" in f.filename else (
                    f"src/{f.filename}" if f.filename in ["index.html", "style.css", "script.js"] else f.filename
                ),
                "filename": f.filename.split("/")[-1],
                "content": f.content,
                "file_type": f.file_type,
            }
            for f in files
        ],
    }


@app.get("/api/project/{project_id}/files/{filename:path}")
@app.get("/api/projects/{project_id}/files/{filename:path}")
async def get_file_content(project_id: str, filename: str):
    """Get the content of a specific generated file."""
    engine = active_engines.get(project_id)
    if engine and engine.context:
        f = engine.context.get_file(filename)
        if f:
            return {"filename": f.filename, "content": f.content}

    # Check SQLite
    db_file = db.get_file(project_id, filename)
    if db_file:
        return {"filename": db_file["filename"], "content": db_file["content"]}

    pm = ProjectManager(project_id)
    content = pm.get_file_content(filename)

    if content is None:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    return {
        "filename": filename,
        "content": content,
    }


# ── Get Source Files for Live Preview ─────────────────────────────────────────

@app.get("/api/project/{project_id}/preview")
@app.get("/api/projects/{project_id}/preview")
async def get_preview_files(project_id: str, request: Request):
    """
    Get all source files (HTML/CSS/JS) needed for the live preview iframe.
    If requested directly by a browser (Accept: text/html), returns the rendered HTML page.
    """
    engine = active_engines.get(project_id)
    source_files = []

    if engine and engine.context and engine.context.generated_files:
        source_files = [f for f in engine.context.generated_files if f.category == "source"]
    else:
        # Check SQLite
        db_files = db.get_files(project_id)
        if db_files:
            source_files = [
                type("TempFile", (), {"path": f["path"], "filename": f["filename"], "content": f["content"], "category": f.get("category", "source")})()
                for f in db_files
                if f.get("category") == "source" or f["filename"].endswith((".html", ".css", ".js"))
            ]
        else:
            pm = ProjectManager(project_id)
            pm_files = pm.get_source_files()
            source_files = [
                type("TempFile", (), {"path": f"src/{f.filename}", "filename": f.filename, "content": f.content})()
                for f in pm_files
            ]

    if not source_files:
        raise HTTPException(
            status_code=404,
            detail="No source files available for preview",
        )

    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        html_file = next((f for f in source_files if f.path.endswith("index.html") or f.filename == "index.html"), None)
        css_file = next((f for f in source_files if f.path.endswith("style.css") or f.filename == "style.css"), None)
        js_file = next((f for f in source_files if f.path.endswith("script.js") or f.filename == "script.js"), None)

        if html_file:
            html = html_file.content
            if css_file:
                html = html.replace("</head>", f"<style>{css_file.content}</style></head>")
            if js_file:
                html = html.replace("</body>", f"<script>{js_file.content}</script></body>")
            return HTMLResponse(content=html)

    return {
        "project_id": project_id,
        "files": [
            {"path": f.path, "filename": f.filename, "content": f.content}
            for f in source_files
        ],
    }


# ── Export ZIP ────────────────────────────────────────────────────────────────

@app.get("/api/project/{project_id}/export")
@app.get("/api/projects/{project_id}/export")
async def export_project(project_id: str):
    """
    Download the complete generated project as a ZIP file.
    Contains all generated files.
    """
    pm = ProjectManager(project_id)
    state = pm.load_state()

    if not state.prompt:
        raise HTTPException(status_code=404, detail="Project not found")

    if state.status == ProjectStatus.GENERATING:
        raise HTTPException(
            status_code=409,
            detail="Project is still being generated. Please wait for completion.",
        )

    zip_buffer = ExportService.create_zip(pm)
    zip_filename = ExportService.get_zip_filename(pm)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
        },
    )


# ── Deploy ────────────────────────────────────────────────────────────────────

@app.post("/api/project/{project_id}/deploy")
@app.post("/api/projects/{project_id}/deploy")
async def deploy_project(project_id: str, provider: str = "vercel"):
    """
    Deploy the generated website to a hosting provider.
    Returns NOT_CONFIGURED status with clear guidance if VERCEL_TOKEN is absent.
    """
    pm = ProjectManager(project_id)
    state = pm.load_state()

    if not state.prompt:
        raise HTTPException(status_code=404, detail="Project not found")

    if state.status == ProjectStatus.GENERATING:
        raise HTTPException(
            status_code=409,
            detail="Project is still being generated. Wait for completion before deploying.",
        )

    pm.update_state(deployment_status="deploying")
    result = await deployment_service.deploy(pm, provider_name=provider)

    pm.update_state(
        deployment_status=result["status"],
        deployment_url=result.get("url"),
        status=(
            ProjectStatus.DEPLOYED if result["status"] == "deployed"
            else state.status
        ),
    )

    return result


# ── Deployment Providers ──────────────────────────────────────────────────────

@app.get("/api/deployment/providers")
async def list_deployment_providers():
    """List available deployment providers and configuration status."""
    return {
        "providers": deployment_service.list_providers(),
        "default": deployment_service.default_provider,
    }


# ── Run Server ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )
