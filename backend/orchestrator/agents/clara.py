"""
Auctor Systems — Clara Delacroix (Design Director)
Produces Palette 4 design token sheets, typography hierarchy, and UI component specifications.
"""

import asyncio
from typing import Callable, Awaitable
from orchestrator.base_agent import BaseAgent
from orchestrator.context import ProjectContext
from orchestrator.events import WorkflowEvent
from services.llm_service import llm_service


class ClaraAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="clara",
            name="Clara Delacroix",
            role="Design Director",
            backend_name="design",
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
            "Synthesizing Palette 4 color tokens, typographic hierarchy, and responsive layout grids.",
        )
        await asyncio.sleep(0.4)

        await self.emit_working(
            context,
            emit,
            "Calibrating Palette 4 contrast ratios: Deep Wine (#3A1028), Burgundy (#541B3B), Dusty Rose (#B68A9A)...",
            snippet="""--deep-wine: #3A1028;
--burgundy: #541B3B;
--midnight-navy: #20243A;
--dusty-rose: #B68A9A;
--pearl: #F5F4F5;
--white: #FFFFFF;
--cool-gray: #6B6C78;
--text-primary: #29232B;
--muted-sage: #718276;
--muted-gold: #C79A4A;""",
        )
        await asyncio.sleep(0.4)

        # Design System Specification
        system_prompt = (
            "You are Clara Delacroix, Design Director at Auctor Systems. "
            "Formulate the visual design system ensuring strict adherence to Palette 4. "
            "Detail typography (Fraunces / Inter), glassmorphic card styles, spacing scale, "
            "and component rules for hero, tabbed portfolio, and interactive dialog."
        )

        def fallback_design():
            return """# Design System Specification: Palette 4 (Editorial Heritage)

## Color Tokens
```css
:root {
  --deep-wine: #3A1028;
  --burgundy: #541B3B;
  --midnight-navy: #20243A;
  --dusty-rose: #B68A9A;
  --pearl: #F5F4F5;
  --white: #FFFFFF;
  --cool-gray: #6B6C78;
  --text-primary: #29232B;
  --muted-sage: #718276;
  --muted-gold: #C79A4A;
  --error: #B85C5C;
  
  --bg-main: var(--pearl);
  --surface-card: var(--white);
  --border-subtle: rgba(58, 16, 40, 0.08);
  --shadow-sm: 0 2px 8px rgba(32, 36, 58, 0.05);
  --shadow-md: 0 8px 24px rgba(32, 36, 58, 0.08);
  --shadow-lg: 0 16px 40px rgba(58, 16, 40, 0.12);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
}
```

## Typography
- Headings: 'Fraunces', Georgia, serif (Weight: 600, 700)
- Body & Interface: 'Plus Jakarta Sans', -apple-system, sans-serif
- Code & Meta: 'JetBrains Mono', monospace

## Responsive Layout Grid
- Mobile: 1-column fluid, min-width 320px, 16px margins
- Tablet: 2-column auto-fit, min-width 768px, 24px margins
- Desktop: 12-column dynamic grid, max-width 1240px, 32px margins
"""

        design_text = await llm_service.generate_text(
            system_instruction=system_prompt,
            user_prompt=f"Requirements: {context.requirements}\nPlan: {context.plan}",
            fallback_generator=fallback_design,
            mode=context.execution_mode,
        )

        context.design_system = {
            "tokens": {
                "deep_wine": "#3A1028",
                "burgundy": "#541B3B",
                "midnight_navy": "#20243A",
                "dusty_rose": "#B68A9A",
                "pearl": "#F5F4F5",
                "white": "#FFFFFF",
                "cool_gray": "#6B6C78",
                "text_primary": "#29232B",
                "muted_sage": "#718276",
                "muted_gold": "#C79A4A",
            },
            "specification": design_text,
        }
        context.agent_outputs[self.backend_name] = design_text

        await self.emit_message(
            context,
            emit,
            "Design system complete with Palette 4 variables, responsive grid, and fluid typography.",
        )
        await asyncio.sleep(0.3)

        await self.emit_completed(
            context,
            emit,
            message="Visual tokens and responsive component specifications delivered.",
        )
        await asyncio.sleep(0.2)

        await self.emit_handoff(
            context,
            emit,
            to_agent_id="maya",
            to_agent_name="Maya Thorne",
            message="Design system and responsive layout specification ready.",
        )
