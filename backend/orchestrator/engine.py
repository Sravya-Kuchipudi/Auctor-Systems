"""
Auctor Systems — Orchestrator Engine (Phase 3B)
Coordinates sequential agent execution, shared context passing,
human clarification input/resume, Astrid ↔ Maya QA revision loop,
and reconnect-safe Server-Sent Event streaming.
"""

import asyncio
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any
from uuid import uuid4

from orchestrator.context import ProjectContext, GeneratedFile
from orchestrator.events import WorkflowEvent, EventType
from orchestrator.registry import AgentRegistry
from orchestrator.agents.astrid import AstridAgent
from orchestrator.agents.genevieve import GenevieveAgent
from services.project_manager import ProjectManager
from models import AgentStatus, ProjectStatus
from database import db
from services.lock_manager import project_lock_manager, ConcurrencyConflictError

logger = logging.getLogger("auctor.engine")


class OrchestratorEngine:
    """
    Manages the lifecycle of an 8-agent generation run.
    Provides async event queue, human input resolution, and QA feedback loop.
    Persists all projects, files, and activity logs to SQLite.
    """

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or str(uuid4())
        self.context: Optional[ProjectContext] = None
        self.events_history: List[WorkflowEvent] = []
        self._listeners: List[asyncio.Queue] = []
        self._pending_user_input: Optional[asyncio.Future] = None
        self._task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self.project_manager = ProjectManager(self.project_id)

    async def emit_event(self, event: WorkflowEvent) -> None:
        """Store in history, persist to SQLite, and broadcast to all active SSE subscribers."""
        self.events_history.append(event)
        for q in self._listeners:
            await q.put(event)

        # Persist activity event to SQLite
        try:
            db.save_activity(
                project_id=self.project_id,
                event_type=event.type,
                agent_id=event.agent or "orchestrator",
                agent_name=event.agent_name or "Auctor Studio",
                message=event.message,
                data=event.data,
                timestamp=event.timestamp,
            )

            # Synchronize project state on specific milestone events
            if event.type == EventType.USER_INPUT_REQUIRED.value and event.data:
                db.update_project(self.project_id, clarification=event.data)
            elif event.type in (EventType.TEST_FAILED.value, EventType.TEST_PASSED.value):
                db.update_project(
                    self.project_id,
                    qa_state=event.data or {},
                    qa_revision_count=self.context.qa_revision_count if self.context else 0,
                )
            elif event.type == EventType.AGENT_STARTED.value:
                db.update_project(self.project_id, current_agent=event.agent)
        except Exception as e:
            logger.warning(f"Failed to persist activity event to SQLite: {e}")

    async def wait_for_user_input(self, project_id: str) -> str:
        """
        Called by Beatrice to pause execution until human provides input.
        """
        loop = asyncio.get_running_loop()
        self._pending_user_input = loop.create_future()
        logger.info(f"Orchestrator [{self.project_id}]: Waiting for user clarification...")
        answer = await self._pending_user_input
        self._pending_user_input = None
        logger.info(f"Orchestrator [{self.project_id}]: User clarification received: '{answer}'")
        return answer

    def provide_user_input(self, answer: str) -> bool:
        """
        Called when client submits POST /api/project/{id}/input or /clarification.
        Resumes Beatrice's paused execution.
        """
        if self._pending_user_input and not self._pending_user_input.done():
            self._pending_user_input.set_result(answer)
            if self.context and self.context.clarification:
                self.context.clarification.user_response = answer
                try:
                    db.update_project(
                        self.project_id,
                        clarification=self.context.clarification.model_dump(),
                    )
                except Exception as e:
                    logger.warning(f"Failed to update clarification in SQLite: {e}")
            return True
        logger.warning(f"Orchestrator [{self.project_id}]: No pending input prompt found.")
        return False

    def start(self, prompt: str, mode: str = "real", name: Optional[str] = None) -> str:
        """
        Initialize context and launch the async pipeline as an asyncio task.
        """
        project_lock_manager.check_conflict(self.project_id, op_name="initial_generation")
        self.context = ProjectContext(
            project_id=self.project_id,
            user_prompt=prompt,
            execution_mode=mode,
            workflow_status="running",
        )
        if name:
            self.context.project_name = name

        self.project_manager.initialize(prompt)
        self._is_running = True

        # Initialize project row in SQLite
        try:
            db.create_project(
                project_id=self.project_id,
                name=self.context.project_name,
                prompt=prompt,
                mode=mode,
                status="generating",
            )
        except Exception as e:
            logger.warning(f"Failed to initialize project in SQLite: {e}")

        # Launch background task
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run_pipeline())
        logger.info(f"Orchestrator pipeline task created for project {self.project_id} (mode={mode})")
        return self.project_id

    async def _run_pipeline(self) -> None:
        """
        Execute the 8 agents in sequence with QA revision loops and event broadcasts.
        """
        try:
            async with project_lock_manager.acquire(self.project_id, op_name="initial_generation", blocking=False):
                logger.info(f"Starting 8-agent workflow for project {self.project_id}")
                registry = AgentRegistry(input_waiter=self.wait_for_user_input)

                # 1. Workflow Started Event
                await self.emit_event(
                    WorkflowEvent(
                        type=EventType.WORKFLOW_STARTED.value,
                        project_id=self.project_id,
                        agent="victoria",
                        agent_name="Victoria Vance",
                        message="Auctor 8-agent autonomous pipeline initiated.",
                        data={"prompt": self.context.user_prompt, "mode": self.context.execution_mode},
                    )
                )

                # Agent sequence indices:
                # 0: Victoria, 1: Beatrice, 2: Clara, 3: Maya, 4: Astrid, 5: Genevieve, 6: Nadia, 7: Sophia
                agent_index = 0
                all_agents = registry.get_all()

                while agent_index < len(all_agents):
                    agent = all_agents[agent_index]
                    self.context.current_agent = agent.backend_name

                    # Execute current agent
                    logger.info(f"Executing agent [{agent.agent_id} - {agent.name}]")
                    await agent.execute(self.context, self.emit_event)

                    # Persist any updated files to disk and SQLite immediately
                    self._save_files_to_disk()

                    # Check for Astrid's QA Revision Loop
                    if agent.agent_id == "astrid" and self.context.qa_needs_revision:
                        logger.info(f"Astrid requested QA revision (count={self.context.qa_revision_count}). Routing back to Maya.")
                        # Route back to Maya (index 3)
                        agent_index = 3
                        continue

                    agent_index += 1

                # Workflow Completed
                self.context.workflow_status = "completed"
                self.context.current_agent = None

                # Update legacy ProjectManager state
                self.project_manager.update_state(
                    status=ProjectStatus.GENERATED,
                    current_agent=None,
                    outputs=self.context.agent_outputs,
                    files=self.project_manager.get_all_files(),
                )

                # Generate standardized completion summary
                summary = self.context.generate_completion_summary()

                # Rev 0 Baseline: Persist verified immutable snapshot before marking project completed
                existing_rev0 = db.get_revision(self.project_id, 0)
                if not existing_rev0 and self.context.generated_files:
                    staged_paths = [f.path for f in self.context.generated_files]
                    astrid = AstridAgent()
                    qa_report = astrid.audit_staged_context(self.context)
                    if not qa_report.get("passed", False):
                        rev0_err_msg = f"Rev 0 baseline blocked: QA check failed ({qa_report.get('checks_failed', 0)} failed)."
                        logger.warning(rev0_err_msg)
                        db.record_failure_diagnostic(
                            project_id=self.project_id,
                            event_type="rev0_qa_blocked",
                            message=rev0_err_msg,
                            data=qa_report,
                        )
                        self.context.workflow_status = "error"
                        self.context.error_message = rev0_err_msg
                        db.update_project(self.project_id, status="error")
                        await self.emit_event(
                            WorkflowEvent(
                                type=EventType.AGENT_ERROR.value,
                                project_id=self.project_id,
                                agent="astrid",
                                message=rev0_err_msg,
                                data={"qa_report": qa_report},
                            )
                        )
                        return

                    try:
                        qa_summary = f"Certified Clean by Astrid Lindqvist ({qa_report['checks_passed']}/{qa_report['checks_executed']} checks passed, {qa_report['checks_skipped']} skipped)"
                        db.commit_revision_atomic(
                            project_id=self.project_id,
                            revision_number=0,
                            prompt=self.context.user_prompt or "Initial project generation",
                            files=self.context.generated_files,
                            modified_files=staged_paths,
                            qa_summary=qa_summary,
                            snapshot_status="VERIFIED_IMMUTABLE",
                        )
                        logger.info(f"Rev 0 baseline verified and persisted atomically for {self.project_id}")
                    except Exception as rev0_err:
                        err_msg = f"Rev 0 baseline commit failed: {rev0_err}"
                        logger.error(err_msg)
                        db.record_failure_diagnostic(
                            project_id=self.project_id,
                            event_type="rev0_baseline_failure",
                            message=err_msg,
                            data={"error": str(rev0_err)},
                        )
                        self.context.workflow_status = "error"
                        self.context.error_message = err_msg
                        db.update_project(self.project_id, status="error")
                        await self.emit_event(
                            WorkflowEvent(
                                type=EventType.AGENT_ERROR.value,
                                project_id=self.project_id,
                                agent="orchestrator",
                                message=err_msg,
                                data={"error": str(rev0_err)},
                            )
                        )
                        return

                    # Verify disk integrity of Rev 0
                    integrity_errors = self.project_manager.verify_disk_integrity(self.context.generated_files)
                    if integrity_errors:
                        err_msg = f"Rev 0 disk integrity verification failed: {'; '.join(integrity_errors)}"
                        logger.critical(err_msg)
                        db.update_revision_status(self.project_id, 0, "filesystem_desync")
                        db.update_project(self.project_id, status="filesystem_desync")
                        self.context.workflow_status = "filesystem_desync"
                        self.context.error_message = err_msg
                        db.record_failure_diagnostic(
                            project_id=self.project_id,
                            event_type="rev0_disk_desync",
                            message=err_msg,
                            data={"errors": integrity_errors},
                        )
                        await self.emit_event(
                            WorkflowEvent(
                                type=EventType.AGENT_ERROR.value,
                                project_id=self.project_id,
                                agent="orchestrator",
                                message=err_msg,
                                data={"errors": integrity_errors},
                            )
                        )
                        return

                # Persist finalized completion state to SQLite ONLY after Rev 0 verification succeeds
                agent_statuses = {
                    "planning": "completed",
                    "requirements": "completed",
                    "design": "completed",
                    "development": "completed",
                    "testing": "completed",
                    "documentation": "completed",
                    "deployment": "completed",
                    "marketing": "completed",
                }
                try:
                    db.update_project(
                        self.project_id,
                        name=self.context.project_name,
                        description=self.context.project_description,
                        status="completed",
                        current_agent=None,
                        agent_statuses=agent_statuses,
                        requirements=self.context.requirements,
                        qa_state=self.context.test_results,
                        qa_revision_count=self.context.qa_revision_count,
                        completion_summary=summary,
                    )
                except Exception as e:
                    logger.warning(f"Failed to update completion state in SQLite: {e}")

                self.context.workflow_status = "completed"
                await self.emit_event(
                    WorkflowEvent(
                        type=EventType.WORKFLOW_COMPLETED.value,
                        project_id=self.project_id,
                        message=f"Multi-agent website generation completed successfully: {self.context.project_name}.",
                        data={
                            "project_id": self.project_id,
                            "project_name": self.context.project_name,
                            "file_count": len(self.context.generated_files),
                            "qa_revision_count": self.context.qa_revision_count,
                            "completion_summary": summary,
                        },
                    )
                )
                logger.info(f"Workflow completed successfully for project {self.project_id}")

        except asyncio.CancelledError:
            logger.warning(f"Workflow cancelled for project {self.project_id}")
            self.context.workflow_status = "error"
            self.context.error_message = "Workflow cancelled."
            try:
                db.update_project(self.project_id, status="error")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Workflow failed for project {self.project_id}: {e}", exc_info=True)
            self.context.workflow_status = "error"
            self.context.error_message = str(e)
            try:
                db.update_project(self.project_id, status="error")
            except Exception:
                pass
            await self.emit_event(
                WorkflowEvent(
                    type=EventType.AGENT_ERROR.value,
                    project_id=self.project_id,
                    agent=self.context.current_agent or "orchestrator",
                    message=f"Pipeline error: {str(e)}",
                    data={"error": str(e)},
                )
            )
        finally:
            self._is_running = False

    def _hydrate_from_db(self) -> None:
        """Hydrate project context and files from SQLite if not present in memory."""
        state = db.get_complete_project_state(self.project_id)
        if not state:
            return
        self.context = ProjectContext(
            project_id=self.project_id,
            user_prompt=state.get("prompt", ""),
            project_name=state.get("project_name", "Auctor Project"),
            project_description=state.get("project_description", ""),
            execution_mode=state.get("mode", "real"),
            workflow_status=state.get("status", "completed"),
            requirements=state.get("requirements") or {},
            qa_state=state.get("qa_state") or {},
            qa_revision_count=state.get("qa_revision_count", 0),
            completion_summary=state.get("completion_summary") or {},
        )
        for f in state.get("files", []):
            self.context.set_file(
                f["path"],
                f["filename"],
                f["content"],
                category=f.get("category", "source"),
            )

    def modify(self, prompt: str, mode: str = "real") -> str:
        """
        Phase 4B: Launch targeted modification revision on existing project.
        """
        project_lock_manager.check_conflict(self.project_id, op_name="revision_creation")
        if not self.context or not self.context.generated_files:
            self._hydrate_from_db()

        self.context.workflow_status = "running"
        self._is_running = True

        # Launch background modification task
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run_modification_pipeline(prompt, mode))
        logger.info(f"Orchestrator modification task started for project {self.project_id} (prompt='{prompt}')")
        return self.project_id

    async def _run_modification_pipeline(self, prompt: str, mode: str) -> None:
        """
        Phase 4B Targeted Revision Flow:
        User -> Maya Thorne (Patch) -> Astrid Lindqvist (Differential QA)
        -> (if defects -> Maya remediation -> Astrid re-test)
        -> Genevieve Ward (Changelog Docs) -> (Conditional Nadia/Sophia) -> Complete
        """
        try:
            async with project_lock_manager.acquire(self.project_id, op_name="revision_creation", blocking=False):
                logger.info(f"Starting revision pipeline for project {self.project_id}: '{prompt}'")
                registry = AgentRegistry(input_waiter=self.wait_for_user_input)

                # Determine revision numbering (Rev 0 -> Rev 1 -> Rev 2)
                prev_revisions = db.get_revisions(self.project_id)
                new_rev_number = 1 if not prev_revisions else max(r["revision_number"] for r in prev_revisions) + 1

                # Update project status in SQLite
                db.update_project(self.project_id, status="generating", current_agent="development")

                # 1. Revision Started Event
                await self.emit_event(
                    WorkflowEvent(
                        type=EventType.REVISION_STARTED.value,
                        project_id=self.project_id,
                        agent="maya",
                        agent_name="Maya Thorne",
                        message=f"Revision {new_rev_number} initiated: '{prompt}'",
                        data={
                            "revision_number": new_rev_number,
                            "directive": prompt,
                            "mode": mode,
                        },
                    )
                )

                # 2. Maya Thorne executes targeted modification
                maya = registry.get_by_id("maya")
                self.context.current_agent = "development"
                modified_files = await maya.execute_modification(self.context, self.emit_event, prompt, mode=mode)
                self._save_files_to_disk()

                # 3. Astrid Lindqvist differential QA
                astrid = registry.get_by_id("astrid")
                self.context.current_agent = "testing"
                defects = await astrid.execute_differential_qa(self.context, self.emit_event, modified_files)

                # 4. Maya remediation loop if defects found
                remed_count = 0
                while defects and self.context.qa_needs_revision and remed_count < 3:
                    remed_count += 1
                    logger.info(f"Astrid found {len(defects)} defects during revision. Remediation by Maya (attempt {remed_count}).")
                    self.context.current_agent = "development"
                    self.context.qa_revision_count += 1
                    await maya.execute(self.context, self.emit_event)
                    self._save_files_to_disk()
                    self.context.current_agent = "testing"
                    defects = await astrid.execute_differential_qa(self.context, self.emit_event, modified_files)

                # 5. Genevieve Ward updates documentation
                genevieve = registry.get_by_id("genevieve")
                self.context.current_agent = "documentation"
                await genevieve.execute_revision_documentation(
                    self.context,
                    self.emit_event,
                    prompt,
                    new_rev_number,
                    modified_files,
                )
                self._save_files_to_disk()

                # 6. Conditional updates for Nadia and Sophia
                lower_p = prompt.lower()
                if any(k in lower_p for k in ["route", "vercel", "edge", "deploy", "header", "redirect", "cache"]):
                    nadia = registry.get_by_id("nadia")
                    self.context.current_agent = "deployment"
                    await nadia.execute(self.context, self.emit_event)
                    self._save_files_to_disk()

                if any(k in lower_p for k in ["marketing", "seo", "launch", "campaign", "social", "copy"]):
                    sophia = registry.get_by_id("sophia")
                    self.context.current_agent = "marketing"
                    await sophia.execute(self.context, self.emit_event)
                    self._save_files_to_disk()

                # 7. Finalize Revision State
                self.context.workflow_status = "completed"
                self.context.current_agent = None
                self.context.qa_revision_count = new_rev_number
                summary = self.context.generate_completion_summary()

                # Persist revision & updated project state in SQLite atomically with immutable snapshot
                try:
                    db.commit_revision_atomic(
                        project_id=self.project_id,
                        revision_number=new_rev_number,
                        prompt=prompt,
                        files=self.context.generated_files,
                        modified_files=modified_files,
                        qa_summary=f"Certified Clean by Astrid Lindqvist ({len(modified_files)} files modified)",
                        snapshot_status="VERIFIED_IMMUTABLE",
                    )
                except Exception as commit_err:
                    logger.error(f"Atomic revision commit failed for {self.project_id} (Rev {new_rev_number}): {commit_err}")
                    db.record_failure_diagnostic(
                        project_id=self.project_id,
                        event_type="atomic_revision_failed",
                        message=f"Atomic commit failed for Revision {new_rev_number}: {commit_err}",
                        data={"revision_number": new_rev_number, "error": str(commit_err)},
                    )
                    raise commit_err

                db.update_project(
                    self.project_id,
                    status="completed",
                    current_agent=None,
                    qa_revision_count=new_rev_number,
                    completion_summary=summary,
                )

                # 8. Emit Revision Completed & Project Generated Events
                await self.emit_event(
                    WorkflowEvent(
                        type=EventType.REVISION_COMPLETED.value,
                        project_id=self.project_id,
                        agent="sophia",
                        agent_name="Sophia Laurent",
                        message=f"Revision {new_rev_number} completed and verified for '{prompt}'.",
                        data={
                            "project_id": self.project_id,
                            "revision_number": new_rev_number,
                            "modified_files": modified_files,
                            "directive": prompt,
                            "completion_summary": summary,
                        },
                    )
                )
                await self.emit_event(
                    WorkflowEvent(
                        type=EventType.PROJECT_GENERATED.value,
                        project_id=self.project_id,
                        agent="orchestrator",
                        agent_name="Auctor Studio",
                        message=f"Live Preview and workspace updated with Revision {new_rev_number}.",
                        data={
                            "project_id": self.project_id,
                            "revision_number": new_rev_number,
                            "files": [{"path": f.path, "filename": f.filename} for f in self.context.generated_files],
                        },
                    )
                )
                logger.info(f"Revision {new_rev_number} completed successfully for project {self.project_id}")

        except asyncio.CancelledError:
            logger.warning(f"Revision pipeline cancelled for project {self.project_id}")
            self.context.workflow_status = "error"
            self.context.error_message = "Revision cancelled."
            try:
                db.update_project(self.project_id, status="error")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Revision pipeline failed for project {self.project_id}: {e}", exc_info=True)
            self.context.workflow_status = "error"
            self.context.error_message = str(e)
            try:
                db.update_project(self.project_id, status="error")
            except Exception:
                pass
        finally:
            self._is_running = False

    def _save_files_to_disk(self) -> None:
        """Write all generated files from context into the project directory and SQLite."""
        if not self.context:
            return
        for file in self.context.generated_files:
            # 1. Disk persistence for backward compatibility
            try:
                self.project_manager.write_file(file.path, file.content)
            except Exception as e:
                logger.warning(f"Could not save file {file.path} to disk: {e}")

            # 2. SQLite persistence with complete file content
            try:
                ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
                db.save_file(
                    project_id=self.project_id,
                    path=file.path,
                    filename=file.filename,
                    content=file.content,
                    file_type=ext,
                    category=file.category,
                )
            except Exception as e:
                logger.warning(f"Could not save file {file.path} to SQLite: {e}")

    async def stream_events(self) -> AsyncGenerator[str, None]:
        """
        Reconnect-safe event stream generator.
        First replays all historical events, then yields new events as they arrive.
        """
        queue = asyncio.Queue()
        self._listeners.append(queue)

        try:
            # 1. Replay past events from memory or SQLite
            is_actively_waiting = bool(getattr(self, "_pending_user_input", None) is not None and not self._pending_user_input.done())
            if self.events_history:
                for past_event in list(self.events_history):
                    if self._is_running and past_event.type in [EventType.WORKFLOW_COMPLETED.value, EventType.REVISION_COMPLETED.value]:
                        continue
                    if past_event.type == EventType.USER_INPUT_REQUIRED.value and not is_actively_waiting:
                        continue
                    yield past_event.format_sse()
            else:
                saved_activities = db.get_activities(self.project_id)
                for act in saved_activities:
                    if self._is_running and act["event_type"] in [EventType.WORKFLOW_COMPLETED.value, EventType.REVISION_COMPLETED.value]:
                        continue
                    if act["event_type"] == EventType.USER_INPUT_REQUIRED.value and not is_actively_waiting:
                        continue
                    evt = WorkflowEvent(
                        type=act["event_type"],
                        project_id=self.project_id,
                        agent=act["agent_id"],
                        agent_name=act["agent_name"],
                        message=act["message"],
                        data=act.get("data"),
                        timestamp=act["timestamp"],
                    )
                    yield evt.format_sse()

            # If already completed or failed, close after replay
            if not self._is_running and self.context and self.context.workflow_status in ["completed", "error"]:
                return

            # 2. Stream live events with heartbeat
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event.format_sse()

                    if event.type in [EventType.WORKFLOW_COMPLETED.value, EventType.REVISION_COMPLETED.value, EventType.AGENT_ERROR.value]:
                        break
                except asyncio.TimeoutError:
                    # Send heartbeat to prevent connection timeout
                    heartbeat = WorkflowEvent(
                        type=EventType.HEARTBEAT.value,
                        project_id=self.project_id,
                        message="heartbeat",
                    )
                    yield heartbeat.format_sse()
                    if not self._is_running:
                        break
        finally:
            if queue in self._listeners:
                self._listeners.remove(queue)

    async def rollback_revision(self, target_revision: int) -> Dict[str, Any]:
        """
        Phase 4C Stage 1: Safe Revision Rollback.
        1. Validates target snapshot exists and is VERIFIED_IMMUTABLE.
        2. Restores files in an isolated staging context.
        3. Genevieve applies deterministic rollback documentation to the staged set.
        4. Astrid executes dynamic QA verification on the staged context.
        5. If QA fails: active project state remains 100% untouched, failure diagnostic is recorded independently, and structured blocker report returned.
        6. If QA passes: creates new forward revision (max_rev + 1), commits active files, revision metadata, and immutable snapshot atomically.
        7. Exact restoration: removes disk and db files absent from the target snapshot.
        8. Emits workflow events and returns structured success report.
        """
        async with project_lock_manager.acquire(self.project_id, op_name="rollback", blocking=False):
            logger.info(f"Orchestrator [{self.project_id}]: Initiating rollback to Revision {target_revision}...")

            # 1. Cryptographic SHA-256 and snapshot integrity verification
            is_valid, snapshot_files, integrity_errors = db.verify_snapshot_integrity(self.project_id, target_revision)
            if not is_valid:
                err_msg = f"Cannot rollback to Revision {target_revision}: Snapshot integrity verification failed: {'; '.join(integrity_errors)}"
                logger.error(err_msg)
                db.record_failure_diagnostic(
                    project_id=self.project_id,
                    event_type="snapshot_integrity_failure",
                    message=err_msg,
                    data={"target_revision": target_revision, "errors": integrity_errors},
                )
                raise ValueError(err_msg)

            # 2. Isolated staging context
            if not self.context or not self.context.generated_files:
                self._hydrate_from_db()

            staging_context = ProjectContext(
                project_id=self.project_id,
                user_prompt=self.context.user_prompt if self.context else "",
                project_name=self.context.project_name if self.context else "Auctor Project",
                project_description=self.context.project_description if self.context else "",
                execution_mode=self.context.execution_mode if self.context else "real",
                workflow_status="running",
            )
            for sf in snapshot_files:
                staging_context.set_file(
                    sf["path"],
                    sf["filename"],
                    sf["content"],
                    category=sf.get("category", "source"),
                )

            # 3. Forward revision numbering
            all_revisions = db.get_revisions(self.project_id)
            max_rev = max([r["revision_number"] for r in all_revisions], default=0)
            new_rev_number = max_rev + 1

            # 4. Deterministic rollback documentation in staging context
            genevieve = GenevieveAgent()
            modified_docs = genevieve.apply_rollback_documentation(
                staging_context,
                target_revision=target_revision,
                new_rev_number=new_rev_number,
            )

            # 5. Isolated Astrid QA verification
            astrid = AstridAgent()
            qa_report = astrid.audit_staged_context(staging_context)

            if not qa_report["passed"]:
                # QA failed in staging context! Leave active state 100% untouched.
                diag_message = f"Rollback to Revision {target_revision} blocked: staged QA check failed ({qa_report['checks_failed']} failed)."
                logger.warning(f"Orchestrator [{self.project_id}]: {diag_message}")
                db.record_failure_diagnostic(
                    project_id=self.project_id,
                    event_type="rollback_qa_blocked",
                    message=diag_message,
                    data={
                        "target_revision": target_revision,
                        "attempted_forward_revision": new_rev_number,
                        "defects": [d.model_dump() if hasattr(d, "model_dump") else d for d in qa_report.get("defects", [])],
                        "blockers": qa_report.get("blockers", []),
                        "checks": qa_report.get("checks", []),
                    },
                )
                return {
                    "status": "blocked",
                    "project_id": self.project_id,
                    "target_revision": target_revision,
                    "attempted_forward_revision": new_rev_number,
                    "message": diag_message,
                    "blockers": qa_report.get("blockers", []),
                    "defects": [d.model_dump() if hasattr(d, "model_dump") else d for d in qa_report.get("defects", [])],
                    "qa_report": qa_report,
                }

            # 6. Commit atomic revision and exact file restoration
            staged_paths = [f.path for f in staging_context.generated_files]
            prompt = f"Rollback to Revision {target_revision}"
            qa_summary = f"Certified Clean by Astrid Lindqvist ({qa_report['checks_passed']}/{qa_report['checks_executed']} checks passed, {qa_report['checks_skipped']} skipped)"

            try:
                # Atomic database commit
                db.commit_revision_atomic(
                    project_id=self.project_id,
                    revision_number=new_rev_number,
                    prompt=prompt,
                    files=staging_context.generated_files,
                    modified_files=staged_paths,
                    qa_summary=qa_summary,
                    snapshot_status="VERIFIED_IMMUTABLE",
                )
            except Exception as commit_err:
                logger.error(f"Atomic commit failed during rollback for {self.project_id}: {commit_err}")
                db.record_failure_diagnostic(
                    project_id=self.project_id,
                    event_type="atomic_rollback_failure",
                    message=f"Atomic commit failed during rollback: {commit_err}",
                    data={"target_revision": target_revision, "attempted_forward_revision": new_rev_number, "error": str(commit_err)},
                )
                raise commit_err

            # Exact disk restoration: remove absent files and write verified files
            disk_sync_errors = []
            try:
                self.project_manager.remove_files_except(set(staged_paths))
                for f in staging_context.generated_files:
                    self.project_manager.write_file(f.path, f.content)

                # Verify disk integrity matches the committed revision exactly
                integrity_errors = self.project_manager.verify_disk_integrity(staging_context.generated_files)
                if integrity_errors:
                    disk_sync_errors.extend(integrity_errors)
            except Exception as disk_err:
                logger.error(f"Error syncing rollback files to disk for {self.project_id}: {disk_err}")
                disk_sync_errors.append(str(disk_err))

            if disk_sync_errors:
                err_msg = "; ".join(disk_sync_errors)
                logger.critical(
                    f"Filesystem desynchronization detected for project {self.project_id} (Rev {new_rev_number}): {err_msg}"
                )
                # 1. Update revision status to 'filesystem_desync'
                db.update_revision_status(self.project_id, new_rev_number, "filesystem_desync")
                db.update_project(self.project_id, status="filesystem_desync")
                if self.context:
                    self.context.workflow_status = "filesystem_desync"

                # 2. Record independent failure diagnostic
                db.record_failure_diagnostic(
                    project_id=self.project_id,
                    event_type="filesystem_sync_failure",
                    message=f"Filesystem restoration failed after SQLite commit for Rev {new_rev_number}: {err_msg}",
                    data={
                        "target_revision": target_revision,
                        "new_revision": new_rev_number,
                        "errors": disk_sync_errors,
                    },
                )

                # 3. Emit failure event
                await self.emit_event(
                    WorkflowEvent(
                        type=EventType.AGENT_ERROR.value,
                        project_id=self.project_id,
                        agent="orchestrator",
                        agent_name="Auctor Studio",
                        message=f"Filesystem restoration failed for Revision {new_rev_number}. System marked as 'filesystem_desync'. Reconciliation required.",
                        data={"errors": disk_sync_errors, "revision_number": new_rev_number},
                    )
                )

                # 4. Never report success when filesystem is inconsistent
                raise RuntimeError(
                    f"Filesystem restoration failed after SQLite commit for Rev {new_rev_number}: {err_msg}. "
                    f"Status marked 'filesystem_desync'. Reconciliation required."
                )

            # Update in-memory context and completion summary
            if self.context:
                self.context.generated_files = list(staging_context.generated_files)
                self.context.qa_revision_count = new_rev_number
                self.context.workflow_status = "completed"
                summary = self.context.generate_completion_summary()
                db.update_project(
                    self.project_id,
                    status="completed",
                    current_agent=None,
                    qa_revision_count=new_rev_number,
                    completion_summary=summary,
                )

            # 7. Emit workflow events
            await self.emit_event(
                WorkflowEvent(
                    type=EventType.REVISION_STARTED.value,
                    project_id=self.project_id,
                    agent="orchestrator",
                    agent_name="Auctor Studio",
                    message=f"Rollback to Revision {target_revision} initiated.",
                    data={"target_revision": target_revision, "new_revision": new_rev_number},
                )
            )
            await self.emit_event(
                WorkflowEvent(
                    type=EventType.QA_VERIFIED.value,
                    project_id=self.project_id,
                    agent="astrid",
                    agent_name="Astrid Lindqvist",
                    message=f"Staged rollback certified clean by Astrid Lindqvist ({qa_report['checks_passed']}/{qa_report['checks_executed']} checks passed, {qa_report['checks_skipped']} skipped).",
                    data=qa_report,
                )
            )
            await self.emit_event(
                WorkflowEvent(
                    type=EventType.REVISION_COMPLETED.value,
                    project_id=self.project_id,
                    agent="sophia",
                    agent_name="Sophia Laurent",
                    message=f"Rollback to Revision {target_revision} successfully applied as Revision {new_rev_number}.",
                    data={
                        "project_id": self.project_id,
                        "target_revision": target_revision,
                        "revision_number": new_rev_number,
                        "restored_files_count": len(staged_paths),
                    },
                )
            )
            await self.emit_event(
                WorkflowEvent(
                    type=EventType.PROJECT_GENERATED.value,
                    project_id=self.project_id,
                    agent="orchestrator",
                    agent_name="Auctor Studio",
                    message=f"Live preview restored to Revision {target_revision}.",
                    data={
                        "project_id": self.project_id,
                        "revision_number": new_rev_number,
                        "files": [{"path": f.path, "filename": f.filename} for f in staging_context.generated_files],
                    },
                )
            )

            logger.info(f"Rollback to Revision {target_revision} completed as Revision {new_rev_number} for {self.project_id}")
            return {
                "status": "success",
                "project_id": self.project_id,
                "target_revision": target_revision,
                "new_revision": new_rev_number,
                "restored_file_count": len(staged_paths),
                "files": staged_paths,
                "modified_docs": modified_docs,
                "qa_report": qa_report,
                "message": f"Successfully rolled back to Revision {target_revision} as Revision {new_rev_number}.",
            }

    def reconcile_filesystem(self, revision_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Durable recovery mechanism for filesystem desynchronization.
        Uses the immutable SQLite snapshot as the single source of truth to heal the disk.
        Clears 'filesystem_desync' state once verification passes.
        """
        # Check concurrency conflict
        project_lock_manager.check_conflict(self.project_id, op_name="reconciliation")

        # Determine revision to reconcile against
        if revision_number is None:
            revisions = db.get_revisions(self.project_id)
            if not revisions:
                raise ValueError(f"Cannot reconcile: No revisions found for project {self.project_id}")
            revision_number = max(r["revision_number"] for r in revisions)

        rev_record = db.get_revision(self.project_id, revision_number)
        if not rev_record:
            raise ValueError(f"Revision {revision_number} not found for project {self.project_id}")

        # Cryptographic SHA-256 and snapshot integrity verification
        is_valid, snapshot_files, integrity_errors = db.verify_snapshot_integrity(self.project_id, revision_number)
        if not is_valid:
            err_msg = f"Cannot reconcile Revision {revision_number}: Snapshot integrity verification failed: {'; '.join(integrity_errors)}"
            logger.error(err_msg)
            db.record_failure_diagnostic(
                project_id=self.project_id,
                event_type="snapshot_integrity_failure",
                message=err_msg,
                data={"revision_number": revision_number, "errors": integrity_errors},
            )
            raise ValueError(err_msg)

        staged_paths = [f["path"] for f in snapshot_files]

        try:
            self.project_manager.remove_files_except(set(staged_paths))
            for f in snapshot_files:
                self.project_manager.write_file(f["path"], f["content"])

            integrity_errors = self.project_manager.verify_disk_integrity(snapshot_files)
            if integrity_errors:
                raise IOError(f"Post-reconciliation integrity check failed: {'; '.join(integrity_errors)}")

            # Successfully restored disk!
            db.update_revision_status(self.project_id, revision_number, "completed")
            db.update_project(self.project_id, status="completed", qa_revision_count=revision_number)
            if self.context:
                self.context.workflow_status = "completed"
                self.context.qa_revision_count = revision_number
                self.context.generated_files = [
                    GeneratedFile(
                        filename=f["filename"],
                        path=f["path"],
                        content=f["content"],
                        category=f.get("category", "source"),
                    )
                    for f in snapshot_files
                ]

            db.record_failure_diagnostic(
                project_id=self.project_id,
                event_type="filesystem_reconciliation_success",
                message=f"Filesystem successfully reconciled to Revision {revision_number}.",
                data={"revision_number": revision_number, "files_count": len(snapshot_files)},
            )

            logger.info(f"Filesystem successfully reconciled for {self.project_id} (Rev {revision_number})")
            return {
                "status": "success",
                "project_id": self.project_id,
                "revision_number": revision_number,
                "reconciled_files_count": len(snapshot_files),
                "message": f"Successfully reconciled filesystem with Revision {revision_number} snapshot.",
            }

        except Exception as e:
            logger.critical(f"Reconciliation failed for {self.project_id}: {e}")
            db.update_revision_status(self.project_id, revision_number, "filesystem_desync")
            db.update_project(self.project_id, status="filesystem_desync")
            db.record_failure_diagnostic(
                project_id=self.project_id,
                event_type="filesystem_reconciliation_failed",
                message=f"Filesystem reconciliation failed: {e}",
                data={"revision_number": revision_number, "error": str(e)},
            )
            raise e

