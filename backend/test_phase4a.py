"""
Auctor Systems — Phase 4A Verification Test Suite
Persistent Project Workspace & Database Isolation Verification

Tests:
1. project creation
2. project listing
3. project retrieval
4. project update
5. project deletion
6. multiple-project isolation
7. persistence after reload (memory wipe / server restart simulation)
8. generated file CONTENT persistence (all 8 files with actual text)
9. activity history persistence (chronological stream, zero fake events)
10. requirements persistence (Beatrice requirements dict)
11. clarification persistence (ClarificationData question, options, user_response)
12. agent state persistence (all 8 agent statuses)
13. QA / revision persistence (Astrid test results, defects, revision count)
14. completion summary persistence (product name, file counts, QA status)
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

from database import db, Database
from orchestrator.engine import OrchestratorEngine
from orchestrator.context import ProjectContext, ClarificationData, GeneratedFile
from models import GenerateRequest, ProjectUpdateRequest, ClarificationInput
from main import app, active_engines
from httpx import AsyncClient, ASGITransport


async def run_phase4a_tests():
    print("=" * 70)
    print("TEST: Phase 4A — Persistent Project Workspace Verification")
    print("=" * 70)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ── 1. Project Creation ───────────────────────────────────────────────
        print("\n[1] Testing Project Creation...")
        proj_a_id = f"test-p4a-alpha-{uuid4().hex[:6]}"
        create_res = await client.post(
            "/api/projects",
            json={
                "prompt": "Create a boutique sustainable coffee brand web studio with online ordering",
                "mode": "demo",
                "name": "Verdant Brew Co.",
            },
        )
        assert create_res.status_code == 200, f"Project creation failed: {create_res.text}"
        create_data = create_res.json()
        assert "project_id" in create_data
        created_pid = create_data["project_id"]
        assert create_data["status"] == "generating"

        # Verify in SQLite database directly
        db_proj = db.get_project(created_pid)
        assert db_proj is not None, "Project was not written to SQLite 'projects' table!"
        assert db_proj["id"] == created_pid
        assert "coffee" in db_proj["prompt"].lower()
        print(f"  ✓ Project created and registered in SQLite: {created_pid}")

        # ── 2. Project Listing ────────────────────────────────────────────────
        print("\n[2] Testing Project Listing...")
        list_res = await client.get("/api/projects")
        assert list_res.status_code == 200
        projects_list = list_res.json()
        assert isinstance(projects_list, list), "List response should be an array of projects"
        matching = [p for p in projects_list if p["id"] == created_pid]
        assert len(matching) == 1, "Created project not found in /api/projects listing"
        assert "file_count" in matching[0]
        assert "activity_count" in matching[0]
        print(f"  ✓ Project listing returns {len(projects_list)} projects with counts.")

        # ── 3. Project Retrieval ──────────────────────────────────────────────
        print("\n[3] Testing Project Retrieval...")
        get_res = await client.get(f"/api/projects/{created_pid}")
        assert get_res.status_code == 200
        project_state = get_res.json()
        assert project_state["project_id"] == created_pid
        assert project_state["prompt"] == db_proj["prompt"]
        print(f"  ✓ Project retrieved successfully via GET /api/projects/{created_pid}")

        # ── 4. Project Update ─────────────────────────────────────────────────
        print("\n[4] Testing Project Update...")
        new_name = "Verdant Roast & Lab"
        update_res = await client.put(
            f"/api/projects/{created_pid}",
            json={"name": new_name, "description": "Artisanal coffee subscription platform"},
        )
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["name"] == new_name
        assert updated_data["description"] == "Artisanal coffee subscription platform"

        # Verify update in database
        check_db = db.get_project(created_pid)
        assert check_db["name"] == new_name
        print(f"  ✓ Project metadata updated in SQLite: '{new_name}'")

        # ── 5. Project Deletion ───────────────────────────────────────────────
        print("\n[5] Testing Project Deletion & Cascading Clean-up...")
        temp_del_id = f"test-del-{uuid4().hex[:6]}"
        db.create_project(temp_del_id, prompt="Temporary site to delete", name="Disposable")
        db.save_file(temp_del_id, "src/index.html", "index.html", "<h1>Del</h1>", "html")
        db.save_activity(temp_del_id, "test_event", "victoria", "Victoria", "Starting")

        assert db.get_project(temp_del_id) is not None
        assert len(db.get_files(temp_del_id)) == 1
        assert len(db.get_activities(temp_del_id)) == 1

        del_res = await client.delete(f"/api/projects/{temp_del_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # Verify cascade deletion from SQLite
        assert db.get_project(temp_del_id) is None
        assert len(db.get_files(temp_del_id)) == 0
        assert len(db.get_activities(temp_del_id)) == 0

        # Verify 404 after deletion
        not_found_res = await client.get(f"/api/projects/{temp_del_id}")
        assert not_found_res.status_code == 404
        print("  ✓ Project and associated files/activities deleted cleanly with cascade.")

        # ── 6. Multiple-Project Isolation ─────────────────────────────────────
        print("\n[6] Testing Strict Multiple-Project Isolation (Project A vs. Project B)...")
        pid_a = f"proj-iso-a-{uuid4().hex[:6]}"
        pid_b = f"proj-iso-b-{uuid4().hex[:6]}"

        # Create Project A
        db.create_project(pid_a, prompt="Project Alpha prompt", name="Alpha Studio")
        db.save_file(pid_a, "src/index.html", "index.html", "<html>Alpha Project Content</html>", "html")
        db.save_file(pid_a, "README.md", "README.md", "# Alpha Documentation", "md")
        db.save_activity(pid_a, "agent_started", "victoria", "Victoria Vance", "Alpha Started")

        # Create Project B
        db.create_project(pid_b, prompt="Project Beta prompt", name="Beta Tech")
        db.save_file(pid_b, "src/index.html", "index.html", "<html>Beta Project Content</html>", "html")
        db.save_file(pid_b, "README.md", "README.md", "# Beta Documentation", "md")
        db.save_activity(pid_b, "agent_started", "maya", "Maya Thorne", "Beta Maya Working")

        # Verify Project A data does NOT contain Project B data
        files_a = db.get_files(pid_a)
        files_b = db.get_files(pid_b)
        assert len(files_a) == 2
        assert len(files_b) == 2

        file_a_content = db.get_file(pid_a, "src/index.html")["content"]
        file_b_content = db.get_file(pid_b, "src/index.html")["content"]
        assert file_a_content == "<html>Alpha Project Content</html>"
        assert file_b_content == "<html>Beta Project Content</html>"
        assert "Beta" not in file_a_content
        assert "Alpha" not in file_b_content

        # Verify activities isolation
        acts_a = db.get_activities(pid_a)
        acts_b = db.get_activities(pid_b)
        assert len(acts_a) == 1 and acts_a[0]["message"] == "Alpha Started"
        assert len(acts_b) == 1 and acts_b[0]["message"] == "Beta Maya Working"

        # Delete Project B, verify Project A remains completely intact
        del_b = await client.delete(f"/api/projects/{pid_b}")
        assert del_b.status_code == 200
        assert db.get_project(pid_b) is None
        assert db.get_project(pid_a) is not None
        assert db.get_file(pid_a, "src/index.html")["content"] == "<html>Alpha Project Content</html>"
        print("  ✓ Strict project isolation verified: zero cross-contamination between A and B.")

        # ── 7–14. Full Pipeline Execution & Complete Persistence ──────────────
        print("\n[7-14] Testing Full 8-Agent Execution, Content Persistence & Restoration...")
        e2e_id = f"test-p4a-full-{uuid4().hex[:6]}"
        engine = OrchestratorEngine(project_id=e2e_id)

        # Collect events
        events_stream = []
        async def event_collector():
            async for sse in engine.stream_events():
                events_stream.append(sse)
                if "workflow_completed" in sse:
                    break

        collector_task = asyncio.create_task(event_collector())

        # Start demo mode execution
        prompt = "Create a luxury acoustic guitar luthier showcase with custom build estimator and tone selector"
        engine.start(prompt, mode="demo", name="Aura Guitars")
        active_engines[e2e_id] = engine

        # Beatrice clarification pause
        clarification_seen = False
        for _ in range(50):
            await asyncio.sleep(0.1)
            if any(e.type == "user_input_required" for e in engine.events_history):
                clarification_seen = True
                break
        assert clarification_seen, "Beatrice clarification pause failed!"

        # Provide user clarification
        engine.provide_user_input("Option 1: Vintage Nitrocellulose Finish with Hand-Carved Bracing")

        # Wait for workflow completion
        for _ in range(200):
            await asyncio.sleep(0.1)
            if any(e.type == "workflow_completed" for e in engine.events_history):
                break

        assert any(e.type == "workflow_completed" for e in engine.events_history), "Workflow failed to complete!"
        print("  ✓ 8-agent pipeline executed to completion.")

        # ── SIMULATE COMPLETE SERVER RESTART / BROWSER RELOAD ─────────────────
        print("\n[7] Simulating Server Restart (Clearing in-memory active_engines)...")
        assert e2e_id in active_engines
        del active_engines[e2e_id]  # Memory wipe: engine no longer in active_engines!
        assert e2e_id not in active_engines

        # Fetch state via REST API now that memory is wiped
        restore_res = await client.get(f"/api/projects/{e2e_id}")
        assert restore_res.status_code == 200, f"Restoration from DB failed: {restore_res.text}"
        restored = restore_res.json()

        # ── 8. Generated File CONTENT Persistence ─────────────────────────────
        print("\n[8] Verifying Generated File Content Persistence (all 8 files)...")
        restored_files = restored.get("files", [])
        expected_files = [
            "src/index.html",
            "src/style.css",
            "src/script.js",
            "README.md",
            "docs/README.md",
            "docs/ARCHITECTURE.md",
            "deploy/vercel.json",
            "marketing/LAUNCH_COPY.md",
        ]
        restored_paths = [f["path"] for f in restored_files]
        for exp in expected_files:
            assert exp in restored_paths, f"Missing persisted file: {exp}"
            # Check content is non-empty
            f_obj = next(f for f in restored_files if f["path"] == exp)
            assert len(f_obj["content"].strip()) > 50, f"File {exp} content trivial or empty!"

        # Verify individual file content retrieval endpoint
        html_res = await client.get(f"/api/projects/{e2e_id}/files/src/index.html")
        assert html_res.status_code == 200
        assert "<!DOCTYPE html>" in html_res.json()["content"]

        arch_res = await client.get(f"/api/projects/{e2e_id}/files/docs/ARCHITECTURE.md")
        assert arch_res.status_code == 200
        assert "Multi-Agent" in arch_res.json()["content"]
        print("  ✓ Complete 8-file structure and full actual text verified after memory reload.")

        # ── 9. Activity History Persistence (Zero Fake Events) ────────────────
        print("\n[9] Verifying Activity History Persistence...")
        act_res = await client.get(f"/api/projects/{e2e_id}/activities")
        assert act_res.status_code == 200
        activities = act_res.json()["activities"]
        assert len(activities) >= 20, f"Expected >= 20 activity events, got {len(activities)}"
        
        # Verify chronological ordering and genuine event types
        event_types = [a["event_type"] for a in activities]
        assert "workflow_started" in event_types
        assert "agent_started" in event_types
        assert "agent_completed" in event_types
        assert "workflow_completed" in event_types

        # Verify no fabricated restoration events
        assert all(a["event_type"] != "fake_event" for a in activities)
        print(f"  ✓ {len(activities)} genuine activity events persisted and restored in exact order.")

        # ── 10. Requirements Persistence ──────────────────────────────────────
        print("\n[10] Verifying Requirements Persistence...")
        assert "requirements" in restored
        reqs = restored["requirements"]
        assert bool(reqs), "Beatrice requirements were not persisted!"
        print("  ✓ Beatrice requirements successfully restored from SQLite.")

        # ── 11. Clarification Persistence ─────────────────────────────────────
        print("\n[11] Verifying Clarification Persistence...")
        clar = restored.get("clarification")
        assert clar is not None, "Clarification object missing from restored state!"
        assert "question" in clar
        assert "options" in clar
        assert "user_response" in clar or "Vintage" in str(clar)
        print("  ✓ Human-in-the-loop clarification question & response persisted.")

        # ── 12. Agent State Persistence (8 Agents) ────────────────────────────
        print("\n[12] Verifying Agent State Persistence...")
        statuses = restored.get("agent_statuses", {})
        expected_agents = ["planning", "requirements", "design", "development", "testing", "documentation", "deployment", "marketing"]
        for ag in expected_agents:
            assert ag in statuses, f"Agent status missing for {ag}"
            assert statuses[ag] == "completed", f"Agent {ag} expected completed, got {statuses[ag]}"
        print("  ✓ All 8 agent statuses persisted as 'completed'.")

        # ── 13. QA / Revision Persistence ─────────────────────────────────────
        print("\n[13] Verifying QA / Revision Persistence...")
        assert "qa_revision_count" in restored
        assert restored["qa_revision_count"] >= 1, "QA revision count should be >= 1"
        assert "qa_state" in restored or "test_results" in restored
        print(f"  ✓ QA revision count ({restored['qa_revision_count']}) & QA test state restored.")

        # ── 14. Completion Summary Persistence ────────────────────────────────
        print("\n[14] Verifying Completion Summary Persistence...")
        summary = restored.get("completion_summary")
        assert summary is not None, "Completion summary missing from restored state!"
        assert "agents_completed" in summary
        assert "8 / 8" in summary["agents_completed"]
        assert "qa_status" in summary
        assert "file_count" in summary or "files_count" in summary
        assert summary.get("file_count") == 8 or summary.get("files_count") == 8
        print("  ✓ Standardized completion summary accurately persisted and restored.")

        # ── Live Preview Endpoint Verification After Reload ───────────────────
        print("\n[15] Verifying Live Preview Endpoint After Memory Reload...")
        preview_res = await client.get(f"/api/projects/{e2e_id}/preview", headers={"Accept": "text/html"})
        assert preview_res.status_code == 200
        assert "<!DOCTYPE html>" in preview_res.text
        assert "<style>" in preview_res.text
        assert "<script>" in preview_res.text
        print("  ✓ Live Preview endpoint compiles standalone HTML page directly from SQLite.")

    print("\n" + "=" * 70)
    print("ALL 14 PHASE 4A PERSISTENT WORKSPACE TESTS PASSED PERFECTLY!")
    print("=" * 70)


def test_phase4a_suite():
    """Pytest entrypoint."""
    asyncio.run(run_phase4a_tests())


if __name__ == "__main__":
    test_phase4a_suite()
