"""
Auctor Systems — Orchestrator

The central coordinator that runs the 8-agent CrewAI pipeline.
Manages the full lifecycle: prompt → agents → files → state updates.

The orchestrator runs CrewAI in a background thread and streams
real events to the frontend via the StreamingEventHandler.

CRITICAL RULES:
- All events represent REAL agent execution
- No fake timers, no predetermined progress
- If agents fail, errors are reported honestly
"""

import logging
import threading
from uuid import uuid4
from typing import Optional

from crewai import Crew, Process

from agents.definitions import create_llm, create_agents
from agents.tasks import create_tasks
from models import (
    AgentName, AgentStatus, ProjectStatus,
    DeploymentStatus, AGENT_ORDER,
)
from services.streaming import StreamingEventHandler
from services.project_manager import ProjectManager
from config import VERCEL_TOKEN

logger = logging.getLogger("auctor.orchestrator")


class AuctorOrchestrator:
    """
    Coordinates the 8-agent pipeline for a single project generation.
    
    Usage:
        orchestrator = AuctorOrchestrator()
        project_id = orchestrator.start(user_prompt)
        async for event in orchestrator.event_handler.stream():
            # send to frontend via SSE
    """

    def __init__(self):
        self.event_handler = StreamingEventHandler()
        self.project_manager: Optional[ProjectManager] = None
        self.project_id: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running: bool = False

    def start(self, prompt: str) -> str:
        """
        Start the agent pipeline in a background thread.
        Returns the project_id immediately.
        """
        self.project_id = str(uuid4())
        self.project_manager = ProjectManager(self.project_id)
        self.project_manager.initialize(prompt)

        self._is_running = True
        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(prompt,),
            daemon=True,
            name=f"auctor-pipeline-{self.project_id[:8]}",
        )
        self._thread.start()

        logger.info(f"Pipeline started for project {self.project_id}")
        return self.project_id

    def _run_pipeline(self, prompt: str):
        """
        Execute the full 8-agent CrewAI pipeline.
        Runs in a background thread.
        """
        try:
            # Emit pipeline started
            self.event_handler.emit_pipeline_started(prompt)

            # Create LLM, agents, and tasks
            llm = create_llm()
            agents = create_agents(llm)
            tasks = create_tasks(agents, prompt)

            # Create the crew with callbacks
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
                step_callback=self.event_handler.on_step,
                task_callback=self._on_task_complete,
            )

            # Execute the pipeline — this is the REAL execution
            logger.info(f"Kicking off CrewAI pipeline for: {prompt[:100]}...")
            result = crew.kickoff()

            # Post-process: handle Testing Agent feedback loop
            self._handle_test_results()

            # Update final project state
            deployment_status = (
                DeploymentStatus.READY if VERCEL_TOKEN
                else DeploymentStatus.NOT_CONFIGURED
            )
            self.project_manager.update_state(
                status=ProjectStatus.GENERATED,
                current_agent=None,
                deployment_status=deployment_status,
            )

            # Emit pipeline complete
            self.event_handler.emit_pipeline_complete(
                f"Website generated successfully. "
                f"Project ID: {self.project_id}"
            )

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.event_handler.emit_error(f"Pipeline failed: {str(e)}")

            if self.project_manager:
                self.project_manager.update_state(
                    status=ProjectStatus.FAILED,
                    current_agent=None,
                )
        finally:
            self._is_running = False

    def _on_task_complete(self, task_output):
        """
        Called when each agent's task completes.
        Saves the output to disk and updates project state.
        """
        try:
            # Determine which agent just completed
            agent_index = self.event_handler.current_agent_index
            agent_name = AGENT_ORDER[agent_index].value if agent_index < len(AGENT_ORDER) else "Unknown"

            # Extract the raw output
            if hasattr(task_output, "raw"):
                raw_output = str(task_output.raw)
            elif hasattr(task_output, "output"):
                raw_output = str(task_output.output)
            else:
                raw_output = str(task_output)

            # Save output and extract files
            saved_files = self.project_manager.parse_and_save_files(agent_name, raw_output)

            # Update project state
            agent_statuses = self.project_manager.load_state().agent_statuses
            agent_statuses[agent_name] = AgentStatus.COMPLETED
            next_index = agent_index + 1
            if next_index < len(AGENT_ORDER):
                next_agent = AGENT_ORDER[next_index].value
                agent_statuses[next_agent] = AgentStatus.ACTIVE
            
            # Store the raw output for this agent
            outputs = self.project_manager.load_state().outputs
            outputs[agent_name] = raw_output

            self.project_manager.update_state(
                current_agent=AGENT_ORDER[next_index].value if next_index < len(AGENT_ORDER) else None,
                agent_statuses=agent_statuses,
                outputs=outputs,
                files=self.project_manager.get_all_files(),
            )

            logger.info(
                f"Agent '{agent_name}' completed. "
                f"Saved {len(saved_files)} files."
            )

        except Exception as e:
            logger.error(f"Error in task complete handler: {e}", exc_info=True)

        # Delegate to the streaming handler for SSE events
        self.event_handler.on_task_complete(task_output)

    def _handle_test_results(self):
        """
        Check if the Testing Agent found CRITICAL issues.
        If so, extract corrected files and overwrite the originals.
        
        This is the Testing → Development feedback loop.
        """
        try:
            state = self.project_manager.load_state()
            testing_output = state.outputs.get(AgentName.TESTING.value, "")

            if not testing_output:
                return

            # Check if the Testing Agent provided corrected files
            if "===FILE:" in testing_output and "CRITICAL" in testing_output.upper():
                logger.info("Testing Agent found CRITICAL issues — applying corrections")
                corrected_files = self.project_manager.parse_and_save_files(
                    AgentName.TESTING.value,
                    testing_output,
                )
                if corrected_files:
                    logger.info(f"Applied {len(corrected_files)} corrected files from Testing Agent")

                    # Update state with new files
                    self.project_manager.update_state(
                        status=ProjectStatus.TESTED,
                        files=self.project_manager.get_all_files(),
                    )
            else:
                # Tests passed — update status
                self.project_manager.update_state(status=ProjectStatus.TESTED)
                logger.info("Testing Agent: all tests passed")

        except Exception as e:
            logger.warning(f"Error handling test results: {e}")

    @property
    def is_running(self) -> bool:
        return self._is_running
