"""
Auctor Systems — Task Definitions

Defines the 8 CrewAI tasks that correspond to each agent.
Tasks are chained sequentially: output from task N is available
as context to task N+1 via CrewAI's automatic context passing.
"""

from crewai import Task, Agent


def create_tasks(agents: list[Agent], user_prompt: str) -> list[Task]:
    """
    Create and return all 8 tasks in pipeline order.
    Each task's description includes the user's original prompt
    and instructions for what to produce.
    
    Args:
        agents: List of 8 agents in order (Planning through Marketing)
        user_prompt: The user's original website description
    
    Returns:
        List of 8 Task objects in execution order
    """
    (
        planning_agent,
        requirements_agent,
        design_agent,
        development_agent,
        testing_agent,
        documentation_agent,
        deployment_agent,
        marketing_agent,
    ) = agents

    # ── 1. Planning Task ──────────────────────────────────────────────────
    planning_task = Task(
        description=(
            f"The user wants the following website built:\n\n"
            f'"{user_prompt}"\n\n'
            f"Create a comprehensive project plan that includes:\n"
            f"1. Project name and summary\n"
            f"2. Target audience description\n"
            f"3. List of all pages to create (e.g., Home, About, Contact, etc.)\n"
            f"4. Key features and content sections for each page\n"
            f"5. Technical approach (static HTML/CSS/JS)\n"
            f"6. Milestones and task breakdown\n\n"
            f"Be specific and practical. This plan will guide the entire build process."
        ),
        expected_output=(
            "A structured project plan document with clear headings covering: "
            "project overview, target audience, page list with descriptions, "
            "features per page, content sections, and milestone breakdown."
        ),
        agent=planning_agent,
    )

    # ── 2. Requirements Task ──────────────────────────────────────────────
    requirements_task = Task(
        description=(
            "Based on the project plan, create a complete requirements document.\n\n"
            "Cover the following:\n"
            "1. FUNCTIONAL REQUIREMENTS:\n"
            "   - User stories (As a user, I want to...)\n"
            "   - Interactive features (forms, navigation, animations, etc.)\n"
            "   - Content requirements per page\n\n"
            "2. NON-FUNCTIONAL REQUIREMENTS:\n"
            "   - Performance (fast loading, optimized assets)\n"
            "   - Accessibility (WCAG 2.1 AA compliance)\n"
            "   - Responsiveness (mobile-first: 375px, 768px, 1200px+)\n"
            "   - SEO (meta tags, semantic HTML, structured headings)\n"
            "   - Browser compatibility (Chrome, Firefox, Safari, Edge)\n\n"
            "3. CONTENT REQUIREMENTS:\n"
            "   - Real text content needed (not Lorem ipsum)\n"
            "   - Image/icon placeholders with descriptions\n"
            "   - Call-to-action text\n\n"
            "Be thorough — the design and development agents depend on this."
        ),
        expected_output=(
            "A complete requirements specification with functional requirements "
            "(user stories, features), non-functional requirements (performance, "
            "accessibility, responsiveness, SEO), and content requirements."
        ),
        agent=requirements_agent,
    )

    # ── 3. Design Task ────────────────────────────────────────────────────
    design_task = Task(
        description=(
            "Based on the requirements, create a complete visual design specification.\n\n"
            "You MUST specify:\n"
            "1. COLOR PALETTE: Primary, secondary, accent, background, text colors with hex codes\n"
            "2. TYPOGRAPHY: Font families (from Google Fonts), sizes, weights, line heights\n"
            "3. SPACING SYSTEM: Consistent padding/margin scale (e.g., 4px, 8px, 16px, 24px, 32px, 48px, 64px)\n"
            "4. LAYOUT: Page layout for each page (header, hero, sections, footer)\n"
            "5. COMPONENTS: Button styles, card styles, form styles, navigation styles\n"
            "6. RESPONSIVE STRATEGY: What changes at mobile (375px), tablet (768px), desktop (1200px+)\n"
            "7. VISUAL EFFECTS: Hover states, transitions, scroll animations\n"
            "8. NAVIGATION: Menu structure, mobile menu behavior\n\n"
            "Be extremely specific with CSS values. The developer must be able to "
            "directly translate your spec into code without guessing."
        ),
        expected_output=(
            "A detailed design specification with exact hex color codes, Google Font "
            "selections, spacing scale, layout descriptions per page, component styles, "
            "responsive breakpoint behavior, and visual effect descriptions."
        ),
        agent=design_agent,
    )

    # ── 4. Development Task ───────────────────────────────────────────────
    development_task = Task(
        description=(
            "Generate the complete website code based on the design specification.\n\n"
            "CRITICAL OUTPUT FORMAT — You MUST use this exact format for EVERY file:\n\n"
            "===FILE: filename.ext===\n"
            "[complete file content]\n"
            "===END_FILE===\n\n"
            "REQUIRED FILES:\n"
            "1. index.html — Main page with full HTML structure\n"
            "2. style.css — Complete responsive stylesheet\n"
            "3. script.js — All JavaScript functionality\n"
            "4. Additional .html files for each page in the plan\n\n"
            "CODING STANDARDS:\n"
            "- HTML: Semantic tags, proper meta tags, Google Fonts link, "
            "Open Graph tags, lang attribute\n"
            "- CSS: Mobile-first responsive design, CSS custom properties for colors, "
            "smooth transitions, proper reset/normalize\n"
            "- JS: Smooth scroll, mobile menu toggle, form handling, scroll animations, "
            "intersection observer for reveal effects\n"
            "- Use the EXACT colors, fonts, and spacing from the design spec\n"
            "- Write REAL content appropriate for the website — NO placeholder text\n"
            "- All internal links must work between pages\n"
            "- All code must be COMPLETE — no comments like '// add more here'\n\n"
            "The generated website must look professional when opened in any browser."
        ),
        expected_output=(
            "Complete website source code with all files in ===FILE: name=== format. "
            "Minimum: index.html, style.css, script.js. "
            "All code must be complete, functional, and production-ready."
        ),
        agent=development_agent,
    )

    # ── 5. Testing Task ───────────────────────────────────────────────────
    testing_task = Task(
        description=(
            "Review and audit all generated HTML, CSS, and JavaScript code.\n\n"
            "TEST CHECKLIST:\n"
            "1. HTML VALIDITY: Proper doctype, head structure, semantic tags, "
            "closing tags, valid attributes\n"
            "2. CSS QUALITY: Valid syntax, no undefined custom properties, "
            "responsive rules for all breakpoints, no conflicting rules\n"
            "3. JAVASCRIPT: Valid syntax, no undefined variables, event listeners "
            "properly attached, no console errors expected\n"
            "4. ACCESSIBILITY: Alt text on images, ARIA labels on interactive elements, "
            "sufficient color contrast, keyboard navigation, focus styles\n"
            "5. LINKS: All internal href links point to existing pages, "
            "anchor links reference existing IDs\n"
            "6. RESPONSIVE: Layout works at 375px, 768px, and 1200px+\n"
            "7. META TAGS: Title, description, viewport, charset, Open Graph\n\n"
            "OUTPUT FORMAT:\n"
            "- Overall: PASS or FAIL\n"
            "- For each issue found: [CRITICAL/WARNING/INFO] Description + Fix\n"
            "- If CRITICAL issues exist, output corrected files using:\n"
            "  ===FILE: filename.ext===\n"
            "  [corrected content]\n"
            "  ===END_FILE===\n\n"
            "Be thorough but fair. Only mark FAIL for genuinely broken code."
        ),
        expected_output=(
            "A structured test report with PASS/FAIL status, list of issues by "
            "severity (CRITICAL/WARNING/INFO), fix recommendations, and corrected "
            "files if critical issues were found."
        ),
        agent=testing_agent,
    )

    # ── 6. Documentation Task ─────────────────────────────────────────────
    documentation_task = Task(
        description=(
            "Generate project documentation based on the actual generated code.\n\n"
            "Create these files using the ===FILE: format:\n\n"
            "===FILE: README.md===\n"
            "Include: project title, description (2-3 sentences), features list, "
            "tech stack, file structure tree, how to run locally (just open index.html), "
            "how to deploy (Vercel one-click), customization guide, license.\n"
            "===END_FILE===\n\n"
            "===FILE: ARCHITECTURE.md===\n"
            "Include: overview, file descriptions, CSS architecture (custom properties, "
            "responsive strategy), JavaScript functionality overview, design decisions.\n"
            "===END_FILE===\n\n"
            "Documentation must accurately reflect the ACTUAL code that was generated. "
            "Do not write generic template documentation."
        ),
        expected_output=(
            "Complete README.md and ARCHITECTURE.md files in ===FILE: format, "
            "accurately describing the generated project."
        ),
        agent=documentation_agent,
    )

    # ── 7. Deployment Task ────────────────────────────────────────────────
    deployment_task = Task(
        description=(
            "Generate deployment configuration for the static website.\n\n"
            "Create these files using the ===FILE: format:\n\n"
            "===FILE: vercel.json===\n"
            "Vercel configuration for static site deployment. Include:\n"
            '{\n'
            '  "version": 2,\n'
            '  "builds": [{"src": "*.html", "use": "@vercel/static"}],\n'
            '  "routes": [appropriate route configuration]\n'
            '}\n'
            "===END_FILE===\n\n"
            "===FILE: DEPLOYMENT.md===\n"
            "Step-by-step deployment guide covering:\n"
            "- Vercel deployment (recommended): CLI and dashboard methods\n"
            "- Netlify alternative\n"
            "- GitHub Pages alternative\n"
            "- Custom domain setup\n"
            "- HTTPS configuration\n"
            "===END_FILE===\n\n"
            "Configuration must be production-ready and correct."
        ),
        expected_output=(
            "vercel.json configuration and DEPLOYMENT.md guide in ===FILE: format."
        ),
        agent=deployment_agent,
    )

    # ── 8. Marketing Task ─────────────────────────────────────────────────
    marketing_task = Task(
        description=(
            "Create marketing and launch materials for the completed website.\n\n"
            "Create this file using the ===FILE: format:\n\n"
            "===FILE: MARKETING.md===\n"
            "Include ALL of the following:\n\n"
            "1. PRODUCT DESCRIPTION:\n"
            "   - Elevator pitch (1 sentence)\n"
            "   - Short description (1 paragraph)\n"
            "   - Full description (3-4 paragraphs)\n\n"
            "2. VALUE PROPOSITION:\n"
            "   - 3-5 unique selling points\n"
            "   - Key differentiators\n\n"
            "3. TARGET AUDIENCE:\n"
            "   - Primary audience profile\n"
            "   - Secondary audience\n"
            "   - User personas (2-3)\n\n"
            "4. SEO STRATEGY:\n"
            "   - Primary keywords (5-10)\n"
            "   - Long-tail keywords (5-10)\n"
            "   - Meta description for each page\n\n"
            "5. SOCIAL MEDIA LAUNCH:\n"
            "   - Twitter/X launch thread (3-5 tweets)\n"
            "   - LinkedIn announcement post\n"
            "   - Instagram caption\n\n"
            "6. EMAIL TEMPLATE:\n"
            "   - Launch announcement email\n\n"
            "7. LAUNCH CHECKLIST:\n"
            "   - Pre-launch, launch day, post-launch tasks\n\n"
            "===END_FILE===\n\n"
            "All content must be specific to the actual website that was built. "
            "Do NOT write generic marketing templates."
        ),
        expected_output=(
            "MARKETING.md file in ===FILE: format with product description, "
            "value proposition, target audience, SEO keywords, social media posts, "
            "email template, and launch checklist."
        ),
        agent=marketing_agent,
    )

    return [
        planning_task,
        requirements_task,
        design_task,
        development_task,
        testing_task,
        documentation_task,
        deployment_task,
        marketing_task,
    ]
