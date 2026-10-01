"""
Auctor Systems — Victoria Vance (Planning Specialist)
Analyzes directives, structures project scope, pages, and milestones.
"""

import asyncio
from typing import Callable, Awaitable
from orchestrator.base_agent import BaseAgent
from orchestrator.context import ProjectContext
from orchestrator.events import WorkflowEvent
from services.llm_service import llm_service


class VictoriaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="victoria",
            name="Victoria Vance",
            role="Planning Specialist",
            backend_name="planning",
        )

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
            f"Deconstructing directive: '{context.user_prompt[:80]}...' into architectural milestones.",
        )
        await asyncio.sleep(0.4)

        await self.emit_working(
            context,
            emit,
            "Formulating site hierarchy, target personas, and scope breakdown...",
            snippet="Site Architecture: Hero Section, Interactive Showcase, About/Philosophy, Contact Dialog",
        )
        await asyncio.sleep(0.4)

        # Plan generation via LLM or deterministic fallback
        system_prompt = (
            "You are Victoria Vance, Planning Specialist at Auctor Systems. "
            "Analyze the website directive and produce a concise JSON plan with: "
            "project_name, project_description, pages, key_features, milestones."
        )

        def fallback_plan():
            words = [w.capitalize() for w in context.user_prompt.split() if len(w) > 3][:3]
            base_name = " ".join(words) if words else "Modern Studio"
            return f"""# Project Plan: {base_name}
Target Audience: Discerning clients seeking premium digital experiences.
Core Sections:
1. Navigation & Hero Showcase
2. Interactive Features & Offerings
3. Philosophical Manifesto / About Us
4. Contact & Inquiries Modal

Milestones:
- M1: Planning & Scope (Victoria)
- M2: Requirements & Specifications (Beatrice)
- M3: Palette 4 Visual Design System (Clara)
- M4: Modular Frontend Development (Maya)
- M5: QA & WCAG Audit (Astrid)
- M6: Architecture & User Guide (Genevieve)
- M7: Production Deployment Manifest (Nadia)
- M8: Launch Marketing & SEO (Sophia)
"""

        plan_text = await llm_service.generate_text(
            system_instruction=system_prompt,
            user_prompt=f"Directive: {context.user_prompt}",
            fallback_generator=fallback_plan,
            mode=context.execution_mode,
        )

        # Derive project name
        lines = [line.strip() for line in plan_text.splitlines() if line.strip()]
        proj_name = "Auctor Project"
        for l in lines:
            if l.startswith("# Project Plan:") or l.startswith("Project Plan:"):
                proj_name = l.split(":", 1)[1].strip()
                break
            elif "project_name" in l.lower():
                cleaned = l.split(":", 1)[-1].strip().strip('"').strip(",")
                if cleaned:
                    proj_name = cleaned
                    break

        context.project_name = proj_name
        context.project_description = f"Engineered website based on: {context.user_prompt}"
        context.plan = {
            "title": proj_name,
            "raw_plan": plan_text,
            "milestones": 8,
            "target_audience": "Discerning clients seeking bespoke digital experiences",
            "sections": [
                {"id": "hero", "name": "Hero Section & Value Proposition"},
                {"id": "features", "name": "Interactive Offerings & Case Studies"},
                {"id": "manifesto", "name": "Studio Manifesto & Craftsmanship Principles"},
                {"id": "contactModal", "name": "Interactive Inquiries & Consultation Modal"},
            ],
            "features": [
                "Dynamic Category Filtering (All, Core Architecture, Design Tokens, Performance)",
                "Live Keyword Filter with Real-Time Counter",
                "Accessible Inquiries Modal with Live Form Validation & Feedback Toast",
                "Palette 4 Editorial Styling with Responsive Grid",
            ],
        }
        context.agent_outputs[self.backend_name] = plan_text

        await self.emit_message(
            context,
            emit,
            f"Project blueprint finalized: '{proj_name}'. 8-stage sequence established.",
        )
        await asyncio.sleep(0.3)

        await self.emit_completed(
            context,
            emit,
            message="Strategic scope and architectural milestones approved.",
            data={"project_name": proj_name},
        )
        await asyncio.sleep(0.2)

        await self.emit_handoff(
            context,
            emit,
            to_agent_id="beatrice",
            to_agent_name="Beatrice Stone",
            message="Project scope and milestone plan completed.",
        )
