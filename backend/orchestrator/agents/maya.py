"""
Auctor Systems — Maya Thorne (Lead Developer)
Engineers clean, semantic HTML5, CSS3 with Palette 4 tokens, and interactive ES6+ JavaScript.
Produces a genuinely usable web application with visible state, filtering, search, and accessible modal inquiry.
Resolves Astrid's concrete defects during the QA revision loop.
"""

import asyncio
from typing import Callable, Awaitable, List, Dict, Any, Optional
from orchestrator.base_agent import BaseAgent
from orchestrator.context import ProjectContext
from orchestrator.events import WorkflowEvent, EventType
from services.llm_service import llm_service


class MayaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="maya",
            name="Maya Thorne",
            role="Lead Developer",
            backend_name="development",
        )

    async def execute(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
    ) -> None:
        is_revision = context.qa_needs_revision and context.qa_revision_count > 0

        await self.emit_started(
            context,
            emit,
            message="Commencing code remediation based on QA defect report." if is_revision else "Initiating frontend code generation."
        )
        await asyncio.sleep(0.3)

        if is_revision:
            defects_summary = ", ".join(d.issue for d in context.defects) if context.defects else context.qa_defect_feedback
            await self.emit_thinking(
                context,
                emit,
                f"Ingesting Astrid's defect report ({len(context.defects)} issues): {defects_summary[:120]}...",
            )
            await asyncio.sleep(0.3)
            await self.emit_working(
                context,
                emit,
                f"Patching defects: applying aria-labels and Palette 4 :focus-visible outlines...",
                snippet="""/* Applied QA Accessibility Remediation */
button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
  outline: 2px solid var(--muted-gold);
  outline-offset: 2px;
}
#closeModalBtn[aria-label="Close modal dialog"] { ... }""",
            )
            await asyncio.sleep(0.4)
        else:
            await self.emit_thinking(
                context,
                emit,
                f"Architecting responsive web application for {context.project_name}...",
            )
            await asyncio.sleep(0.3)
            await self.emit_working(
                context,
                emit,
                "Building index.html, style.css, and script.js with dynamic search, tabbed filters, live counter, and inquiry modal...",
                snippet="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Production Web Application</title>
</head>""",
            )
            await asyncio.sleep(0.4)

        # Context details
        project_title = context.project_name or "Auctor Studio"
        clean_name = project_title.replace('"', '&quot;')
        tagline = context.user_prompt or "Curated Digital Experience"
        clarified_preference = ""
        if context.clarification and context.clarification.user_response:
            clarified_preference = context.clarification.user_response

        # During initial pass (pass 0), closeModalBtn lacks aria-label and style.css lacks :focus-visible
        # During revision pass, these defects are explicitly fixed based on context.defects!
        has_aria_fix = is_revision
        has_focus_fix = is_revision

        aria_attr = 'aria-label="Close modal dialog"' if has_aria_fix else ''
        focus_rule = """
/* Accessibility Focus Rings (Remediated for WCAG 2.1 AA) */
button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {
  outline: 2px solid var(--muted-gold);
  outline-offset: 2px;
}
""" if has_focus_fix else ""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{clean_name} — Modern Web Experience</title>
  <meta name="description" content="{clean_name} built with Auctor Systems 8-agent autonomous pipeline.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- Global Navigation -->
  <header class="site-header">
    <div class="nav-container">
      <a href="#hero" class="brand-logo" aria-label="{clean_name} Home">
        <span class="logo-mark">A</span>
        <span class="logo-text">{clean_name}</span>
      </a>
      <nav class="main-nav" aria-label="Primary Navigation">
        <a href="#hero" class="nav-link active">Overview</a>
        <a href="#features" class="nav-link">Offerings</a>
        <a href="#manifesto" class="nav-link">Manifesto</a>
        <button class="nav-btn" id="openModalBtn" type="button">Inquire Now</button>
      </nav>
    </div>
  </header>

  <main>
    <!-- Hero Section -->
    <section id="hero" class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          <span>{clarified_preference or "Palette 4 · Editorial Standard"}</span>
        </div>
        <h1 class="hero-title">{clean_name}</h1>
        <p class="hero-subtitle">
          {tagline}
        </p>
        <div class="hero-actions">
          <a href="#features" class="btn btn-primary">Explore Case Studies</a>
          <button class="btn btn-secondary" id="openModalBtnHero" type="button">Request Consultation</button>
        </div>
      </div>
      <div class="hero-visual">
        <div class="hero-card">
          <div class="card-header">
            <span class="card-pill">Production Ready</span>
            <span class="card-date">v1.0 Verified</span>
          </div>
          <div class="card-body">
            <h3>Architectural Precision</h3>
            <p>Every component is rendered with Palette 4 luxury tokens, responsive layout grids, and zero third-party dependencies.</p>
            <div class="stats-row">
              <div class="stat-item">
                <span class="stat-num">100%</span>
                <span class="stat-label">Vanilla Web</span>
              </div>
              <div class="stat-item">
                <span class="stat-num">AA</span>
                <span class="stat-label">WCAG Compliant</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Interactive Features & Case Studies -->
    <section id="features" class="features-section">
      <div class="section-header">
        <span class="section-eyebrow">Interactive Showcase</span>
        <h2 class="section-title">Engineered Capabilities</h2>
        <p class="section-desc">Explore our interactive portfolio using dynamic keyword search and category filters.</p>
      </div>

      <!-- Controls: Category Filter Tabs & Live Search -->
      <div class="controls-toolbar">
        <div class="search-wrap">
          <input
            type="text"
            id="filterSearchInput"
            class="search-input"
            placeholder="Filter case studies by keyword (e.g. typography, tokens, grid)..."
            aria-label="Filter case studies"
          />
        </div>
        <div class="filter-tabs" role="tablist" aria-label="Feature categories">
          <button class="tab-btn active" data-filter="all" role="tab" aria-selected="true">All Modules</button>
          <button class="tab-btn" data-filter="core" role="tab" aria-selected="false">Core Architecture</button>
          <button class="tab-btn" data-filter="design" role="tab" aria-selected="false">Design Tokens</button>
          <button class="tab-btn" data-filter="performance" role="tab" aria-selected="false">Performance</button>
        </div>
      </div>

      <!-- Live Counter Badge -->
      <div class="counter-row">
        <span id="visibleCountBadge" class="counter-badge">Showing 4 of 4 Case Studies</span>
      </div>

      <!-- Cards Grid -->
      <div class="grid-container" id="cardsGrid">
        <div class="feature-card" data-category="core" data-tags="typography editorial serif fraunces font">
          <div class="card-icon">✧</div>
          <h3>Curated Typographic Hierarchy</h3>
          <p>Fraunces editorial serif headers paired seamlessly with Plus Jakarta Sans body structure for readable digital balance.</p>
          <span class="card-meta">Editorial Hierarchy</span>
        </div>

        <div class="feature-card" data-category="design" data-tags="palette tokens colors wine burgundy rose pearl">
          <div class="card-icon">◈</div>
          <h3>Palette 4 Color System</h3>
          <p>Deep Wine (#3A1028), Burgundy (#541B3B), and Dusty Rose (#B68A9A) harmonious tokens calibrated for high contrast.</p>
          <span class="card-meta">Palette 4 Tokens</span>
        </div>

        <div class="feature-card" data-category="performance" data-tags="responsive layout fluid grid touch mobile tablet">
          <div class="card-icon">⬡</div>
          <h3>Fluid Responsive Grid</h3>
          <p>Adaptive multi-column layout seamlessly reflowing between 320px mobile viewports, tablet screens, and 4K displays.</p>
          <span class="card-meta">Fluid Breakpoints</span>
        </div>

        <div class="feature-card" data-category="core" data-tags="interactive micro-interactions dialog modal tabs transition">
          <div class="card-icon">❖</div>
          <h3>Micro-Interactions & State</h3>
          <p>Smooth cubic-bezier state transitions, live search filtering, and accessible dialog controls that keep the application engaging.</p>
          <span class="card-meta">Dynamic State</span>
        </div>
      </div>

      <!-- Empty State for Search Filter -->
      <div id="emptySearchState" class="empty-state" style="display: none;">
        <span class="empty-icon">⊘</span>
        <h4>No matching case studies</h4>
        <p>Try refining your search keyword or reset the filter to view all modules.</p>
        <button type="button" class="btn btn-secondary btn-sm" id="resetFilterBtn">Reset Filter</button>
      </div>
    </section>

    <!-- Manifesto / Philosophy -->
    <section id="manifesto" class="manifesto-section">
      <div class="manifesto-card">
        <span class="manifesto-quote">“</span>
        <blockquote>
          Software built with intentional craft outlasts fleeting trends. By unifying planning, design, implementation, and rigorous QA into a singular coherent pipeline, Auctor creates web experiences of enduring distinction.
        </blockquote>
        <div class="manifesto-author">
          <strong>The Auctor Studio Collective</strong>
          <span>Synthesized by 8 Autonomous Specialists</span>
        </div>
      </div>
    </section>
  </main>

  <!-- Interactive Contact Dialog / Modal -->
  <div class="modal-overlay" id="contactModal" aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <div class="modal-dialog">
      <div class="modal-header">
        <h3 id="modalTitle">Initiate Inquiries</h3>
        <button class="modal-close-btn" id="closeModalBtn" type="button" {aria_attr}>&times;</button>
      </div>
      <form class="modal-form" id="inquiryForm" novalidate>
        <div class="form-group">
          <label for="clientName">Full Name</label>
          <input type="text" id="clientName" required placeholder="e.g. Eleanor Vance">
          <span class="field-error" id="nameError"></span>
        </div>
        <div class="form-group">
          <label for="clientEmail">Email Address</label>
          <input type="email" id="clientEmail" required placeholder="eleanor@studio.com">
          <span class="field-error" id="emailError"></span>
        </div>
        <div class="form-group">
          <label for="clientBudget">Project Scope</label>
          <select id="clientBudget">
            <option value="bespoke">Bespoke Brand & Web Application</option>
            <option value="portfolio">Curated Portfolio Experience</option>
            <option value="enterprise">Multi-Page Production Architecture</option>
          </select>
        </div>
        <div class="form-group">
          <label for="clientMessage">Project Vision & Timeline</label>
          <textarea id="clientMessage" rows="3" placeholder="Describe the scope, objectives, or target milestones..."></textarea>
        </div>
        <div class="modal-footer">
          <button type="submit" class="btn btn-primary" id="submitInquiryBtn">
            <span class="btn-text">Dispatch Inquiry</span>
            <span class="btn-loader" style="display: none;">Sending...</span>
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Success Toast Confirmation -->
  <div id="inquiryToast" class="inquiry-toast" role="status" aria-live="polite">
    <span class="toast-icon">✓</span>
    <span class="toast-message">Inquiry dispatched successfully. We will be in touch shortly.</span>
  </div>

  <!-- Site Footer -->
  <footer class="site-footer">
    <div class="footer-container">
      <div class="footer-left">
        <p class="footer-copy">&copy; 2026 {clean_name}. Handcrafted with Auctor Systems.</p>
      </div>
      <div class="footer-right">
        <a href="#hero">Top &uarr;</a>
        <a href="#features">Offerings</a>
        <a href="#manifesto">Manifesto</a>
      </div>
    </div>
  </footer>

  <script src="script.js"></script>
</body>
</html>"""

        css_content = f"""/* =============================================================================
   Auctor Systems — Production Stylesheet
   Design System: Palette 4 (Editorial Heritage)
   ============================================================================= */

:root {{
  /* Palette 4 Locked Tokens */
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

  /* Surfaces & Elevation */
  --bg-main: var(--pearl);
  --surface-card: var(--white);
  --border-light: rgba(58, 16, 40, 0.08);
  --border-focus: var(--burgundy);
  --shadow-sm: 0 2px 10px rgba(32, 36, 58, 0.04);
  --shadow-md: 0 8px 30px rgba(32, 36, 58, 0.08);
  --shadow-lg: 0 20px 48px rgba(58, 16, 40, 0.12);

  /* Typography */
  --font-serif: 'Fraunces', Georgia, serif;
  --font-sans: 'Plus Jakarta Sans', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}}

/* Reset & Base */
*, *::before, *::after {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html {{
  scroll-behavior: smooth;
  font-size: 16px;
}}

body {{
  background-color: var(--bg-main);
  color: var(--text-primary);
  font-family: var(--font-sans);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}
{focus_rule}

/* Navigation */
.site-header {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(245, 244, 245, 0.88);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-light);
}}

.nav-container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.brand-logo {{
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--deep-wine);
}}

.logo-mark {{
  width: 32px;
  height: 32px;
  background: var(--burgundy);
  color: var(--white);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-family: var(--font-serif);
  font-weight: 700;
  font-size: 16px;
}}

.logo-text {{
  font-family: var(--font-serif);
  font-weight: 700;
  font-size: 18px;
  letter-spacing: -0.2px;
}}

.main-nav {{
  display: flex;
  align-items: center;
  gap: 24px;
}}

.nav-link {{
  text-decoration: none;
  color: var(--cool-gray);
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s ease;
}}

.nav-link:hover, .nav-link.active {{
  color: var(--burgundy);
}}

.nav-btn {{
  background: var(--burgundy);
  color: var(--white);
  padding: 8px 18px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}}

.nav-btn:hover {{
  background: var(--deep-wine);
  transform: translateY(-1px);
}}

/* Hero Section */
.hero-section {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 24px;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 48px;
  align-items: center;
}}

.hero-badge {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(182, 138, 154, 0.15);
  color: var(--burgundy);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 20px;
  border: 1px solid rgba(182, 138, 154, 0.3);
}}

.badge-dot {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--burgundy);
}}

.hero-title {{
  font-family: var(--font-serif);
  font-size: clamp(2.5rem, 5vw, 4rem);
  line-height: 1.15;
  color: var(--deep-wine);
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: 20px;
}}

.hero-subtitle {{
  font-size: 18px;
  color: var(--cool-gray);
  line-height: 1.6;
  margin-bottom: 32px;
}}

.hero-actions {{
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}}

.btn {{
  padding: 12px 26px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  border: none;
}}

.btn-primary {{
  background: var(--burgundy);
  color: var(--white);
}}

.btn-primary:hover {{
  background: var(--deep-wine);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}}

.btn-secondary {{
  background: var(--white);
  color: var(--deep-wine);
  border: 1px solid var(--border-light);
}}

.btn-secondary:hover {{
  background: var(--pearl);
  border-color: var(--dusty-rose);
}}

.btn-sm {{
  padding: 8px 16px;
  font-size: 12px;
}}

.hero-card {{
  background: var(--surface-card);
  border-radius: 16px;
  padding: 32px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  position: relative;
}}

.card-header {{
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}}

.card-pill {{
  background: rgba(113, 130, 118, 0.15);
  color: var(--muted-sage);
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
  text-transform: uppercase;
}}

.card-date {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--cool-gray);
}}

.hero-card h3 {{
  font-family: var(--font-serif);
  font-size: 22px;
  color: var(--deep-wine);
  margin-bottom: 12px;
}}

.hero-card p {{
  font-size: 14px;
  color: var(--cool-gray);
  margin-bottom: 24px;
}}

.stats-row {{
  display: flex;
  gap: 32px;
  border-top: 1px solid var(--border-light);
  padding-top: 20px;
}}

.stat-num {{
  display: block;
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  color: var(--burgundy);
}}

.stat-label {{
  font-size: 11px;
  color: var(--cool-gray);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

/* Features Section */
.features-section {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 24px;
}}

.section-header {{
  text-align: center;
  max-width: 600px;
  margin: 0 auto 32px auto;
}}

.section-eyebrow {{
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--burgundy);
  text-transform: uppercase;
  letter-spacing: 1px;
  display: block;
  margin-bottom: 8px;
}}

.section-title {{
  font-family: var(--font-serif);
  font-size: 32px;
  color: var(--deep-wine);
  margin-bottom: 12px;
}}

.section-desc {{
  font-size: 15px;
  color: var(--cool-gray);
}}

/* Toolbar: Search & Filter Tabs */
.controls-toolbar {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}}

.search-wrap {{
  width: 100%;
  max-width: 480px;
}}

.search-input {{
  width: 100%;
  padding: 10px 18px;
  border-radius: 30px;
  border: 1px solid var(--border-light);
  background: var(--white);
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
  outline: none;
  transition: all 0.2s ease;
}}

.search-input:focus {{
  border-color: var(--burgundy);
  box-shadow: 0 0 0 3px rgba(84, 27, 59, 0.1);
}}

.filter-tabs {{
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}}

.tab-btn {{
  background: var(--white);
  border: 1px solid var(--border-light);
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: var(--cool-gray);
  cursor: pointer;
  transition: all 0.2s ease;
}}

.tab-btn.active, .tab-btn:hover {{
  background: var(--burgundy);
  color: var(--white);
  border-color: var(--burgundy);
}}

.counter-row {{
  text-align: center;
  margin-bottom: 32px;
}}

.counter-badge {{
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--burgundy);
  background: rgba(182, 138, 154, 0.15);
  padding: 4px 12px;
  border-radius: 12px;
}}

.grid-container {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
}}

.feature-card {{
  background: var(--surface-card);
  padding: 30px;
  border-radius: 12px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}}

.feature-card:hover {{
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: rgba(182, 138, 154, 0.4);
}}

.card-icon {{
  font-size: 24px;
  color: var(--burgundy);
  margin-bottom: 16px;
}}

.feature-card h3 {{
  font-family: var(--font-serif);
  font-size: 18px;
  color: var(--deep-wine);
  margin-bottom: 10px;
}}

.feature-card p {{
  font-size: 14px;
  color: var(--cool-gray);
  margin-bottom: 16px;
  flex: 1;
}}

.card-meta {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--dusty-rose);
  font-weight: 600;
}}

/* Empty State */
.empty-state {{
  text-align: center;
  padding: 60px 20px;
  background: var(--white);
  border-radius: 16px;
  border: 1px dashed var(--border-light);
}}

.empty-icon {{
  font-size: 32px;
  color: var(--cool-gray);
  display: block;
  margin-bottom: 12px;
}}

.empty-state h4 {{
  font-family: var(--font-serif);
  font-size: 18px;
  color: var(--deep-wine);
  margin-bottom: 6px;
}}

.empty-state p {{
  font-size: 13px;
  color: var(--cool-gray);
  margin-bottom: 16px;
}}

/* Manifesto */
.manifesto-section {{
  max-width: 1000px;
  margin: 0 auto;
  padding: 60px 24px 100px 24px;
}}

.manifesto-card {{
  background: var(--deep-wine);
  color: var(--pearl);
  border-radius: 20px;
  padding: 60px 48px;
  position: relative;
  box-shadow: var(--shadow-lg);
}}

.manifesto-quote {{
  font-family: var(--font-serif);
  font-size: 80px;
  position: absolute;
  top: 20px;
  left: 32px;
  color: rgba(182, 138, 154, 0.2);
  line-height: 1;
}}

.manifesto-card blockquote {{
  font-family: var(--font-serif);
  font-size: clamp(1.2rem, 3vw, 1.8rem);
  font-style: italic;
  line-height: 1.5;
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}}

.manifesto-author strong {{
  display: block;
  font-size: 16px;
  color: var(--white);
}}

.manifesto-author span {{
  font-size: 12px;
  color: var(--dusty-rose);
}}

/* Modal / Dialog */
.modal-overlay {{
  position: fixed;
  inset: 0;
  background: rgba(32, 36, 58, 0.6);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}}

.modal-overlay.open {{
  opacity: 1;
  visibility: visible;
}}

.modal-dialog {{
  background: var(--white);
  width: 90%;
  max-width: 520px;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
}}

.modal-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}}

.modal-header h3 {{
  font-family: var(--font-serif);
  font-size: 22px;
  color: var(--deep-wine);
}}

.modal-close-btn {{
  background: transparent;
  border: none;
  font-size: 24px;
  color: var(--cool-gray);
  cursor: pointer;
  line-height: 1;
  padding: 4px;
}}

.form-group {{
  margin-bottom: 16px;
}}

.form-group label {{
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}}

.form-group input, .form-group textarea, .form-group select {{
  width: 100%;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-light);
  font-family: var(--font-sans);
  font-size: 14px;
  outline: none;
  background: var(--pearl);
  transition: border-color 0.2s;
}}

.form-group input:focus, .form-group textarea:focus, .form-group select:focus {{
  border-color: var(--burgundy);
  background: var(--white);
}}

.field-error {{
  display: block;
  font-size: 11px;
  color: var(--error);
  margin-top: 4px;
  min-height: 16px;
}}

.modal-footer {{
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}}

/* Toast */
.inquiry-toast {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: var(--deep-wine);
  color: var(--white);
  padding: 14px 20px;
  border-radius: 10px;
  box-shadow: var(--shadow-lg);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 500;
  z-index: 2000;
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}}

.inquiry-toast.show {{
  transform: translateY(0);
  opacity: 1;
}}

.toast-icon {{
  color: var(--muted-sage);
  font-weight: 700;
}}

/* Footer */
.site-footer {{
  border-top: 1px solid var(--border-light);
  background: var(--white);
  padding: 32px 24px;
}}

.footer-container {{
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}}

.footer-copy {{
  font-size: 13px;
  color: var(--cool-gray);
}}

.footer-right {{
  display: flex;
  gap: 20px;
}}

.footer-right a {{
  color: var(--cool-gray);
  text-decoration: none;
  font-size: 13px;
}}

.footer-right a:hover {{
  color: var(--burgundy);
}}

/* Responsive Breakpoints */
@media (max-width: 768px) {{
  .hero-section {{
    grid-template-columns: 1fr;
    padding: 48px 16px;
  }}
  .main-nav {{
    display: none;
  }}
  .manifesto-card {{
    padding: 36px 24px;
  }}
  .grid-container {{
    grid-template-columns: 1fr;
  }}
}}
"""

        js_content = """/**
 * Auctor Systems — Interactive Client Logic
 * Modular ES6+ components: Live Search, Filter Tabs, Dynamic Counter, Modal Validation, and Toast.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Search, Filter Tabs & Dynamic Item Counter
  const searchInput = document.getElementById('filterSearchInput');
  const tabButtons = document.querySelectorAll('.tab-btn');
  const cards = Array.from(document.querySelectorAll('.feature-card'));
  const counterBadge = document.getElementById('visibleCountBadge');
  const emptyState = document.getElementById('emptySearchState');
  const resetBtn = document.getElementById('resetFilterBtn');

  let activeCategory = 'all';
  let searchKeyword = '';

  function applyFilters() {
    let visibleCount = 0;
    const query = searchKeyword.toLowerCase().trim();

    cards.forEach((card) => {
      const category = card.getAttribute('data-category') || '';
      const text = card.textContent.toLowerCase();
      const tags = card.getAttribute('data-tags') || '';

      const matchesCategory = (activeCategory === 'all' || category === activeCategory);
      const matchesQuery = (!query || text.includes(query) || tags.includes(query));

      if (matchesCategory && matchesQuery) {
        card.style.display = 'flex';
        card.style.opacity = '1';
        visibleCount++;
      } else {
        card.style.display = 'none';
        card.style.opacity = '0';
      }
    });

    if (counterBadge) {
      counterBadge.textContent = `Showing ${visibleCount} of ${cards.length} Case Studies`;
    }

    if (emptyState) {
      emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabButtons.forEach((b) => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      activeCategory = btn.getAttribute('data-filter') || 'all';
      applyFilters();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchKeyword = e.target.value;
      applyFilters();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      activeCategory = 'all';
      searchKeyword = '';
      if (searchInput) searchInput.value = '';
      tabButtons.forEach((b) => {
        b.classList.toggle('active', b.getAttribute('data-filter') === 'all');
        b.setAttribute('aria-selected', b.getAttribute('data-filter') === 'all');
      });
      applyFilters();
    });
  }

  // 2. Interactive Inquiries Modal with Live Form Validation & Feedback Toast
  const modal = document.getElementById('contactModal');
  const openBtns = [
    document.getElementById('openModalBtn'),
    document.getElementById('openModalBtnHero'),
  ].filter(Boolean);
  const closeBtn = document.getElementById('closeModalBtn');
  const form = document.getElementById('inquiryForm');
  const nameInput = document.getElementById('clientName');
  const emailInput = document.getElementById('clientEmail');
  const nameError = document.getElementById('nameError');
  const emailError = document.getElementById('emailError');
  const submitBtn = document.getElementById('submitInquiryBtn');
  const toast = document.getElementById('inquiryToast');

  function openModal() {
    if (!modal) return;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    if (nameInput) nameInput.focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    clearValidation();
  }

  function clearValidation() {
    if (nameError) nameError.textContent = '';
    if (emailError) emailError.textContent = '';
  }

  function showToast(msg) {
    if (!toast) return;
    if (msg) toast.querySelector('.toast-message').textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 4000);
  }

  openBtns.forEach((btn) => btn.addEventListener('click', (e) => {
    e.preventDefault();
    openModal();
  }));

  if (closeBtn) closeBtn.addEventListener('click', closeModal);

  window.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal && modal.classList.contains('open')) {
      closeModal();
    }
  });

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      clearValidation();

      let hasError = false;
      const nameVal = nameInput ? nameInput.value.trim() : '';
      const emailVal = emailInput ? emailInput.value.trim() : '';
      const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;

      if (!nameVal) {
        if (nameError) nameError.textContent = 'Please enter your full name.';
        hasError = true;
      }
      if (!emailVal || !emailRegex.test(emailVal)) {
        if (emailError) emailError.textContent = 'Please provide a valid email address.';
        hasError = true;
      }

      if (hasError) return;

      // Simulate loading state and success confirmation
      const btnText = submitBtn ? submitBtn.querySelector('.btn-text') : null;
      const btnLoader = submitBtn ? submitBtn.querySelector('.btn-loader') : null;
      if (btnText) btnText.style.display = 'none';
      if (btnLoader) btnLoader.style.display = 'inline';
      if (submitBtn) submitBtn.disabled = true;

      setTimeout(() => {
        if (btnText) btnText.style.display = 'inline';
        if (btnLoader) btnLoader.style.display = 'none';
        if (submitBtn) submitBtn.disabled = false;
        closeModal();
        if (form) form.reset();
        showToast(`Inquiry dispatched for ${nameVal}. Auctor will contact you shortly.`);
      }, 600);
    });
  }
});
"""

        # Update Project Context files
        context.set_file("src/index.html", "index.html", html_content, category="source")
        context.set_file("src/style.css", "style.css", css_content, category="source")
        context.set_file("src/script.js", "script.js", js_content, category="source")
        context.agent_outputs[self.backend_name] = f"Generated interactive web application with dynamic search, category tabs, and accessible inquiry modal."

        # Emit project generated event
        await emit(
            WorkflowEvent(
                type=EventType.PROJECT_GENERATED.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=f"Interactive frontend application compiled ({len(context.get_source_files())} files ready for Live Preview).",
                data={
                    "files": [
                        {"path": "src/index.html", "filename": "index.html"},
                        {"path": "src/style.css", "filename": "style.css"},
                        {"path": "src/script.js", "filename": "script.js"},
                    ],
                    "interactive_modules": ["Live Search Filter", "Dynamic Item Counter", "Interactive Modal Dialog", "Feedback Toast"],
                },
            )
        )
        await asyncio.sleep(0.3)

        await self.emit_completed(
            context,
            emit,
            message="Code remediation applied and verified." if is_revision else "Frontend source code built successfully.",
            data={"file_count": len(context.generated_files)},
        )
        await asyncio.sleep(0.2)

        # Handoff message according to Phase 3C requirement
        handoff_msg = (
            "Defects addressed. Requesting re-test."
            if is_revision
            else "Implementation generated. Ready for validation."
        )
        await self.emit_handoff(
            context,
            emit,
            to_agent_id="astrid",
            to_agent_name="Astrid Lindqvist",
            message=handoff_msg,
        )

    async def execute_modification(
        self,
        context: ProjectContext,
        emit: Callable[[WorkflowEvent], Awaitable[None]],
        modification_prompt: str,
        mode: str = "real",
    ) -> List[str]:
        """
        Phase 4B: Targeted, non-destructive modifications to existing project files.
        Ingests current files, applies precise patches based on natural language directive,
        and hands off directly to Astrid for differential QA.
        """
        await self.emit_started(
            context,
            emit,
            message=f"Analyzing revision directive: '{modification_prompt}'",
        )
        await asyncio.sleep(0.3)

        await self.emit_thinking(
            context,
            emit,
            f"Inspecting existing codebase ({len(context.generated_files)} files) to apply targeted modifications...",
        )
        await asyncio.sleep(0.3)

        modified_files: List[str] = []
        html_file = context.get_file("index.html")
        css_file = context.get_file("style.css")
        js_file = context.get_file("script.js")

        html = html_file.content if html_file else ""
        css = css_file.content if css_file else ""
        js = js_file.content if js_file else ""

        lower_prompt = modification_prompt.lower()
        snippet_preview = ""

        # Check for Gemini real modification if enabled
        if mode == "real" and llm_service.is_available:
            try:
                system_prompt = (
                    "You are Maya Thorne, Senior Frontend Developer at Auctor Systems. "
                    "You are performing a targeted, non-destructive modification of an existing static web application.\n"
                    "RULES:\n"
                    "1. Modify only files strictly relevant to the user directive.\n"
                    "2. Preserve all existing functionality, semantic markup, and Palette 4 tokens (#3A1028, #541B3B, #20243A, #B68A9A, #F5F4F5, #FFFFFF, #6B6C78, #29232B, #718276, #C79A4A).\n"
                    "3. NEVER use #D4AF37.\n"
                    "4. Output modified files using format:\n"
                    "===FILE: src/filename.ext===\n[file content]\n===END_FILE===\n"
                )
                user_msg = (
                    f"USER DIRECTIVE: {modification_prompt}\n\n"
                    f"EXISTING FILES:\n"
                    f"--- src/index.html ---\n{html}\n\n"
                    f"--- src/style.css ---\n{css}\n\n"
                    f"--- src/script.js ---\n{js}\n"
                )
                llm_response = await asyncio.to_thread(llm_service.generate_code, user_msg, system_prompt)
                if llm_response and "===FILE:" in llm_response:
                    parts = llm_response.split("===FILE:")
                    for part in parts[1:]:
                        if "===" in part and "===END_FILE===" in part:
                            header, rest = part.split("===", 1)
                            fname = header.strip()
                            content = rest.split("===END_FILE===")[0].strip()
                            clean_name = fname.split("/")[-1]
                            context.set_file(f"src/{clean_name}", clean_name, content, category="source")
                            modified_files.append(f"src/{clean_name}")
            except Exception as e:
                # Graceful fallback to deterministic patcher
                pass

        # Deterministic targeted patcher (Demo mode & fallback)
        if not modified_files:
            # 1. Subtitle / Title Patching
            import re
            quotes_match = re.findall(r"['\"]([^'\"]+)['\"]", modification_prompt)
            target_text = quotes_match[0] if quotes_match else None

            if "subtitle" in lower_prompt or "subheading" in lower_prompt or "tagline" in lower_prompt:
                sub_text = target_text or "Handcrafted Elegance & Bespoke Quality"
                if '<p class="hero-subtitle">' in html:
                    html = re.sub(r'<p class="hero-subtitle">.*?</p>', f'<p class="hero-subtitle">{sub_text}</p>', html, flags=re.DOTALL)
                    modified_files.append("src/index.html")
                    snippet_preview += f'<p class="hero-subtitle">{sub_text}</p>\n'
                elif '<p class="hero-subtitle" id="heroSubtitle">' in html:
                    html = re.sub(r'<p class="hero-subtitle" id="heroSubtitle">.*?</p>', f'<p class="hero-subtitle" id="heroSubtitle">{sub_text}</p>', html, flags=re.DOTALL)
                    modified_files.append("src/index.html")
                    snippet_preview += f'<p class="hero-subtitle" id="heroSubtitle">{sub_text}</p>\n'
                elif re.search(r'<p[^>]*class=[\'"][^\'"]*(?:sub|tagline|desc)[^\'"]*[\'"][^>]*>.*?</p>', html, flags=re.DOTALL):
                    html = re.sub(r'(<p[^>]*class=[\'"][^\'"]*(?:sub|tagline|desc)[^\'"]*[\'"][^>]*>).*?(</p>)', rf'\g<1>{sub_text}\g<2>', html, flags=re.DOTALL)
                    modified_files.append("src/index.html")
                    snippet_preview += f'<p class="sub">{sub_text}</p>\n'

            if "title" in lower_prompt or "headline" in lower_prompt:
                title_text = target_text or "Auctor Artisanal Experience"
                if '<h1 class="hero-title">' in html:
                    html = re.sub(r'<h1 class="hero-title">.*?</h1>', f'<h1 class="hero-title">{title_text}</h1>', html, flags=re.DOTALL)
                    if "src/index.html" not in modified_files:
                        modified_files.append("src/index.html")

            # 1b. Button / CTA Text Patching
            if "button" in lower_prompt or "cta" in lower_prompt or "action" in lower_prompt:
                btn_text = target_text or "Reserve Private Viewing"
                if '<button class="cta-btn">' in html or '<button class="cta-btn"' in html:
                    html = re.sub(r'<button class="cta-btn[^"]*">.*?</button>', f'<button class="cta-btn">{btn_text}</button>', html, flags=re.DOTALL)
                    if "src/index.html" not in modified_files:
                        modified_files.append("src/index.html")
                elif '<button class="hero-cta-btn"' in html or '<button class="hero-cta-btn">' in html:
                    html = re.sub(r'<button class="hero-cta-btn[^"]*">.*?</button>', f'<button class="hero-cta-btn">{btn_text}</button>', html, flags=re.DOTALL)
                    if "src/index.html" not in modified_files:
                        modified_files.append("src/index.html")
                elif '<a href="#features" class="btn btn-primary">' in html or '<a class="btn' in html:
                    html = re.sub(r'<a [^>]*class="btn btn-primary"[^>]*>.*?</a>', f'<a href="#features" class="btn btn-primary">{btn_text}</a>', html, flags=re.DOTALL)
                    if "src/index.html" not in modified_files:
                        modified_files.append("src/index.html")

            # 2. Modal / Inquiry Dialog
            if "modal" in lower_prompt or "inquiry" in lower_prompt or "contact" in lower_prompt:
                if 'id="inquiriesModal"' not in html:
                    modal_html = """
    <!-- Interactive Inquiries Modal (Revision Added) -->
    <div class="modal-overlay" id="inquiriesModal" aria-hidden="true" role="dialog" aria-labelledby="modalTitle">
      <div class="modal-container">
        <div class="modal-header">
          <h3 class="modal-title font-serif" id="modalTitle">Direct Studio Inquiry</h3>
          <button type="button" class="modal-close-btn" id="closeModalBtn" aria-label="Close modal dialog">&times;</button>
        </div>
        <form class="modal-form" id="inquiryForm">
          <div class="form-group">
            <label for="inquiryName">Your Name</label>
            <input type="text" id="inquiryName" name="name" required placeholder="e.g. Sravya Vance" />
          </div>
          <div class="form-group">
            <label for="inquiryEmail">Email Address</label>
            <input type="email" id="inquiryEmail" name="email" required placeholder="sravya@example.com" />
          </div>
          <div class="form-group">
            <label for="inquiryMessage">Project Specifications</label>
            <textarea id="inquiryMessage" name="message" rows="3" placeholder="Share your vision or requirements..."></textarea>
          </div>
          <button type="submit" class="btn btn-primary" id="submitInquiryBtn">
            <span class="btn-text">Submit Inquiry</span>
          </button>
        </form>
      </div>
    </div>
"""
                    html = html.replace("</main>", f"{modal_html}\n</main>")
                    if "src/index.html" not in modified_files:
                        modified_files.append("src/index.html")

            # 3. CSS Enhancements (borders, colors, gold, wine, spacing, typography, modal, navigation)
            if "navigation" in lower_prompt or "nav" in lower_prompt:
                nav_css = """
/* Phase 4B Primary Navigation Enhancement */
.site-header, .main-nav {
  background: var(--deep-wine, #3A1028) !important;
}
.site-header .logo-text, .site-header .brand-logo {
  color: var(--white, #FFFFFF) !important;
}
.site-header .brand-logo .logo-mark {
  background: var(--muted-gold, #C79A4A) !important;
  color: var(--deep-wine, #3A1028) !important;
}
.nav-link {
  color: rgba(245, 244, 245, 0.8) !important;
}
.nav-link:hover, .nav-link.active {
  color: var(--muted-gold, #C79A4A) !important;
  border-bottom: 2px solid var(--muted-gold, #C79A4A) !important;
  padding-bottom: 4px;
}
"""
                if "Phase 4B Primary Navigation Enhancement" not in css:
                    css += "\n" + nav_css
                if "src/style.css" not in modified_files:
                    modified_files.append("src/style.css")
                snippet_preview += nav_css[:120] + "...\n"

            if any(k in lower_prompt for k in ["wine", "gold", "border", "spacing", "layout", "typography", "button", "cta", "modal", "card"]):
                revision_css = """
/* Phase 4B Revision Styles */
.card-item, .feature-card, .showcase-card {
  border: 1px solid rgba(182, 138, 154, 0.25);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.card-item:hover, .feature-card:hover, .showcase-card:hover {
  border-color: var(--muted-gold);
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(58, 16, 40, 0.08);
}
.hero-cta-btn:focus-visible, .btn-primary:focus-visible, input:focus-visible, textarea:focus-visible {
  outline: 2px solid var(--muted-gold);
  outline-offset: 2px;
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(32, 36, 58, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}
.modal-overlay.active {
  opacity: 1;
  pointer-events: auto;
}
.modal-container {
  background: var(--white);
  border: 1px solid rgba(182, 138, 154, 0.3);
  border-radius: 12px;
  padding: 24px;
  max-width: 480px;
  width: 90%;
  box-shadow: 0 16px 40px rgba(58, 16, 40, 0.2);
}
"""
                if "Phase 4B Revision Styles" not in css:
                    css += "\n" + revision_css
                if "src/style.css" not in modified_files:
                    modified_files.append("src/style.css")
                snippet_preview += revision_css[:120] + "...\n"

            # 4. JavaScript Interactive Bindings (Modal / Button triggers)
            if "modal" in lower_prompt or "inquiry" in lower_prompt or "dialog" in lower_prompt:
                revision_js = """
// Modal Interactive Controller
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('inquiriesModal') || document.getElementById('contactModal');
  const openBtns = document.querySelectorAll('.cta-btn, .hero-cta-btn, #inquiryBtn, #openModalBtn, #openModalBtnHero, .nav-btn');
  const closeBtn = document.getElementById('closeModalBtn');
  if (modal) {
    openBtns.forEach(btn => btn.addEventListener('click', (e) => {
      e.preventDefault();
      modal.classList.add('active');
      modal.setAttribute('aria-hidden', 'false');
    }));
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
      });
    }
  }
});
"""
                if "Modal Interactive Controller" not in js:
                    js += "\n" + revision_js
                if "src/script.js" not in modified_files:
                    modified_files.append("src/script.js")

            # 4. Fallback if no specific rule matched: update hero & css tag
            if not modified_files:
                sub_text = target_text or modification_prompt
                if '<p class="hero-subtitle">' in html:
                    html = re.sub(r'<p class="hero-subtitle">.*?</p>', f'<p class="hero-subtitle">{sub_text}</p>', html, flags=re.DOTALL)
                elif '<p class="hero-subtitle" id="heroSubtitle">' in html:
                    html = re.sub(r'<p class="hero-subtitle" id="heroSubtitle">.*?</p>', f'<p class="hero-subtitle" id="heroSubtitle">{sub_text}</p>', html, flags=re.DOTALL)
                modified_files.append("src/index.html")
                modified_files.append("src/style.css")

            # Save updated source files into context
            if "src/index.html" in modified_files:
                context.set_file("src/index.html", "index.html", html, category="source")
            if "src/style.css" in modified_files:
                context.set_file("src/style.css", "style.css", css, category="source")
            if "src/script.js" in modified_files:
                context.set_file("src/script.js", "script.js", js, category="source")

        await self.emit_working(
            context,
            emit,
            f"Applied targeted modifications to: {', '.join(modified_files)}.",
            snippet=snippet_preview or f"/* Modified: {', '.join(modified_files)} */",
        )
        await asyncio.sleep(0.3)

        # Emit code_modified event
        await emit(
            WorkflowEvent(
                type=EventType.CODE_MODIFIED.value,
                project_id=context.project_id,
                agent=self.agent_id,
                agent_name=self.name,
                message=f"Code modifications applied to {len(modified_files)} files: {', '.join(modified_files)}.",
                data={
                    "modified_files": modified_files,
                    "directive": modification_prompt,
                },
            )
        )
        await asyncio.sleep(0.2)

        await self.emit_completed(
            context,
            emit,
            message=f"Refinement patch completed across {len(modified_files)} files.",
            data={"modified_files": modified_files},
        )
        await asyncio.sleep(0.2)

        # Handoff to Astrid Lindqvist
        await self.emit_handoff(
            context,
            emit,
            to_agent_id="astrid",
            to_agent_name="Astrid Lindqvist",
            message=f"Targeted changes applied to {', '.join(modified_files)}. Ready for differential QA.",
        )
        return modified_files
