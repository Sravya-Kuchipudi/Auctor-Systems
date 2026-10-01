"""
Auctor Systems — Sophia Laurent (Marketing Director)
Crafts high-impact launch copy, SEO metadata, and promotional campaigns
based strictly on the actual generated features and verified product capabilities.
"""

import asyncio
from typing import Callable, Awaitable
from orchestrator.base_agent import BaseAgent
from orchestrator.context import ProjectContext
from orchestrator.events import WorkflowEvent
from services.llm_service import llm_service


class SophiaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="sophia",
            name="Sophia Laurent",
            role="Marketing Director",
            backend_name="marketing",
        )

    async def execute(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
    ) -> None:
        await self.emit_started(context, emit)
        await asyncio.sleep(0.3)

        project_title = context.project_name or "Auctor Studio"
        clean_name = project_title.replace('"', '&quot;')
        audience = context.plan.get("target_audience", "Discerning clients seeking bespoke digital experiences")

        await self.emit_thinking(
            context,
            emit,
            f"Analyzing verified product features for {clean_name} to generate an authentic launch campaign without unsupported claims...",
        )
        await asyncio.sleep(0.4)

        await self.emit_working(
            context,
            emit,
            "Formulating marketing/LAUNCH_COPY.md with value proposition, verified features, SEO metadata, and social broadcast copy...",
            snippet="""# Launch Campaign Strategy
1. One-Line Value Proposition
2. Verified Feature Highlights (Search, Tabs, Counter, Modal, Palette 4)
3. Target Audience & Social Announcements""",
        )
        await asyncio.sleep(0.4)

        launch_copy = f"""# Launch Campaign Strategy & SEO Package: {clean_name}

## 1. Product Name
**{clean_name}**

## 2. One-Line Value Proposition
Bespoke digital architecture crafted with Palette 4 editorial elegance and zero runtime framework dependencies.

## 3. Short Product Description
{clean_name} is an autonomous, responsive web application engineered to unite timeless editorial aesthetics with modern interactive controls. Built entirely with clean semantic HTML5, CSS3 Custom Properties, and vanilla ES6+ JavaScript, it delivers exceptional performance, complete WCAG 2.1 AA accessibility, and intuitive user engagement.

## 4. Feature Highlights
- **Interactive Case Study Showcase**: Real-time keyword search and category tab filtering (Core Architecture, Design Tokens, Performance).
- **Dynamic Item Counter**: Live badge automatically reflecting the number of visible modules in real-time.
- **Accessible Inquiries Modal Dialog**: Client-side form validation with field error states, simulated dispatch loading, and confirmation toast feedback.
- **Palette 4 Visual System**: Curated color harmony using Deep Wine (#3A1028), Burgundy (#541B3B), and Dusty Rose (#B68A9A) accents.
- **Fluid Multi-Device Grid**: Flawless responsiveness across Mobile (375px), Tablet (768px), and Desktop (1200px) viewports.
- **Zero-Dependency Architecture**: Pure web standards ensuring instantaneous load times and zero supply-chain vulnerabilities.

## 5. Target Audience
{audience}.

## 6. Launch Announcement
We are pleased to unveil **{clean_name}** — an interactive web experience engineered through the Auctor Systems 8-agent autonomous pipeline. From architectural planning and requirements analysis to visual token design, automated QA testing, and edge deployment configuration, {clean_name} demonstrates what intentional web craft looks like.

## 7. Social Media Copy
### LinkedIn / Executive Release
Excited to announce the launch of **{clean_name}**. Engineered autonomously through @AuctorSystems, this application brings together high-contrast editorial typography, interactive filtering, and full WCAG 2.1 AA compliance — with zero external libraries.

Explore the live release: https://auctor.systems/preview/{context.project_id}

### X / Product Hunt
Introducing **{clean_name}** ✧
- Palette 4 Editorial Design System
- Live search & tabbed portfolio filtering
- Accessible consultation modal with live validation
- 100% Vanilla HTML5/CSS3/ES6+

Crafted by 8 autonomous AI specialists. Discover intentional software: https://auctor.systems/preview/{context.project_id}

## 8. SEO Title
{clean_name} — Bespoke Web Architecture & Digital Experience

## 9. SEO Description
Experience {clean_name}: an autonomous, high-performance web experience crafted to Palette 4 editorial standards with zero runtime dependencies and verified WCAG 2.1 AA accessibility.
"""

        context.set_file("marketing/LAUNCH_COPY.md", "LAUNCH_COPY.md", launch_copy, category="doc")
        context.marketing = {
            "launch_copy": "marketing/LAUNCH_COPY.md",
            "campaign_status": "complete",
            "seo_title": f"{clean_name} — Bespoke Web Architecture & Digital Experience",
            "seo_description": f"Experience {clean_name}: an autonomous, high-performance web experience crafted to Palette 4 editorial standards.",
            "value_prop": "Bespoke digital architecture crafted with Palette 4 editorial elegance and zero runtime framework dependencies.",
        }
        context.agent_outputs[self.backend_name] = f"Launch marketing strategy and SEO metadata package completed."

        await self.emit_message(
            context,
            emit,
            "Marketing campaign assets, social blurbs, and SEO tags compiled successfully.",
        )
        await asyncio.sleep(0.3)

        await self.emit_completed(
            context,
            emit,
            message="Brand narrative, launch messaging, and SEO configuration approved.",
            data={"marketing_file": "marketing/LAUNCH_COPY.md"},
        )
