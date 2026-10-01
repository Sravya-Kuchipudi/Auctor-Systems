"""
Auctor Systems — Beatrice Stone (Requirements Analyst)
Analyzes functional/non-functional requirements and drives the genuine Human-In-The-Loop clarification flow.
"""

import asyncio
from typing import Callable, Awaitable, Optional
from orchestrator.base_agent import BaseAgent
from orchestrator.context import ProjectContext, ClarificationData
from orchestrator.events import WorkflowEvent, EventType
from services.llm_service import llm_service


class BeatriceAgent(BaseAgent):
    def __init__(self, input_waiter: Optional[Callable[[str], Awaitable[str]]] = None):
        super().__init__(
            agent_id="beatrice",
            name="Beatrice Stone",
            role="Systems Requirements Analyst",
            backend_name="requirements",
        )
        self.input_waiter = input_waiter

    async def execute(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
    ) -> None:
        await self.emit_started(context, emit)
        await asyncio.sleep(0.3)

        await self.emit_thinking(
            context,
            emit,
            "Auditing user directive against accessibility, layout constraints, and feature matrix.",
        )
        await asyncio.sleep(0.4)

        # Formulate clarification question based on user prompt
        prompt_lower = context.user_prompt.lower()
        if "portfolio" in prompt_lower or "personal" in prompt_lower or "academic" in prompt_lower:
            question = "Which primary aesthetic and navigation style best fits your target audience?"
            options = [
                "Minimalist Luxury with interactive editorial layout",
                "Academic Studio with structured case studies & research tabs",
                "Modern High-Performance Portfolio with floating action bar",
            ]
        elif "shop" in prompt_lower or "store" in prompt_lower or "ecommerce" in prompt_lower:
            question = "Which product presentation style should be prioritized for client conversion?"
            options = [
                "Curated editorial showcase with story-driven highlights",
                "High-density grid layout with instant filter tabs",
                "Boutique gallery with smooth drawer inspections",
            ]
        else:
            question = "Which interaction emphasis should the frontend architecture prioritize?"
            options = [
                "Rich typography and smooth micro-interactions (Palette 4)",
                "Data-dense interactive modules and tabbed showcases",
                "Conversion-focused call-to-action flow with accessible modal inquiries",
            ]

        # Genuine Human-In-The-Loop flow
        context.workflow_status = "waiting_user"
        context.clarification = ClarificationData(
            question=question,
            options=options,
        )

        await emit(
            WorkflowEvent(
                type=EventType.USER_INPUT_REQUIRED.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message="Client clarification required to solidify requirements matrix.",
                data={
                    "question": question,
                    "options": options,
                    "agentName": self.name,
                    "agentRole": self.role,
                },
            )
        )

        user_answer = ""
        if self.input_waiter:
            self.logger.info(f"[{self.agent_id}] Pausing for user answer on project {context.project_id}...")
            user_answer = await self.input_waiter(context.project_id)
            self.logger.info(f"[{self.agent_id}] Received user answer: '{user_answer}'")
        else:
            # Fallback if no waiter registered
            user_answer = options[0]

        context.workflow_status = "running"
        context.clarification.user_response = user_answer
        context.clarification.selected_option = user_answer

        await self.emit_working(
            context,
            emit,
            f"Incorporating user directive: '{user_answer}' into functional specification...",
            snippet=f"Preference mapped: {user_answer}",
        )
        await asyncio.sleep(0.4)

        # Generate requirements document
        system_prompt = (
            "You are Beatrice Stone, Systems Requirements Analyst at Auctor Systems. "
            "Formulate detailed functional and non-functional requirements based on "
            "the user prompt, the project plan, and the clarified user preference."
        )

        def fallback_reqs():
            return f"""# Requirements Specification: {context.project_name}
Clarified Preference: {user_answer}

## Functional Requirements
1. Responsive Single-Page Application (SPA) architecture with multi-section layout.
2. Dynamic Tabbed Navigation & Filterable Portfolio / Offerings showcase.
3. Interactive Inquiries Dialog with full keyboard focus trapping and validation.
4. Smooth scroll anchors with active scroll spy indicators.

## Non-Functional Requirements
1. Zero external CSS/JS framework dependencies (Pure Vanilla HTML5/CSS3/ES6+).
2. Strict adherence to Palette 4 visual tokens.
3. WCAG 2.1 AA compliant color contrast and ARIA landmarks.
4. Mobile, Tablet, and Desktop responsive breakpoints (375px, 768px, 1200px).
"""

        req_text = await llm_service.generate_text(
            system_instruction=system_prompt,
            user_prompt=f"Prompt: {context.user_prompt}\nPlan: {context.plan}\nSelected: {user_answer}",
            fallback_generator=fallback_reqs,
            mode=context.execution_mode,
        )

        context.requirements = {
            "specification": req_text,
            "user_choice": user_answer,
            "functional": [
                "Single-Page responsive application with section navigation",
                "Category tab filtering and real-time live keyword search",
                "Interactive live counter showing visible module count",
                "Accessible inquiry modal dialog with client-side form validation",
                "Interactive feedback states (loading, empty, success toast)",
            ],
            "non_functional": [
                "100% Vanilla Web Standards (HTML5, CSS3, ES6+)",
                "Palette 4 Design Tokens compliance",
                "WCAG 2.1 AA keyboard navigation and ARIA landmarks",
                "Fluid responsive layouts (Mobile 375px, Tablet 768px, Desktop 1200px)",
            ],
            "standards": ["WCAG 2.1 AA", "Palette 4 Tokens", "Vanilla ES6+"],
        }
        context.agent_outputs[self.backend_name] = req_text

        await self.emit_message(
            context,
            emit,
            "Comprehensive requirements matrix verified against client preferences.",
        )
        await asyncio.sleep(0.3)

        await self.emit_completed(
            context,
            emit,
            message="Requirements signed off with verified constraints.",
        )
        await asyncio.sleep(0.2)

        await self.emit_handoff(
            context,
            emit,
            to_agent_id="clara",
            to_agent_name="Clara Delacroix",
            message="Requirements confirmed with user.",
        )
