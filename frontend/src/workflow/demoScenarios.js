// Auctor Systems — Multi-Agent Collaboration Scenarios & Mock Payloads
// Authentic dialogues, handoffs, questions, and recovery loops

export const DEFAULT_STUDENT_PRODUCTIVITY_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KAIROS — Student Productivity Studio</title>
  <link rel="stylesheet" href="style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;1,9..144,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
  <header class="navbar">
    <div class="brand">
      <span class="logo-mark">K</span>
      <span class="brand-title">KAIROS</span>
    </div>
    <nav class="nav-links">
      <a href="#focus" class="active">Focus Timer</a>
      <a href="#syllabus">Syllabus</a>
      <a href="#tasks">Action Items</a>
      <a href="#reflections">Reflections</a>
    </nav>
    <button class="cta-pill" onclick="alert('Starting deep work session...')">Start Session</button>
  </header>

  <main class="hero-section">
    <div class="hero-content">
      <span class="tagline-chip">ACADEMIC WORKSPACE ARCHITECTURE</span>
      <h1 class="hero-heading">Master your study rhythm with clarity and intent.</h1>
      <p class="hero-lead">An integrated academic operating system designed for deep study, milestone tracking, and mindful daily reflections.</p>
      
      <div class="focus-timer-card">
        <div class="timer-display">
          <span id="time-val">25:00</span>
          <span class="timer-mode-tag">DEEP WORK FOCUS</span>
        </div>
        <div class="timer-controls">
          <button id="toggle-btn" class="btn-primary" onclick="toggleTimer()">Begin Focus</button>
          <button class="btn-secondary" onclick="resetTimer()">Reset</button>
        </div>
      </div>
    </div>
  </main>

  <section id="tasks" class="modules-grid">
    <div class="card">
      <div class="card-header">
        <h3>Active Syllabi Milestones</h3>
        <span class="badge">Term 2</span>
      </div>
      <ul class="item-list">
        <li><span>Advanced Distributed Systems — Paper Review</span> <strong>Tomorrow</strong></li>
        <li><span>Cognitive Neuroscience — Lab Formulation</span> <strong>Oct 04</strong></li>
        <li><span>Modern Typographic Systems — Portfolio</span> <strong>Oct 12</strong></li>
      </ul>
    </div>

    <div class="card">
      <div class="card-header">
        <h3>Today's Critical Tasks</h3>
        <span class="badge">3 of 5 Done</span>
      </div>
      <ul class="task-checklist">
        <li class="done">✓ Synthesize seminar notes into obsidian vault</li>
        <li class="done">✓ Complete problem set 4: Matrix decompositions</li>
        <li class="done">✓ Peer review Clara's interaction thesis</li>
        <li>□ Outline literature review chapter 2</li>
        <li>□ 30-minute evening reading retreat</li>
      </ul>
    </div>
  </section>

  <footer class="footer">
    <p>© 2026 Kairos Academic Studio · Handcrafted with Auctor 8-Agent Orchestration</p>
  </footer>

  <script src="script.js"></script>
</body>
</html>`;

export const DEFAULT_STUDENT_PRODUCTIVITY_CSS = `/* Kairos — Editorial Student Productivity Studio */
:root {
  --wine: #3A1028;
  --burgundy: #541B3B;
  --rose: #B68A9A;
  --pearl: #F5F4F5;
  --white: #FFFFFF;
  --text-primary: #29232B;
  --text-secondary: #6B6C78;
  --sage: #718276;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: var(--pearl);
  color: var(--text-primary);
  line-height: 1.6;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 36px;
  background: var(--white);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-mark {
  width: 28px;
  height: 28px;
  background: var(--wine);
  color: var(--white);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 14px;
}

.brand-title {
  font-family: 'Fraunces', serif;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--wine);
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-links a {
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.nav-links a.active, .nav-links a:hover {
  color: var(--burgundy);
  font-weight: 600;
}

.cta-pill {
  padding: 8px 18px;
  background: var(--burgundy);
  color: var(--white);
  border: none;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
}

.cta-pill:hover {
  background: #672249;
  transform: translateY(-1px);
}

.hero-section {
  padding: 48px 36px 36px;
  max-width: 900px;
  margin: 0 auto;
  text-align: center;
}

.tagline-chip {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--burgundy);
  background: rgba(84, 27, 59, 0.08);
  padding: 4px 12px;
  border-radius: 9999px;
  margin-bottom: 14px;
}

.hero-heading {
  font-family: 'Fraunces', serif;
  font-size: 38px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--wine);
  margin-bottom: 14px;
}

.hero-lead {
  font-size: 15px;
  color: var(--text-secondary);
  max-width: 620px;
  margin: 0 auto 32px;
}

.focus-timer-card {
  background: var(--white);
  border: 1px solid rgba(0, 0, 0, 0.07);
  border-radius: 16px;
  padding: 28px;
  max-width: 360px;
  margin: 0 auto;
  box-shadow: 0 10px 30px rgba(58, 16, 40, 0.06);
}

.timer-display {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

#time-val {
  font-family: 'Fraunces', serif;
  font-size: 52px;
  font-weight: 700;
  color: var(--wine);
  letter-spacing: 2px;
}

.timer-mode-tag {
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--rose);
  font-weight: 700;
}

.timer-controls {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.btn-primary {
  padding: 9px 20px;
  background: var(--burgundy);
  color: var(--white);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}

.btn-secondary {
  padding: 9px 18px;
  background: var(--pearl);
  color: var(--text-secondary);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  max-width: 900px;
  margin: 0 auto 48px;
  padding: 0 36px;
}

.card {
  background: var(--white);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.card-header h3 {
  font-family: 'Fraunces', serif;
  font-size: 15px;
  color: var(--wine);
}

.badge {
  font-size: 10px;
  background: rgba(113, 130, 118, 0.15);
  color: var(--sage);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 9999px;
}

.item-list, .task-checklist {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 12.5px;
}

.item-list li {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  padding-bottom: 6px;
}

.item-list li strong {
  color: var(--burgundy);
  font-size: 11px;
}

.task-checklist li {
  color: var(--text-primary);
}

.task-checklist li.done {
  color: var(--text-secondary);
  text-decoration: line-through;
  opacity: 0.7;
}

.footer {
  text-align: center;
  padding: 24px;
  font-size: 11px;
  color: var(--text-secondary);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

@media (max-width: 640px) {
  .navbar { padding: 14px 20px; }
  .nav-links { display: none; }
  .hero-heading { font-size: 28px; }
  .modules-grid { padding: 0 20px; }
}`;

export const DEFAULT_STUDENT_PRODUCTIVITY_JS = `// Kairos Interactive Focus Timer Controller
let timerDuration = 25 * 60;
let timeRemaining = timerDuration;
let timerInterval = null;
let isRunning = false;

function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return \`\${m}:\${s}\`;
}

function updateDisplay() {
  const display = document.getElementById('time-val');
  if (display) {
    display.textContent = formatTime(timeRemaining);
  }
}

function toggleTimer() {
  const btn = document.getElementById('toggle-btn');
  if (isRunning) {
    clearInterval(timerInterval);
    isRunning = false;
    if (btn) btn.textContent = 'Resume Focus';
  } else {
    isRunning = true;
    if (btn) btn.textContent = 'Pause Focus';
    timerInterval = setInterval(() => {
      if (timeRemaining > 0) {
        timeRemaining--;
        updateDisplay();
      } else {
        clearInterval(timerInterval);
        isRunning = false;
        if (btn) btn.textContent = 'Session Done!';
        alert('Well done! You have completed your Kairos focus block.');
      }
    }, 1000);
  }
}

function resetTimer() {
  clearInterval(timerInterval);
  isRunning = false;
  timeRemaining = timerDuration;
  updateDisplay();
  const btn = document.getElementById('toggle-btn');
  if (btn) btn.textContent = 'Begin Focus';
}

document.addEventListener('DOMContentLoaded', () => {
  updateDisplay();
});`;

export const DEFAULT_README_MD = `# KAIROS — Academic Productivity Studio

Generated by **Auctor Systems 8-Agent Software Studio**

## Architecture & Specification
- **Framework**: Static HTML5 / Vanilla CSS3 / Modern ES6 JS
- **Typography**: Fraunces (Headings) & Plus Jakarta Sans (Body)
- **Palette**: Deep Wine, Burgundy, Midnight Navy, Dusty Rose, Sage
- **Compliance**: WCAG 2.1 AA Audited by Astrid Lindqvist

## Included Agents
1. Victoria Vance — Architecture & Product Scoping
2. Beatrice Stone — Requirements Specification
3. Clara Delacroix — UI/UX Design System
4. Maya Thorne — Component Implementation
5. Astrid Lindqvist — Accessibility & Viewport Testing
6. Genevieve Ward — Technical Documentation
7. Nadia Chen — Deployment Manifest (Vercel & Netlify)
8. Sophia Laurent — Product Launch Strategy
`;

export const DEFAULT_ARCHITECTURE_MD = `# Technical Architecture: KAIROS Academic Studio

## 1. Multi-Agent Provenance Pipeline
The application was synthesized through the Auctor Systems 8-Agent Autonomous Pipeline:
1. **Victoria Vance (Planning)**: Architectural scope decomposition and milestone tracking.
2. **Beatrice Stone (Requirements)**: Systems requirements matrix and study timer specification.
3. **Clara Delacroix (Design)**: Palette 4 design tokens (Deep Wine #3A1028, Burgundy #541B3B, Midnight Navy #20243A, Muted Gold #C79A4A).
4. **Maya Thorne (Development)**: Production-grade HTML5/CSS3/ES6+ web application implementation.
5. **Astrid Lindqvist (QA)**: Concrete property inspection, defect detection, and verification of remediated code.
6. **Genevieve Ward (Documentation)**: Developer documentation, user guides, and architecture specifications.
7. **Nadia Chen (Deployment)**: Static edge routing, security headers, and deployment manifest.
8. **Sophia Laurent (Marketing)**: SEO optimization, launch positioning, and promotional narrative.

## 2. Generated Application Architecture
- **DOM & Components**: Semantic layout featuring Focus Timer Card, Active Syllabi Milestones, and Reflective Journal.
- **Interactivity**: Pure vanilla JavaScript state loop handling Pomodoro timer intervals, reset state, and responsive menu drawer.
- **Accessibility**: WCAG 2.1 AA certified with explicit ARIA landmarks and :focus-visible outlines.
`;

export const DEFAULT_LAUNCH_COPY_MD = `# Launch Campaign Strategy: KAIROS Academic Studio

## 1. Product Name
**KAIROS — Academic Productivity Studio**

## 2. One-Line Value Proposition
Bespoke academic operating system crafted with Palette 4 editorial elegance and zero runtime framework dependencies.

## 3. Short Product Description
KAIROS unites mindful study rhythms, modular focus timers, and syllabus milestone tracking into a unified, high-performance static workspace. Built entirely with clean semantic HTML5, CSS3 Custom Properties, and vanilla ES6+ JavaScript.

## 4. Feature Highlights
- **Deep Work Focus Timer**: 25-minute Pomodoro timer with reactive start/pause and reset controls.
- **Modular Syllabi Milestones**: Structured academic course timeline with urgent milestone badges.
- **Palette 4 Editorial Design**: Refined color system featuring Deep Wine (#3A1028), Burgundy (#541B3B), and Muted Gold (#C79A4A).
- **Responsive Multi-Device Layout**: Fluid experience across mobile, tablet, and desktop viewports.
`;

export const DEFAULT_VERCEL_JSON = `{
  "version": 2,
  "public": true,
  "cleanUrls": true,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "SAMEORIGIN" },
        { "key": "X-Auctor-Studio", "value": "8-agent-orchestrated" }
      ]
    }
  ]
};`;

// Deterministic Sequence Scenarios
export function getScenarioForPrompt(prompt) {
  return [
    // ── 1. Victoria Vance (Planning) ─────────────────────────────────────────
    {
      agentId: 'planning',
      agentName: 'Victoria Vance',
      role: 'Project Planning Specialist',
      type: 'thinking',
      message: 'Deconstructing directive into architectural milestones and page hierarchy...',
      delay: 900,
    },
    {
      agentId: 'planning',
      agentName: 'Victoria Vance',
      role: 'Project Planning Specialist',
      type: 'working',
      message: 'Drafting project plan: defined single-page application with modular focus timer, syllabus tracker, and responsive grid.',
      delay: 1200,
    },
    {
      agentId: 'planning',
      agentName: 'Victoria Vance',
      role: 'Project Planning Specialist',
      type: 'dialogue',
      message: 'Planning complete. Project scope is structured into 4 cohesive components.',
      delay: 800,
    },
    {
      agentId: 'planning',
      agentName: 'Victoria Vance',
      role: 'Project Planning Specialist',
      toAgentId: 'requirements',
      toAgentName: 'Beatrice Stone',
      type: 'handoff',
      message: 'Victoria → Beatrice: Handing project plan over for functional requirements & scope validation.',
      delay: 1100,
    },

    // ── 2. Beatrice Stone (Requirements) ─────────────────────────────────────
    {
      agentId: 'requirements',
      agentName: 'Beatrice Stone',
      role: 'Systems Requirements Analyst',
      type: 'thinking',
      message: 'Reviewing functional requirements, interactive state contracts, and accessibility constraints...',
      delay: 900,
    },
    {
      agentId: 'requirements',
      agentName: 'Beatrice Stone',
      role: 'Systems Requirements Analyst',
      type: 'question',
      question: 'Which study timer methodology should be prioritized for the primary focus module?',
      options: [
        'Standard Pomodoro (25 min focus / 5 min rest)',
        'Customizable Deep Work Blocks (45-90 min)',
        'Both modes with instant switcher',
      ],
      message: 'Beatrice: Requesting client clarification on study timer preference...',
      delay: 0, // Pauses until user answers in chat!
    },
    {
      agentId: 'requirements',
      agentName: 'Beatrice Stone',
      role: 'Systems Requirements Analyst',
      type: 'working',
      message: 'Client specification incorporated. Finalizing requirements matrix & state transitions.',
      delay: 1100,
    },
    {
      agentId: 'requirements',
      agentName: 'Beatrice Stone',
      role: 'Systems Requirements Analyst',
      toAgentId: 'design',
      toAgentName: 'Clara Delacroix',
      type: 'handoff',
      message: 'Beatrice → Clara: Requirements matrix validated. Ready for design architecture.',
      delay: 1000,
    },

    // ── 3. Clara Delacroix (Design) ──────────────────────────────────────────
    {
      agentId: 'design',
      agentName: 'Clara Delacroix',
      role: 'UI/UX Design Architect',
      type: 'thinking',
      message: 'Curating Palette 4 editorial tokens: Deep Wine #3A1028, Burgundy #541B3B, and Pearl #F5F4F5...',
      delay: 900,
    },
    {
      agentId: 'design',
      agentName: 'Clara Delacroix',
      role: 'UI/UX Design Architect',
      type: 'working',
      message: 'Composing Fraunces display typography, micro-shadow elevations, and card grid specifications.',
      delay: 1200,
    },
    {
      agentId: 'design',
      agentName: 'Clara Delacroix',
      role: 'UI/UX Design Architect',
      toAgentId: 'development',
      toAgentName: 'Maya Thorne',
      type: 'handoff',
      message: 'Clara → Maya: Design specifications and CSS tokens prepared for frontend implementation.',
      delay: 1000,
    },

    // ── 4. Maya Thorne (Development) ─────────────────────────────────────────
    {
      agentId: 'development',
      agentName: 'Maya Thorne',
      role: 'Senior Frontend Developer',
      type: 'thinking',
      message: 'Structuring semantic HTML5 DOM and Vanilla JS state listener for timer controller...',
      delay: 900,
    },
    {
      agentId: 'development',
      agentName: 'Maya Thorne',
      role: 'Senior Frontend Developer',
      type: 'working',
      message: 'Assembling index.html, style.css, and script.js with responsive breakpoint listeners.',
      delay: 1400,
    },
    {
      agentId: 'development',
      agentName: 'Maya Thorne',
      role: 'Senior Frontend Developer',
      toAgentId: 'testing',
      toAgentName: 'Astrid Lindqvist',
      type: 'handoff',
      message: 'Maya → Astrid: Initial build compiled. Requesting accessibility and responsive audit.',
      delay: 1000,
    },

    // ── 5. Astrid Lindqvist (Testing) & QA Revision Loop with Maya ───────────
    {
      agentId: 'testing',
      agentName: 'Astrid Lindqvist',
      role: 'QA & Accessibility Auditor',
      type: 'thinking',
      message: 'Running automated WCAG 2.1 AA audit and responsive viewport simulations (Desktop, 768px, 375px)...',
      delay: 900,
    },
    {
      agentId: 'testing',
      agentName: 'Astrid Lindqvist',
      role: 'QA & Accessibility Auditor',
      toAgentId: 'development',
      toAgentName: 'Maya Thorne',
      type: 'review',
      message: 'Astrid → Maya: Audit Flag: Navigation touch targets on 375px mobile need +4px padding for compliance.',
      delay: 1100,
    },
    {
      agentId: 'development',
      agentName: 'Maya Thorne',
      role: 'Senior Frontend Developer',
      type: 'working',
      message: 'Maya: Applying responsive padding adjustment to mobile navigation targets in style.css.',
      delay: 1000,
    },
    {
      agentId: 'development',
      agentName: 'Maya Thorne',
      role: 'Senior Frontend Developer',
      toAgentId: 'testing',
      toAgentName: 'Astrid Lindqvist',
      type: 'dialogue',
      message: 'Maya → Astrid: Touch target padding increased to 12px. Revision deployed for re-audit.',
      delay: 900,
    },
    {
      agentId: 'testing',
      agentName: 'Astrid Lindqvist',
      role: 'QA & Accessibility Auditor',
      type: 'working',
      message: 'Astrid: Re-running audit suite... Score: 98/100. WCAG AA compliant and responsive breakpoints verified.',
      delay: 1000,
    },
    {
      agentId: 'testing',
      agentName: 'Astrid Lindqvist',
      role: 'QA & Accessibility Auditor',
      toAgentId: 'documentation',
      toAgentName: 'Genevieve Ward',
      type: 'handoff',
      message: 'Astrid → Genevieve: Build candidate fully passed testing. Ready for documentation.',
      delay: 1000,
    },

    // ── 6. Genevieve Ward (Documentation) ───────────────────────────────────
    {
      agentId: 'documentation',
      agentName: 'Genevieve Ward',
      role: 'Technical Documentation Lead',
      type: 'thinking',
      message: 'Drafting project README.md, technical architecture notes, and keyboard shortcuts guide...',
      delay: 900,
    },
    {
      agentId: 'documentation',
      agentName: 'Genevieve Ward',
      role: 'Technical Documentation Lead',
      type: 'working',
      message: 'Writing comprehensive documentation with installation commands and deployment specs.',
      delay: 1100,
    },
    {
      agentId: 'documentation',
      agentName: 'Genevieve Ward',
      role: 'Technical Documentation Lead',
      toAgentId: 'deployment',
      toAgentName: 'Nadia Chen',
      type: 'handoff',
      message: 'Genevieve → Nadia: Documentation generated. Handing off for deployment packaging.',
      delay: 1000,
    },

    // ── 7. Nadia Chen (Deployment) ───────────────────────────────────────────
    {
      agentId: 'deployment',
      agentName: 'Nadia Chen',
      role: 'DevOps & Deployment Architect',
      type: 'thinking',
      message: 'Configuring Vercel routing rules, static caching headers, and ZIP production bundle...',
      delay: 900,
    },
    {
      agentId: 'deployment',
      agentName: 'Nadia Chen',
      role: 'DevOps & Deployment Architect',
      type: 'working',
      message: 'Generated vercel.json configuration and bundled static assets for deployment.',
      delay: 1100,
    },
    {
      agentId: 'deployment',
      agentName: 'Nadia Chen',
      role: 'DevOps & Deployment Architect',
      toAgentId: 'marketing',
      toAgentName: 'Sophia Laurent',
      type: 'handoff',
      message: 'Nadia → Sophia: Production package verified and ready for launch communications.',
      delay: 1000,
    },

    // ── 8. Sophia Laurent (Marketing) ────────────────────────────────────────
    {
      agentId: 'marketing',
      agentName: 'Sophia Laurent',
      role: 'Product Marketing Strategist',
      type: 'thinking',
      message: 'Crafting product value proposition, feature summary, and SEO meta tags...',
      delay: 900,
    },
    {
      agentId: 'marketing',
      agentName: 'Sophia Laurent',
      role: 'Product Marketing Strategist',
      type: 'working',
      message: 'Synthesizing launch narrative: "Kairos Academic Operating System" is ready for release.',
      delay: 1100,
    },
    {
      agentId: 'marketing',
      agentName: 'Sophia Laurent',
      role: 'Product Marketing Strategist',
      type: 'completed',
      message: 'Sophia: All 8 specialized agents have concluded their deliverables.',
      delay: 800,
    },
  ];
}
