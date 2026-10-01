"""
test_phase3c.py — Phase 3C Generated Product Quality + Agent Collaboration Test Suite.
Validates:
1. Context sharing across Victoria, Beatrice, Clara, Maya, Astrid, Genevieve, Nadia, Sophia.
2. Maya generated application functionality & structure (search, category tabs, dynamic counter, accessible modal, toast).
3. Astrid code inspection detecting structured defects on Pass 1.
4. Maya QA remediation pass and Astrid re-test passing on Pass 2.
5. Exact handoff messages across the workflow.
6. Genevieve docs/README.md (10 sections) & docs/ARCHITECTURE.md (codebase-backed).
7. Nadia static routing checks and deploy/vercel.json.
8. Sophia marketing/LAUNCH_COPY.md (9 sections).
9. Completion summary payload in workflow_completed event.
"""

import sys
import asyncio
import json
import shutil
from pathlib import Path
from uuid import uuid4

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.context import ProjectContext
from orchestrator.engine import OrchestratorEngine
from services.project_manager import ProjectManager


async def run_phase3c_tests():
    print("=" * 60)
    print("TEST: Phase 3C Generated Product Quality + Agent Collaboration")
    print("=" * 60)

    test_id = f"test-p3c-{uuid4().hex[:6]}"
    engine = OrchestratorEngine(project_id=test_id)
    events_raw = []

    # Stream collector task
    async def collect_events():
        async for sse_chunk in engine.stream_events():
            events_raw.append(sse_chunk)
            if "workflow_completed" in sse_chunk:
                break

    stream_task = asyncio.create_task(collect_events())

    # Start generation in demo mode (fast, deterministic)
    prompt = "Create a luxury architectural studio portfolio with interactive case study filtering, modal dialog, and contact workflow"
    engine.start(prompt, mode="demo")

    # Step 1: Wait for Beatrice clarification
    clarification_detected = False
    for _ in range(50):
        await asyncio.sleep(0.1)
        if any(e.type == "user_input_required" for e in engine.events_history):
            clarification_detected = True
            break

    assert clarification_detected, "Beatrice failed to emit user_input_required event!"
    print("  ✓ Step 1: Beatrice emitted user_input_required and paused workflow.")

    # Step 2: Resume with user clarification
    resumed = engine.provide_user_input("Option A: Interactive Project Showcase with Real-Time Filtering & Client Inquiry Portal")
    assert resumed is True, "Failed to resume orchestrator with user clarification!"
    print("  ✓ Step 2: Resumed orchestrator with user clarification.")

    # Step 3: Wait for workflow completion
    for _ in range(200):
        await asyncio.sleep(0.1)
        if any(e.type == "workflow_completed" for e in engine.events_history):
            break

    assert any(e.type == "workflow_completed" for e in engine.events_history), "Workflow timed out before completion!"
    print("  ✓ Step 3: 8-agent workflow completed.")

    # Step 4: Verify Events and Handoff Messages
    handoffs = [e for e in engine.events_history if e.type == "agent_handoff"]
    handoff_messages = [h.message for h in handoffs]

    print(f"  Handoff count: {len(handoffs)}")
    for h in handoffs:
        print(f"    - [{h.from_agent}] -> [{h.to_agent}]: {h.message}")

    assert any("Project scope and milestone plan completed" in m for m in handoff_messages), "Victoria handoff missing"
    assert any("Requirements confirmed with user" in m for m in handoff_messages), "Beatrice handoff missing"
    assert any("Design system and responsive layout specification ready" in m for m in handoff_messages), "Clara handoff missing"
    assert any("Implementation generated. Ready for validation" in m for m in handoff_messages), "Maya pass 1 handoff missing"
    assert any("2 defects detected in interaction validation" in m for m in handoff_messages), "Astrid pass 1 handoff missing"
    assert any("Defects addressed. Requesting re-test" in m for m in handoff_messages), "Maya pass 2 handoff missing"
    assert any("Validation passed" in m for m in handoff_messages), "Astrid pass 2 handoff missing"
    assert any("Documentation compiled based on validated codebase" in m for m in handoff_messages), "Genevieve handoff missing"
    assert any("Deployment manifest configured for production static edge" in m for m in handoff_messages), "Nadia handoff missing"

    # Sophia is the final agent; verify her completed event
    completed_agent_events = [e for e in engine.events_history if e.type == "agent_completed"]
    completed_messages = [c.message for c in completed_agent_events]
    assert any("Brand narrative, launch messaging, and SEO configuration approved" in m for m in completed_messages), "Sophia completion message missing"

    print("  ✓ Step 4: All exact Phase 3C handoff and completion messages verified.")

    # Step 5: Verify Astrid QA defect detection & resolution events
    test_failed_events = [e for e in engine.events_history if e.type == "test_failed"]
    test_passed_events = [e for e in engine.events_history if e.type == "test_passed"]

    assert len(test_failed_events) >= 1, "Expected test_failed event from Astrid Pass 1"
    assert len(test_passed_events) >= 1, "Expected test_passed event from Astrid Pass 2"

    failed_data = test_failed_events[0].data or {}
    assert "defects" in failed_data, "test_failed event missing defects array"
    defects = failed_data["defects"]
    assert len(defects) == 2, f"Expected 2 defects, found {len(defects)}"
    assert "aria-label" in defects[0]["issue"]
    assert ":focus-visible" in defects[1]["issue"]
    assert defects[0]["file"] == "src/index.html"
    assert defects[1]["file"] == "src/style.css"

    print("  ✓ Step 5: Astrid concrete QA defect inspection & structure verified.")

    # Step 6: Verify Generated Code Quality (Maya Thorne)
    project_dir = Path(__file__).parent / "projects" / test_id
    html_path = project_dir / "src" / "index.html"
    css_path = project_dir / "src" / "style.css"
    js_path = project_dir / "src" / "script.js"

    assert html_path.exists() and css_path.exists() and js_path.exists(), "Source files not created"

    html_content = html_path.read_text(encoding="utf-8")
    css_content = css_path.read_text(encoding="utf-8")
    js_content = js_path.read_text(encoding="utf-8")

    # HTML checks
    assert 'id="filterSearchInput"' in html_content, "HTML missing filterSearchInput"
    assert 'class="tab-btn' in html_content, "HTML missing tab-btn filter tabs"
    assert 'id="visibleCountBadge"' in html_content, "HTML missing dynamic visibleCountBadge"
    assert 'id="contactModal"' in html_content, "HTML missing contactModal"
    assert 'aria-label="Close modal dialog"' in html_content, "HTML missing resolved aria-label on close button"
    assert 'id="inquiryToast"' in html_content, "HTML missing toast notification container"

    # CSS checks
    assert ":focus-visible" in css_content, "CSS missing resolved :focus-visible rules"
    assert "--deep-wine: #3A1028" in css_content, "CSS missing Palette 4 Deep Wine"
    assert "--midnight-navy: #20243A" in css_content, "CSS missing Palette 4 Midnight Navy"
    assert "@media (max-width: 768px)" in css_content, "CSS missing tablet breakpoint"

    # JS checks
    assert "filterSearchInput" in js_content, "JS missing real-time search input binding"
    assert "tabButtons" in js_content, "JS missing category filter tab buttons binding"
    assert "inquiryForm" in js_content, "JS missing inquiry form submission logic"
    assert "showToast" in js_content, "JS missing toast notification display function"
    assert "applyFilters" in js_content, "JS missing reactive filter state function"

    print("  ✓ Step 6: Maya's interactive web application code & defect remediation verified.")

    # Step 7: Verify Genevieve Documentation (docs/README.md & docs/ARCHITECTURE.md)
    readme_path = project_dir / "docs" / "README.md"
    arch_path = project_dir / "docs" / "ARCHITECTURE.md"

    assert readme_path.exists() and arch_path.exists(), "Documentation files not created"

    readme_content = readme_path.read_text(encoding="utf-8")
    arch_content = arch_path.read_text(encoding="utf-8")

    # 10 required sections in README.md
    required_readme_sections = [
        "## 1. Product Overview",
        "## 2. Features",
        "## 3. Technology Stack",
        "## 4. Project Structure",
        "## 5. How to Run",
        "## 6. How the Application Works",
        "## 7. Responsive Behavior",
        "## 8. Testing & QA Certification",
        "## 9. Deployment",
        "## 10. Limitations"
    ]
    for sec in required_readme_sections:
        assert sec in readme_content, f"README.md missing section: {sec}"

    assert "index.html" in readme_content and "style.css" in readme_content and "script.js" in readme_content
    assert "Data & Control Flow" in arch_content
    print("  ✓ Step 7: Genevieve's 10-section README.md and ARCHITECTURE.md verified.")

    # Step 8: Verify Nadia Deployment Manifest (deploy/vercel.json)
    vercel_path = project_dir / "deploy" / "vercel.json"
    assert vercel_path.exists(), "deploy/vercel.json missing"
    vercel_content = vercel_path.read_text(encoding="utf-8")
    assert '"cleanUrls": true' in vercel_content
    assert 'X-Content-Type-Options' in vercel_content and 'nosniff' in vercel_content
    assert '"/src/index.html"' in vercel_content
    print("  ✓ Step 8: Nadia's verified edge routing manifest (deploy/vercel.json) verified.")

    # Step 9: Verify Sophia Marketing Copy (marketing/LAUNCH_COPY.md)
    marketing_path = project_dir / "marketing" / "LAUNCH_COPY.md"
    assert marketing_path.exists(), "marketing/LAUNCH_COPY.md missing"
    marketing_content = marketing_path.read_text(encoding="utf-8")

    required_marketing_sections = [
        "## 1. Product Name",
        "## 2. One-Line Value Proposition",
        "## 3. Short Product Description",
        "## 4. Feature Highlights",
        "## 5. Target Audience",
        "## 6. Launch Announcement",
        "## 7. Social Media Copy",
        "## 8. SEO Title",
        "## 9. SEO Description"
    ]
    for sec in required_marketing_sections:
        assert sec in marketing_content, f"marketing/LAUNCH_COPY.md missing section: {sec}"
    print("  ✓ Step 9: Sophia's 9-section validated launch copy verified.")

    # Step 10: Verify Completion Summary in workflow_completed event
    completed_events = [e for e in engine.events_history if e.type == "workflow_completed"]
    assert len(completed_events) == 1, "Expected exactly 1 workflow_completed event"
    summary = completed_events[0].data.get("completion_summary")
    assert summary is not None, "workflow_completed event missing completion_summary"

    print("  Completion Summary:")
    print(f"    Product: {summary.get('product_name')}")
    print(f"    Agents Completed: {summary.get('agents_completed')}")
    print(f"    QA Status: {summary.get('qa_status')}")
    print(f"    Revisions: {summary.get('revisions_count')}")
    print(f"    File Count: {summary.get('file_count')}")
    print(f"    Docs Status: {summary.get('docs_status')}")
    print(f"    Deploy Status: {summary.get('deploy_status')}")
    print(f"    Marketing Status: {summary.get('marketing_status')}")

    assert summary.get("agents_completed") == "8 / 8 completed"
    assert summary.get("qa_status") == "Passed"
    assert summary.get("revisions_count") == 1
    assert summary.get("file_count") in [7, 8]
    assert summary.get("docs_status") == "Complete"
    assert summary.get("deploy_status") == "Ready"
    assert summary.get("marketing_status") == "Complete"

    print("  ✓ Step 10: Completion summary verified with exact required fields.")

    # Clean up test project directory
    shutil.rmtree(project_dir, ignore_errors=True)
    print("=" * 60)
    print("  ✅ PASS: All Phase 3C capabilities verified successfully!")
    print("=" * 60)


def test_phase3c_suite():
    asyncio.run(run_phase3c_tests())


if __name__ == "__main__":
    test_phase3c_suite()
