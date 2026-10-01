"""
Auctor Systems — Documentation Access & Download Verification Suite
Verifies:
1. docs/README.md and docs/ARCHITECTURE.md are generated with non-empty content
2. Root README.md is generated and matches documentation standards
3. Contents are accessible via ProjectManager.get_file_content()
4. Documentation survives project reload / persistence
5. Project ZIP export contains src/, docs/README.md, docs/ARCHITECTURE.md, deploy/, marketing/
6. FastAPI endpoints (/api/project/{id}/files and /api/project/{id}/files/{path}) serve exact contents
"""

import sys
import asyncio
import zipfile
import shutil
from pathlib import Path
from uuid import uuid4

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.engine import OrchestratorEngine
from services.project_manager import ProjectManager
from services.export_service import ExportService
from main import app
from httpx import AsyncClient, ASGITransport


async def _run_documentation_access_tests():
    print("=" * 60)
    print("TEST: Documentation Access, Export & Persistence Verification")
    print("=" * 60)

    test_id = f"test-doc-{uuid4().hex[:6]}"
    engine = OrchestratorEngine(project_id=test_id)
    events_raw = []

    async def collect_events():
        async for sse_chunk in engine.stream_events():
            events_raw.append(sse_chunk)
            if "workflow_completed" in sse_chunk:
                break

    stream_task = asyncio.create_task(collect_events())

    # Start generation in demo mode (deterministic 8-agent run)
    prompt = "Design a luxury boutique portfolio with interactive case study filtering"
    engine.start(prompt, mode="demo")

    # Step 1: Handle Beatrice's clarification
    clarification_detected = False
    for _ in range(50):
        await asyncio.sleep(0.1)
        if any(e.type == "user_input_required" for e in engine.events_history):
            clarification_detected = True
            break

    assert clarification_detected, "Beatrice failed to pause for user input"
    print("  ✓ Step 1: Beatrice paused for clarification.")

    resumed = engine.provide_user_input("Option 1: Modern Luxury with interactive filters")
    assert resumed is True, "Failed to resume engine with user input"
    print("  ✓ Step 2: Provided user clarification and resumed.")

    # Step 2: Wait for workflow completion
    for _ in range(200):
        await asyncio.sleep(0.1)
        if any(e.type == "workflow_completed" for e in engine.events_history):
            break

    assert any(e.type == "workflow_completed" for e in engine.events_history), "Workflow timed out!"
    print("  ✓ Step 3: Workflow completed successfully.")

    # Step 3: Verify Geneviève's output in context
    context = engine.context
    docs_readme = context.get_file("docs/README.md")
    docs_arch = context.get_file("docs/ARCHITECTURE.md")
    root_readme = context.get_file("README.md")

    assert docs_readme is not None, "docs/README.md not found in context.generated_files"
    assert docs_arch is not None, "docs/ARCHITECTURE.md not found in context.generated_files"
    assert root_readme is not None, "README.md not found in context.generated_files"

    assert len(docs_readme.content.strip()) > 200, "docs/README.md content is empty or trivial"
    assert len(docs_arch.content.strip()) > 200, "docs/ARCHITECTURE.md content is empty or trivial"
    assert len(root_readme.content.strip()) > 200, "root README.md content is empty or trivial"

    # Verify key sections
    assert "## 1. Product Overview" in docs_readme.content
    assert "## 2. Features" in docs_readme.content
    assert "## 8. Testing & QA Certification" in docs_readme.content
    assert "Multi-Agent Provenance Pipeline" in docs_arch.content
    assert "Data & Control Flow" in docs_arch.content
    print("  ✓ Step 4: Context files generated and non-empty with exact documentation sections.")

    # Step 4: Verify ProjectManager file access and disk persistence
    pm = ProjectManager(test_id)
    disk_docs_readme = pm.get_file_content("docs/README.md")
    disk_docs_arch = pm.get_file_content("docs/ARCHITECTURE.md")
    disk_root_readme = pm.get_file_content("README.md")

    assert disk_docs_readme is not None, "pm.get_file_content('docs/README.md') returned None"
    assert disk_docs_arch is not None, "pm.get_file_content('docs/ARCHITECTURE.md') returned None"
    assert disk_root_readme is not None, "pm.get_file_content('README.md') returned None"

    assert disk_docs_readme == docs_readme.content, "docs/README.md content mismatch between context and disk"
    assert disk_docs_arch == docs_arch.content, "docs/ARCHITECTURE.md content mismatch between context and disk"
    print("  ✓ Step 5: Direct file access via ProjectManager validated.")

    # Step 5: Verify Persistence Survival across simulated project reload
    # Create an independent ProjectManager instance without active engine
    pm_reloaded = ProjectManager(test_id)
    state = pm_reloaded.load_state()
    assert state is not None, "Project state failed to load on reload"

    reloaded_files = pm_reloaded.get_all_files()
    reloaded_names = [f.filename for f in reloaded_files]

    assert any("docs/README.md" in name or name == "README.md" for name in reloaded_names), "README.md missing after reload"
    assert any("docs/ARCHITECTURE.md" in name for name in reloaded_names), "docs/ARCHITECTURE.md missing after reload"

    reloaded_readme_content = pm_reloaded.get_file_content("docs/README.md")
    reloaded_arch_content = pm_reloaded.get_file_content("docs/ARCHITECTURE.md")

    assert reloaded_readme_content == docs_readme.content, "README content corrupted after reload"
    assert reloaded_arch_content == docs_arch.content, "ARCHITECTURE content corrupted after reload"
    print("  ✓ Step 6: Documentation survival verified after project reload.")

    # Step 6: Verify ZIP Export includes docs and actual content
    zip_buffer = ExportService.create_zip(pm)
    assert zip_buffer is not None and zip_buffer.getbuffer().nbytes > 500, "ZIP buffer is empty"

    with zipfile.ZipFile(zip_buffer, "r") as zf:
        zip_names = zf.namelist()
        print(f"  ZIP namelist ({len(zip_names)} files): {zip_names}")

        project_prefix = f"auctor-{test_id[:8]}"
        expected_zip_files = [
            f"{project_prefix}/src/index.html",
            f"{project_prefix}/src/style.css",
            f"{project_prefix}/src/script.js",
            f"{project_prefix}/docs/README.md",
            f"{project_prefix}/docs/ARCHITECTURE.md",
            f"{project_prefix}/deploy/vercel.json",
            f"{project_prefix}/marketing/LAUNCH_COPY.md",
            f"{project_prefix}/README.md",
        ]

        for expected in expected_zip_files:
            assert expected in zip_names, f"Expected file '{expected}' missing from project ZIP"

        # Verify actual content inside ZIP
        zip_readme_data = zf.read(f"{project_prefix}/docs/README.md").decode("utf-8")
        zip_arch_data = zf.read(f"{project_prefix}/docs/ARCHITECTURE.md").decode("utf-8")

        assert zip_readme_data == docs_readme.content, "ZIP docs/README.md does not contain exact generated content"
        assert zip_arch_data == docs_arch.content, "ZIP docs/ARCHITECTURE.md does not contain exact generated content"

    print("  ✓ Step 7: Project ZIP export verified with both docs and exact content.")

    # Step 7: Verify REST API endpoints serve documentation
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. /api/project/{id}/files list
        files_res = await client.get(f"/api/project/{test_id}/files")
        assert files_res.status_code == 200, f"/files endpoint returned {files_res.status_code}"
        files_data = files_res.json()
        api_files = files_data.get("files", [])
        api_file_paths = [f.get("path") for f in api_files]

        assert "docs/README.md" in api_file_paths, "docs/README.md missing from /api/project/{id}/files"
        assert "docs/ARCHITECTURE.md" in api_file_paths, "docs/ARCHITECTURE.md missing from /api/project/{id}/files"
        assert "README.md" in api_file_paths, "README.md missing from /api/project/{id}/files"

        # 2. Individual file endpoints
        res_readme = await client.get(f"/api/project/{test_id}/files/docs/README.md")
        assert res_readme.status_code == 200, f"/files/docs/README.md failed: {res_readme.status_code}"
        assert res_readme.json()["content"] == docs_readme.content

        res_arch = await client.get(f"/api/project/{test_id}/files/docs/ARCHITECTURE.md")
        assert res_arch.status_code == 200, f"/files/docs/ARCHITECTURE.md failed: {res_arch.status_code}"
        assert res_arch.json()["content"] == docs_arch.content

        res_root_readme = await client.get(f"/api/project/{test_id}/files/README.md")
        assert res_root_readme.status_code == 200, f"/files/README.md failed: {res_root_readme.status_code}"
        assert res_root_readme.json()["content"] == root_readme.content

    print("  ✓ Step 8: FastAPI documentation endpoints return exact generated content.")

    # Clean up test project
    project_dir = Path(__file__).parent / "projects" / test_id
    shutil.rmtree(project_dir, ignore_errors=True)

    print("=" * 60)
    print("  ✅ PASS: All Documentation Access & Download tests passed!")
    print("=" * 60)


def test_documentation_access_suite():
    asyncio.run(_run_documentation_access_tests())


if __name__ == "__main__":
    test_documentation_access_suite()
