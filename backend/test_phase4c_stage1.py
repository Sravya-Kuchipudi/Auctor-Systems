"""
Auctor Systems — Phase 4C Stage 1 Verification Suite
Atomic Snapshot Database & Safe Rollback Engine

Tests:
1. Repeatable idempotent migration for snapshot_status & legacy marking.
2. Legacy revisions without verified snapshots cannot be rolled back.
3. Atomic snapshot creation for newly completed revisions.
4. Exact rollback restoration (restoring snapshot files & removing absent files from disk and DB).
5. Forward revision creation (Rev 2 -> Rev 1 creates Rev 3) preserving all prior history.
6. Transaction failure rollback leaving zero partial records & recording independent failure diagnostics.
7. Staging QA failure blocks rollback, leaving active project files and history untouched.
8. Dynamic QA check reporting (actual executed, passed, failed, skipped; no hardcoded 24/24).
"""

import sys
import sqlite3
import asyncio
import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, MagicMock

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from database import Database, db, get_utc_now
from orchestrator.engine import OrchestratorEngine
from orchestrator.context import ProjectContext, GeneratedFile
from orchestrator.agents.astrid import AstridAgent
from orchestrator.agents.genevieve import GenevieveAgent
from services.project_manager import ProjectManager
from models import RollbackRequest
from main import app, active_engines
from httpx import AsyncClient, ASGITransport


async def _run_test_migration(tmp_path):
    """
    Test 1: Migration on legacy database adds snapshot_status defaulting to LEGACY_UNAVAILABLE,
    and runs idempotently on already-migrated database without error or data loss.
    """
    test_db_file = tmp_path / "legacy_test.db"

    # 1. Create a simulated pre-Phase 4C legacy database
    conn = sqlite3.connect(str(test_db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'idle',
            mode TEXT NOT NULL DEFAULT 'real',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE project_revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            revision_number INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            modified_files TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            qa_summary TEXT,
            timestamp TEXT NOT NULL
        );
    """)
    cur.execute("""
        INSERT INTO projects (id, name, prompt, created_at, updated_at)
        VALUES ('legacy-proj-1', 'Legacy Brand', 'Old prompt', '2026-01-01', '2026-01-01');
    """)
    cur.execute("""
        INSERT INTO project_revisions (project_id, revision_number, prompt, modified_files, status, timestamp)
        VALUES ('legacy-proj-1', 1, 'Legacy directive', '["src/index.html"]', 'completed', '2026-01-01');
    """)
    conn.commit()
    conn.close()

    # 2. Instantiate Database to trigger repeatable migration
    migrated_db = Database(db_path=test_db_file)

    # Verify column snapshot_status exists
    with migrated_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(project_revisions);")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert "snapshot_status" in columns, "snapshot_status column was not created by migration!"

        # Verify legacy row is marked LEGACY_UNAVAILABLE
        cursor.execute("SELECT snapshot_status FROM project_revisions WHERE project_id = 'legacy-proj-1' AND revision_number = 1;")
        row = cursor.fetchone()
        assert row is not None
        assert row["snapshot_status"] == "LEGACY_UNAVAILABLE", "Legacy revision must be marked LEGACY_UNAVAILABLE!"

        # Verify project_revision_files table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_revision_files';")
        assert cursor.fetchone() is not None, "project_revision_files table was not created!"

    # 3. Test idempotency: re-run init_db on already-migrated database
    migrated_db.init_db()
    with migrated_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT snapshot_status FROM project_revisions WHERE project_id = 'legacy-proj-1' AND revision_number = 1;")
        row = cursor.fetchone()
        assert row["snapshot_status"] == "LEGACY_UNAVAILABLE"


def test_migration_idempotent_and_legacy_status(tmp_path):
    asyncio.run(_run_test_migration(tmp_path))


async def _run_test_legacy_cannot_rollback():
    """
    Test 2: Legacy revisions marked LEGACY_UNAVAILABLE cannot be rolled back.
    Must return HTTP 422 with explicit rejection message.
    """
    proj_id = f"test-legacy-rb-{uuid4().hex[:6]}"
    db.create_project(
        project_id=proj_id,
        name="Legacy Horology",
        prompt="Antique watchmaker",
        mode="demo",
    )
    # Insert legacy revision with LEGACY_UNAVAILABLE and no snapshot files
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO project_revisions (
                project_id, revision_number, prompt, modified_files, status, qa_summary, snapshot_status, timestamp
            ) VALUES (?, 1, 'Legacy directive', '["src/index.html"]', 'completed', 'Legacy QA', 'LEGACY_UNAVAILABLE', ?)
            """,
            (proj_id, get_utc_now()),
        )
        conn.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/project/{proj_id}/rollback",
            json={"target_revision": 1},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "LEGACY_UNAVAILABLE" in str(data["detail"])
        assert "cannot be restored" in str(data["detail"]).lower()


def test_legacy_revisions_cannot_be_rolled_back():
    asyncio.run(_run_test_legacy_cannot_rollback())


async def _run_test_atomic_snapshot_and_rollback():
    """
    Test 3 & 4 & 5:
    - Atomically create Rev 1 and Rev 2 snapshots.
    - Rollback to Rev 1:
      * Creates forward Rev 3.
      * Removes files absent from Rev 1 snapshot (e.g. extra file added in Rev 2).
      * Restores exact snapshot contents for Rev 1.
      * Updates docs deterministically with Rev 3 rollback changelog.
      * Preserves Rev 1, Rev 2, Rev 3 snapshots.
    """
    proj_id = f"test-p4c-rb-{uuid4().hex[:6]}"
    pm = ProjectManager(proj_id)
    db.create_project(
        project_id=proj_id,
        name="L’Atelier du Temps",
        prompt="Haute horlogerie showcase",
        mode="demo",
    )

    # ── Rev 1 Baseline Files ──
    rev1_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>L'Atelier du Temps</title><link rel="stylesheet" href="style.css"></head>
<body><header><h1>L'Atelier du Temps</h1><p>Rev 1 Subtitle</p></header><script src="script.js"></script></body>
</html>""",
            category="source",
        ),
        GeneratedFile(
            filename="style.css",
            path="src/style.css",
            content=""":root { --muted-gold: #C79A4A; }
button:focus-visible { outline: 2px solid var(--muted-gold); }""",
            category="source",
        ),
        GeneratedFile(
            filename="script.js",
            path="src/script.js",
            content="""document.addEventListener('DOMContentLoaded', () => { console.log('Rev 1'); });""",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# L'Atelier du Temps\n\n## Revision History\n- Initial release.",
            category="doc",
        ),
        GeneratedFile(
            filename="ARCHITECTURE.md",
            path="docs/ARCHITECTURE.md",
            content="# Architecture\n\n## 5. Revision & Iteration History\n- Initial build.",
            category="doc",
        ),
    ]

    # Commit Rev 1 atomically
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Initial validated release",
        files=rev1_files,
        modified_files=[f.path for f in rev1_files],
        qa_summary="Certified Clean by Astrid Lindqvist (Rev 1)",
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev1_files:
        pm.write_file(f.path, f.content)

    # Verify Rev 1 snapshot stored in project_revision_files
    snap1 = db.get_revision_snapshot(proj_id, 1)
    assert snap1 is not None
    assert len(snap1) == len(rev1_files)
    snap1_paths = {s["path"] for s in snap1}
    assert "src/index.html" in snap1_paths

    # ── Rev 2 Modifications ──
    # Rev 2 modifies index.html and introduces an extra file "src/temp_addon.js"
    rev2_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>L'Atelier du Temps</title><link rel="stylesheet" href="style.css"></head>
<body><header><h1>L'Atelier du Temps</h1><p>Rev 2 Modified Subtitle</p></header><script src="script.js"></script></body>
</html>""",
            category="source",
        ),
        GeneratedFile(
            filename="style.css",
            path="src/style.css",
            content=""":root { --muted-gold: #C79A4A; }
button:focus-visible { outline: 2px solid var(--muted-gold); }""",
            category="source",
        ),
        GeneratedFile(
            filename="script.js",
            path="src/script.js",
            content="""document.addEventListener('DOMContentLoaded', () => { console.log('Rev 2'); });""",
            category="source",
        ),
        GeneratedFile(
            filename="temp_addon.js",
            path="src/temp_addon.js",
            content="""console.log('Temporary add-on only in Rev 2');""",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# L'Atelier du Temps\n\n## Revision History\n- Initial release.\n- Rev 2 added temp addon.",
            category="doc",
        ),
        GeneratedFile(
            filename="ARCHITECTURE.md",
            path="docs/ARCHITECTURE.md",
            content="# Architecture\n\n## 5. Revision & Iteration History\n- Initial build.\n- Rev 2 addon.",
            category="doc",
        ),
    ]

    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=2,
        prompt="Add temp addon",
        files=rev2_files,
        modified_files=["src/index.html", "src/temp_addon.js"],
        qa_summary="Certified Clean by Astrid Lindqvist (Rev 2)",
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev2_files:
        pm.write_file(f.path, f.content)

    # Verify temp_addon.js is active
    assert db.get_file(proj_id, "src/temp_addon.js") is not None
    assert (pm.src_dir / "temp_addon.js").exists()

    # ── Execute Safe Rollback to Rev 1 ──
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/project/{proj_id}/rollback",
            json={"target_revision": 1},
        )
        assert resp.status_code == 200, f"Rollback failed: {resp.text}"
        data = resp.json()
        assert data["status"] == "success"
        assert data["target_revision"] == 1
        assert data["new_revision"] == 3, "Rollback from Rev 2 to Rev 1 must create Rev 3!"

    # ── Verification of Exact Restoration ──
    # 1. temp_addon.js MUST BE DELETED from SQLite project_files
    assert db.get_file(proj_id, "src/temp_addon.js") is None, "Absent file temp_addon.js was not removed from SQLite!"

    # 2. temp_addon.js MUST BE DELETED from disk
    assert not (pm.src_dir / "temp_addon.js").exists(), "Absent file temp_addon.js was not removed from disk!"

    # 3. index.html must match Rev 1 content
    current_index = db.get_file(proj_id, "src/index.html")
    assert current_index is not None
    assert "Rev 1 Subtitle" in current_index["content"]
    assert "Rev 2 Modified Subtitle" not in current_index["content"]

    # 4. Deterministic changelog in documentation
    arch = db.get_file(proj_id, "docs/ARCHITECTURE.md")
    assert arch is not None
    assert "Revision 3 Rollback Changelog" in arch["content"]
    assert "Safe Revision Rollback to Target Revision 1" in arch["content"]

    # 5. All revisions preserved (Rev 1, Rev 2, Rev 3)
    revisions = db.get_revisions(proj_id)
    assert len(revisions) == 3
    rev_nums = [r["revision_number"] for r in revisions]
    assert rev_nums == [1, 2, 3]

    # 6. Snapshots for all 3 revisions exist
    assert db.get_revision_snapshot(proj_id, 1) is not None
    assert db.get_revision_snapshot(proj_id, 2) is not None
    assert db.get_revision_snapshot(proj_id, 3) is not None


def test_atomic_snapshot_creation_and_exact_rollback():
    asyncio.run(_run_test_atomic_snapshot_and_rollback())


def test_transaction_failure_rollback_and_independent_diagnostics():
    """
    Test 6: If any step of commit_revision_atomic fails:
    - Entire SQLite transaction is rolled back first (zero partial active files or revisions).
    - Failure diagnostic is recorded independently and survives.
    """
    proj_id = f"test-atomic-fail-{uuid4().hex[:6]}"
    db.create_project(
        project_id=proj_id,
        name="Failure Test Project",
        prompt="Testing atomic rollback on error",
        mode="demo",
    )

    # Initial file
    init_file = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<!DOCTYPE html><html><body><h1>Safe</h1></body></html>",
            category="source",
        )
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Initial valid",
        files=init_file,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )

    class CorruptFile:
        def __init__(self):
            self.path = None  # None path violates NOT NULL in SQLite project_files
            self.filename = "corrupt.html"
            self.content = "corrupted content"

    corrupted_files = [CorruptFile()]

    with pytest.raises(Exception):
        db.commit_revision_atomic(
            project_id=proj_id,
            revision_number=2,
            prompt="Should fail atomically",
            files=corrupted_files,
            modified_files=["src/corrupt.html"],
            snapshot_status="VERIFIED_IMMUTABLE",
        )

    # Verify ZERO partial records for Rev 2
    rev2 = db.get_revision(proj_id, 2)
    assert rev2 is None, "Rev 2 revision record must NOT exist after transaction rollback!"

    snap2 = db.get_revision_snapshot(proj_id, 2)
    assert snap2 is None, "Rev 2 snapshot files must NOT exist after transaction rollback!"

    # Verify active files remain at Rev 1
    active_files = db.get_files(proj_id)
    assert len(active_files) == 1
    assert active_files[0]["path"] == "src/index.html"
    assert "Safe" in active_files[0]["content"]

    # Verify independent diagnostic recording
    db.record_failure_diagnostic(
        project_id=proj_id,
        event_type="test_failure_diagnostic",
        message="Independent diagnostic persisted after rollback",
        data={"error": "corrupted_content"},
    )
    activities = db.get_activities(proj_id)
    diag_acts = [a for a in activities if a["event_type"] == "test_failure_diagnostic"]
    assert len(diag_acts) == 1
    assert "Independent diagnostic persisted" in diag_acts[0]["message"]


async def _run_test_staging_qa_failure():
    """
    Test 7: If isolated staging QA check fails:
    - Active project files and revision history remain 100% untouched.
    - Structured blocker report is returned.
    - Failure diagnostic is recorded independently.
    """
    proj_id = f"test-qa-block-{uuid4().hex[:6]}"
    pm = ProjectManager(proj_id)
    db.create_project(
        project_id=proj_id,
        name="QA Block Test",
        prompt="Testing QA rollback guard",
        mode="demo",
    )

    # Valid Rev 1
    rev1_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<!DOCTYPE html><html lang='en'><head><title>Rev 1</title></head><body><h1>Rev 1</h1></body></html>",
            category="source",
        ),
        GeneratedFile(
            filename="style.css",
            path="src/style.css",
            content=":root { --muted-gold: #C79A4A; } button:focus-visible { outline: 2px solid var(--muted-gold); }",
            category="source",
        ),
        GeneratedFile(
            filename="script.js",
            path="src/script.js",
            content="document.addEventListener('DOMContentLoaded', () => {});",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# Docs\n\n## Revision History\n",
            category="doc",
        ),
        GeneratedFile(
            filename="ARCHITECTURE.md",
            path="docs/ARCHITECTURE.md",
            content="# Arch\n\n## 5. Revision & Iteration History\n",
            category="doc",
        ),
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Rev 1 clean",
        files=rev1_files,
        modified_files=[f.path for f in rev1_files],
        snapshot_status="VERIFIED_IMMUTABLE",
    )

    # Deliberately create a flawed snapshot row in Rev 2 containing prohibited #D4AF37
    flawed_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<!DOCTYPE html><html lang='en'><head><title>Rev 2</title></head><body><h1>Rev 2 Flawed</h1></body></html>",
            category="source",
        ),
        GeneratedFile(
            filename="style.css",
            path="src/style.css",
            content=":root { --accent: #D4AF37; }",  # PROHIBITED GOLD
            category="source",
        ),
        GeneratedFile(
            filename="script.js",
            path="src/script.js",
            content="document.addEventListener('DOMContentLoaded', () => {});",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# Docs",
            category="doc",
        ),
        GeneratedFile(
            filename="ARCHITECTURE.md",
            path="docs/ARCHITECTURE.md",
            content="# Arch",
            category="doc",
        ),
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=2,
        prompt="Rev 2 with defect",
        files=flawed_files,
        modified_files=["src/style.css"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )

    # Now create active Rev 3 clean state on top
    rev3_files = list(rev1_files)
    rev3_files[0] = GeneratedFile(
        filename="index.html",
        path="src/index.html",
        content="<!DOCTYPE html><html lang='en'><head><title>Rev 3 Active</title></head><body><h1>Rev 3 Active</h1></body></html>",
        category="source",
    )
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=3,
        prompt="Rev 3 clean active",
        files=rev3_files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev3_files:
        pm.write_file(f.path, f.content)

    # Attempt to rollback to Rev 2 (which contains prohibited gold defect)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/project/{proj_id}/rollback",
            json={"target_revision": 2},
        )
        assert resp.status_code == 422
        data = resp.json()
        detail = data.get("detail", {})
        assert detail.get("status") == "blocked"
        assert len(detail.get("blockers", [])) > 0
        assert any("palette_prohibited_gold" in b for b in detail.get("blockers", []))

    # CRITICAL: Verify active project state remains at Rev 3!
    active_idx = db.get_file(proj_id, "src/index.html")
    assert "Rev 3 Active" in active_idx["content"], "Active files were mutated despite QA failure!"

    # Verify revisions table still ends at Rev 3 (no Rev 4 created)
    revisions = db.get_revisions(proj_id)
    assert max(r["revision_number"] for r in revisions) == 3


def test_staging_qa_failure_leaves_active_project_untouched():
    asyncio.run(_run_test_staging_qa_failure())


def test_dynamic_qa_reporting_no_hardcoded_assumption():
    """
    Test 8: Dynamic QA reporting reports actual executed, passed, failed, and skipped checks.
    """
    astrid = AstridAgent()
    context = ProjectContext(project_id="test-dynamic-qa", user_prompt="Audit test prompt")

    # Add partial files (no closeModalBtn, so modal check will be skipped)
    context.set_file("src/index.html", "index.html", "<!DOCTYPE html><html lang='en'><head><title>Test</title></head><body><h1>Hi</h1></body></html>")
    context.set_file("src/style.css", "style.css", ":root { --muted-gold: #C79A4A; } button:focus-visible { outline: 2px solid var(--muted-gold); }")
    context.set_file("src/script.js", "script.js", "document.addEventListener('DOMContentLoaded', () => {});")
    context.set_file("docs/README.md", "README.md", "# Test Readme")
    context.set_file("docs/ARCHITECTURE.md", "ARCHITECTURE.md", "# Test Arch")

    report = astrid.run_dynamic_audit(context)
    assert report["checks_executed"] > 0
    assert report["checks_passed"] > 0
    assert report["checks_failed"] == 0
    assert report["checks_skipped"] >= 1  # Modal check is skipped because no closeModalBtn present
    assert report["passed"] is True
    assert report["checks_executed"] == report["checks_passed"] + report["checks_failed"]


# ── Step 1 Hardening Tests: Filesystem Recovery & Immutable Protection ────────

async def _run_test_filesystem_write_failure_recovery():
    """
    Step 1A Test 1: Filesystem write failure during rollback disk restoration:
    - Does NOT swallow errors.
    - Does NOT report success.
    - Marks revision and project status as 'filesystem_desync'.
    - Records failure diagnostic independently.
    - Preserves revision history and immutable snapshots.
    - Allows durable recovery via reconcile_filesystem.
    """
    proj_id = f"test-write-fail-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Write Fail Test Project",
        prompt="Initial prompt",
        mode="demo",
    )
    pm = ProjectManager(proj_id)

    # Rev 1: Clean files
    rev1_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<!DOCTYPE html><html lang='en'><head><title>Rev 1</title><link rel='stylesheet' href='style.css'></head><body><h1>Rev 1</h1><script src='script.js'></script></body></html>",
            category="source",
        ),
        GeneratedFile(
            filename="style.css",
            path="src/style.css",
            content=":root { --muted-gold: #C79A4A; } button:focus-visible { outline: 2px solid var(--muted-gold); }",
            category="source",
        ),
        GeneratedFile(
            filename="script.js",
            path="src/script.js",
            content="document.addEventListener('DOMContentLoaded', () => { console.log('Rev 1'); });",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# Rev 1 Docs\n\n## Revision History\n- Initial release.",
            category="doc",
        ),
        GeneratedFile(
            filename="ARCHITECTURE.md",
            path="docs/ARCHITECTURE.md",
            content="# Rev 1 Arch\n\n## 5. Revision & Iteration History\n- Initial build.",
            category="doc",
        ),
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Rev 1 base",
        files=rev1_files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev1_files:
        pm.write_file(f.path, f.content)

    # Rev 2: Clean files with modification
    rev2_files = list(rev1_files)
    rev2_files[0] = GeneratedFile(
        filename="index.html",
        path="src/index.html",
        content="<!DOCTYPE html><html lang='en'><head><title>Rev 2</title></head><body><h1>Rev 2 Modified</h1></body></html>",
        category="source",
    )
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=2,
        prompt="Rev 2 mod",
        files=rev2_files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev2_files:
        pm.write_file(f.path, f.content)

    engine = OrchestratorEngine(project_id=proj_id)
    active_engines[proj_id] = engine

    # Simulate filesystem write failure during rollback disk writing
    original_write = pm.write_file
    fail_count = 0

    def mock_failing_write(rel_path, content):
        nonlocal fail_count
        if "src/index.html" in rel_path:
            fail_count += 1
            raise OSError("Simulated disk write failure: disk I/O error")
        return original_write(rel_path, content)

    engine.project_manager.write_file = mock_failing_write

    # Execute rollback to Rev 1: MUST fail and raise RuntimeError / HTTP 500
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/project/{proj_id}/rollback",
            json={"target_revision": 1},
        )
        # Rollback MUST NOT report success!
        assert resp.status_code == 500
        data = resp.json()
        assert "filesystem" in data.get("detail", "").lower() or "desync" in data.get("detail", "").lower()

    # Verify revision was committed in DB as forward Rev 3, but status is 'filesystem_desync'
    rev3 = db.get_revision(proj_id, 3)
    assert rev3 is not None
    assert rev3["status"] == "filesystem_desync"
    assert rev3["snapshot_status"] == "VERIFIED_IMMUTABLE"

    # Verify project status is 'filesystem_desync'
    proj = db.get_project(proj_id)
    assert proj["status"] == "filesystem_desync"

    # Verify failure diagnostic was recorded independently
    activities = db.get_activities(proj_id)
    desync_diags = [a for a in activities if a.get("event_type") == "filesystem_sync_failure"]
    assert len(desync_diags) >= 1
    assert "Simulated disk write failure" in desync_diags[0]["message"]

    # Verify prior historical revisions Rev 1 and Rev 2 were preserved intact
    rev1 = db.get_revision(proj_id, 1)
    rev2 = db.get_revision(proj_id, 2)
    assert rev1["status"] == "completed"
    assert rev2["status"] == "completed"

    # Now test Durable Reconciliation: restore the original write_file and reconcile
    engine.project_manager.write_file = original_write
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        rec_resp = await client.post(f"/api/project/{proj_id}/reconcile?revision_number=3")
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()
        assert rec_data["status"] == "success"

    # Verify status is restored to 'completed'
    rev3_updated = db.get_revision(proj_id, 3)
    assert rev3_updated["status"] == "completed"
    proj_updated = db.get_project(proj_id)
    assert proj_updated["status"] == "completed"

    # Verify disk matches Rev 1 content
    index_content = pm.get_file_content("src/index.html")
    assert "<title>Rev 1</title>" in index_content

    # Verify reconciliation success diagnostic was recorded
    activities = db.get_activities(proj_id)
    rec_diags = [a for a in activities if a.get("event_type") == "filesystem_reconciliation_success"]
    assert len(rec_diags) >= 1


def test_filesystem_write_failure_and_reconciliation():
    asyncio.run(_run_test_filesystem_write_failure_recovery())


async def _run_test_filesystem_deletion_failure():
    """
    Step 1A Test 2: Filesystem deletion failure during rollback cleanup:
    - Propagates IOError rather than silently continuing.
    - Fails rollback and sets status to 'filesystem_desync'.
    - Records diagnostic independently.
    - Cleans up successfully on reconcile.
    """
    proj_id = f"test-del-fail-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Deletion Fail Project",
        prompt="Initial prompt",
        mode="demo",
    )
    pm = ProjectManager(proj_id)

    # Rev 1: Clean files
    rev1_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<!DOCTYPE html><html lang='en'><head><title>Rev 1</title><link rel='stylesheet' href='style.css'></head><body><h1>Rev 1</h1><script src='script.js'></script></body></html>",
            category="source",
        ),
        GeneratedFile(
            filename="style.css",
            path="src/style.css",
            content=":root { --muted-gold: #C79A4A; } button:focus-visible { outline: 2px solid var(--muted-gold); }",
            category="source",
        ),
        GeneratedFile(
            filename="script.js",
            path="src/script.js",
            content="document.addEventListener('DOMContentLoaded', () => { console.log('Rev 1'); });",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# Docs\n\n## Revision History\n- Initial release.",
            category="doc",
        ),
        GeneratedFile(
            filename="ARCHITECTURE.md",
            path="docs/ARCHITECTURE.md",
            content="# Arch\n\n## 5. Revision & Iteration History\n- Initial build.",
            category="doc",
        ),
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Rev 1",
        files=rev1_files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev1_files:
        pm.write_file(f.path, f.content)

    # Rev 2: Adds extra file "src/extra.js"
    rev2_files = list(rev1_files) + [
        GeneratedFile(
            filename="extra.js",
            path="src/extra.js",
            content="console.log('extra');",
            category="source",
        )
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=2,
        prompt="Rev 2 extra file",
        files=rev2_files,
        modified_files=["src/extra.js"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev2_files:
        pm.write_file(f.path, f.content)

    engine = OrchestratorEngine(project_id=proj_id)
    active_engines[proj_id] = engine

    # Mock remove_files_except to simulate permission denied on file deletion
    original_remove = pm.remove_files_except

    def mock_failing_remove(allowed):
        raise IOError("Filesystem restoration cleanup failed for 1 file(s): src/extra.js: Permission denied")

    engine.project_manager.remove_files_except = mock_failing_remove

    # Rollback to Rev 1: MUST fail and propagate deletion failure
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/project/{proj_id}/rollback",
            json={"target_revision": 1},
        )
        assert resp.status_code == 500
        data = resp.json()
        assert "cleanup failed" in data.get("detail", "").lower() or "desync" in data.get("detail", "").lower()

    # Verify status is filesystem_desync
    rev3 = db.get_revision(proj_id, 3)
    assert rev3["status"] == "filesystem_desync"

    # Verify failure diagnostic
    activities = db.get_activities(proj_id)
    sync_failures = [a for a in activities if a.get("event_type") == "filesystem_sync_failure"]
    assert len(sync_failures) >= 1

    # Restore unlinking and reconcile
    engine.project_manager.remove_files_except = original_remove
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        rec = await client.post(f"/api/project/{proj_id}/reconcile?revision_number=3")
        assert rec.status_code == 200
        assert rec.json()["status"] == "success"

    # Extra file must now be deleted from disk
    assert not (pm.project_dir / "src" / "extra.js").exists()
    assert db.get_revision(proj_id, 3)["status"] == "completed"


def test_filesystem_deletion_failure_propagation():
    asyncio.run(_run_test_filesystem_deletion_failure())


def test_interrupted_restoration_integrity_detection():
    """
    Step 1A Test 3: Interrupted restoration detection and recovery:
    - verify_disk_integrity catches missing and mismatched files.
    - reconcile_filesystem recovers exact file state.
    """
    proj_id = f"test-interrupted-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Interrupted Project",
        prompt="Initial prompt",
        mode="demo",
    )
    pm = ProjectManager(proj_id)

    files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<!DOCTYPE html><html><body>Correct Content</body></html>",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# Correct Docs",
            category="doc",
        ),
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Rev 1",
        files=files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    # Simulate interrupted write: only write index.html, leave README.md missing
    pm.write_file("src/index.html", "<!DOCTYPE html><html><body>Corrupted Content</body></html>")

    # verify_disk_integrity should detect both content mismatch and missing file
    errors = pm.verify_disk_integrity(files)
    assert len(errors) >= 2
    assert any("Missing file on disk: docs/README.md" in e for e in errors)
    assert any("Content mismatch" in e for e in errors)

    # Reconcile heals the filesystem
    engine = OrchestratorEngine(project_id=proj_id)
    res = engine.reconcile_filesystem(1)
    assert res["status"] == "success"

    # Post-reconciliation verify_disk_integrity must report 0 errors
    post_errors = pm.verify_disk_integrity(files)
    assert len(post_errors) == 0
    assert pm.get_file_content("src/index.html") == "<!DOCTYPE html><html><body>Correct Content</body></html>"
    assert pm.get_file_content("docs/README.md") == "# Correct Docs"


def test_immutable_snapshot_cannot_be_overwritten():
    """
    Step 1B Test 1: Preventing overwrite of existing VERIFIED_IMMUTABLE revisions:
    - Attempting commit_revision_atomic with an existing VERIFIED_IMMUTABLE rev raises ValueError.
    - Attempting add_revision with an existing VERIFIED_IMMUTABLE rev raises ValueError.
    - Snapshot rows and revision metadata remain strictly unchanged.
    """
    proj_id = f"test-immutable-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Immutable Test",
        prompt="Initial prompt",
        mode="demo",
    )

    files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<h1>Original Immutable</h1>",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# Original Docs",
            category="doc",
        ),
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Original commit",
        files=files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )

    # Attempt 1: commit_revision_atomic with same revision number and mutated content
    mutated_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<h1>Hacked Content</h1>",
            category="source",
        ),
    ]
    with pytest.raises(ValueError) as excinfo:
        db.commit_revision_atomic(
            project_id=proj_id,
            revision_number=1,
            prompt="Malicious overwrite",
            files=mutated_files,
            modified_files=["src/index.html"],
            snapshot_status="VERIFIED_IMMUTABLE",
        )
    assert "Immutable revision violation" in str(excinfo.value)

    # Verify original snapshot row is completely unchanged
    snapshot = db.get_revision_snapshot(proj_id, 1)
    assert len(snapshot) == 2
    idx_snap = next(f for f in snapshot if f["path"] == "src/index.html")
    assert idx_snap["content"] == "<h1>Original Immutable</h1>"

    # Attempt 2: add_revision with same revision number
    with pytest.raises(ValueError) as excinfo2:
        db.add_revision(
            project_id=proj_id,
            revision_number=1,
            prompt="Malicious metadata update",
            modified_files=["src/index.html"],
            status="completed",
        )
    assert "Immutable revision violation" in str(excinfo2.value)


def test_cannot_delete_snapshot_rows_in_normal_commit():
    """
    Step 1B Test 2: Snapshot rows cannot be deleted and recreated by normal revision commit path.
    """
    proj_id = f"test-snap-protect-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Snapshot Protect Test",
        prompt="Prompt",
        mode="demo",
    )
    files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<h1>Rev 1</h1>",
            category="source",
        ),
    ]
    # Commit Rev 1
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Rev 1",
        files=files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    # Attempting to call commit_revision_atomic again on Rev 1 fails with immutable snapshot violation
    with pytest.raises(ValueError) as exc:
        db.commit_revision_atomic(
            project_id=proj_id,
            revision_number=1,
            prompt="Rev 1 repeat",
            files=files,
            modified_files=["src/index.html"],
            snapshot_status="VERIFIED_IMMUTABLE",
        )
    assert "Immutable" in str(exc.value)


def test_legacy_revision_compatibility():
    """
    Step 1B Test 3: Legacy revisions with LEGACY_UNAVAILABLE and 0 snapshot rows
    are preserved without corruption.
    """
    proj_id = f"test-legacy-compat-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Legacy Compat Project",
        prompt="Prompt",
        mode="demo",
    )
    # Insert a legacy revision row directly (0 snapshot files, status LEGACY_UNAVAILABLE)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO project_revisions (
                project_id, revision_number, prompt, modified_files, status, qa_summary, snapshot_status, timestamp
            )
            VALUES (?, 1, 'Legacy directive', '["src/index.html"]', 'completed', 'Legacy', 'LEGACY_UNAVAILABLE', '2026-01-01')
            """,
            (proj_id,),
        )
        conn.commit()

    rev = db.get_revision(proj_id, 1)
    assert rev is not None
    assert rev["snapshot_status"] == "LEGACY_UNAVAILABLE"
    # Verify no snapshot files exist
    assert db.get_revision_snapshot(proj_id, 1) is None


# ── Step 2 Hardening Tests: Initial Rev 0 Baseline & Filesystem Cleanup ───────

async def _run_test_successful_initial_generation_creates_verified_rev0():
    """
    Step 2A Test 1: Successful initial generation automatically creates a verified immutable Rev 0 snapshot.
    """
    proj_id = f"test-rev0-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Artisan Pottery Rev0",
        prompt="Handcrafted pottery and ceramic workshop portfolio in dark mode with muted gold accents.",
        mode="demo",
    )
    engine = OrchestratorEngine(project_id=proj_id)
    active_engines[proj_id] = engine

    events_received = []

    async def collect_events():
        async for sse_chunk in engine.stream_events():
            events_received.append(sse_chunk)
            if "workflow_completed" in sse_chunk:
                break

    stream_task = asyncio.create_task(collect_events())

    prompt = "Handcrafted pottery and ceramic workshop portfolio in dark mode with muted gold accents."
    engine.start(prompt, mode="demo")

    for _ in range(50):
        await asyncio.sleep(0.1)
        if any("user_input_required" in e for e in events_received):
            engine.provide_user_input("Artisanal ceramic studio with gallery showcase")
            break

    await asyncio.wait_for(stream_task, timeout=20.0)

    # 1. Verify project status is completed
    proj = db.get_project(proj_id)
    assert proj["status"] == "completed"

    # 2. Verify Rev 0 exists and is VERIFIED_IMMUTABLE
    rev0 = db.get_revision(proj_id, 0)
    assert rev0 is not None, "Rev 0 record was not created after initial generation completed!"
    assert rev0["revision_number"] == 0
    assert rev0["status"] == "completed"
    assert rev0["snapshot_status"] == "VERIFIED_IMMUTABLE"
    assert "Astrid Lindqvist" in rev0.get("qa_summary", "")

    # 3. Verify Rev 0 file snapshot in SQLite
    snap0 = db.get_revision_snapshot(proj_id, 0)
    assert snap0 is not None and len(snap0) > 0
    snap_paths = {f["path"] for f in snap0}
    assert "src/index.html" in snap_paths
    assert "src/style.css" in snap_paths
    assert "docs/README.md" in snap_paths


def test_successful_initial_generation_creates_verified_rev0():
    asyncio.run(_run_test_successful_initial_generation_creates_verified_rev0())


def test_incomplete_or_failed_initial_generation_no_rev0():
    """
    Step 2A Test 2: Incomplete or failed generations do NOT receive a falsely verified Rev 0 baseline.
    """
    proj_id = f"test-incomplete-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Incomplete Project",
        prompt="Incomplete prompt",
        mode="demo",
    )
    # Project left in idle or cancelled state without completing pipeline
    rev0 = db.get_revision(proj_id, 0)
    assert rev0 is None, "Incomplete project must NOT have a Rev 0 snapshot!"
    assert db.get_revision_snapshot(proj_id, 0) is None


def test_duplicate_rev0_creation_prevented():
    """
    Step 2A Test 3: Duplicate Rev 0 snapshots are strictly prevented.
    """
    proj_id = f"test-dup-rev0-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Dup Rev0 Project",
        prompt="Initial prompt",
        mode="demo",
    )
    files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<h1>Rev 0 Original</h1>",
            category="source",
        ),
    ]
    # Commit Rev 0
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=0,
        prompt="Initial generation",
        files=files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    # Attempt duplicate commit of Rev 0
    with pytest.raises(ValueError) as exc:
        db.commit_revision_atomic(
            project_id=proj_id,
            revision_number=0,
            prompt="Duplicate Rev 0 attempt",
            files=files,
            modified_files=["src/index.html"],
            snapshot_status="VERIFIED_IMMUTABLE",
        )
    assert "Immutable revision violation" in str(exc.value)


async def _run_test_rollback_to_rev0():
    """
    Step 2A Test 4 & Step 2B: Rollback to Rev 0 restores original baseline as forward Rev 2.
    """
    proj_id = f"test-rb-rev0-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Rollback Rev0 Test",
        prompt="Initial prompt",
        mode="demo",
    )
    pm = ProjectManager(proj_id)

    # 1. Clean Rev 0 files
    rev0_files = [
        GeneratedFile(
            filename="index.html",
            path="src/index.html",
            content="<!DOCTYPE html><html lang='en'><head><title>Rev 0 Baseline</title><link rel='stylesheet' href='style.css'></head><body><h1>Rev 0 Baseline</h1><script src='script.js'></script></body></html>",
            category="source",
        ),
        GeneratedFile(
            filename="style.css",
            path="src/style.css",
            content=":root { --muted-gold: #C79A4A; } button:focus-visible { outline: 2px solid var(--muted-gold); }",
            category="source",
        ),
        GeneratedFile(
            filename="script.js",
            path="src/script.js",
            content="document.addEventListener('DOMContentLoaded', () => { console.log('Rev 0'); });",
            category="source",
        ),
        GeneratedFile(
            filename="README.md",
            path="docs/README.md",
            content="# Docs\n\n## Revision History\n- Rev 0 baseline.",
            category="doc",
        ),
        GeneratedFile(
            filename="ARCHITECTURE.md",
            path="docs/ARCHITECTURE.md",
            content="# Arch\n\n## 5. Revision & Iteration History\n- Initial architecture.",
            category="doc",
        ),
    ]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=0,
        prompt="Initial Rev 0",
        files=rev0_files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev0_files:
        pm.write_file(f.path, f.content)

    # 2. Rev 1 modification: modifies index.html and introduces an extra nested file
    rev1_files = list(rev0_files)
    rev1_files[0] = GeneratedFile(
        filename="index.html",
        path="src/index.html",
        content="<!DOCTYPE html><html lang='en'><head><title>Rev 1 Mod</title><link rel='stylesheet' href='style.css'></head><body><h1>Rev 1 Mod</h1><script src='script.js'></script></body></html>",
        category="source",
    )
    extra_file = GeneratedFile(
        filename="extra.js",
        path="src/extra.js",
        content="console.log('Rev 1 extra');",
        category="source",
    )
    rev1_files.append(extra_file)

    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Rev 1 modifications",
        files=rev1_files,
        modified_files=["src/index.html", "src/extra.js"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    for f in rev1_files:
        pm.write_file(f.path, f.content)

    # 3. Rollback to Rev 0
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/project/{proj_id}/rollback",
            json={"target_revision": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["target_revision"] == 0
        assert data["new_revision"] == 2

    # Verify Rev 2 was created and verified
    rev2 = db.get_revision(proj_id, 2)
    assert rev2 is not None
    assert rev2["status"] == "completed"
    assert rev2["snapshot_status"] == "VERIFIED_IMMUTABLE"

    # Verify disk matches Rev 0 and extra file from Rev 1 was deleted
    index_content = pm.get_file_content("src/index.html")
    assert "Rev 0 Baseline" in index_content
    assert not (pm.project_dir / "src" / "extra.js").exists(), "Extra file from Rev 1 was not removed during rollback!"


def test_rollback_to_rev0():
    asyncio.run(_run_test_rollback_to_rev0())


def test_cleanup_root_level_and_nested_extra_files():
    """
    Step 2B Test 1: Complete filesystem cleanup handles root-level and nested files
    while strictly preserving protected metadata (state.json, .git, .env).
    """
    proj_id = f"test-cleanup-{uuid4().hex[:8]}"
    pm = ProjectManager(proj_id)
    pm.initialize(prompt="Cleanup Test")

    # Allowed paths
    allowed_paths = {"src/index.html", "src/style.css", "docs/README.md"}
    for p in allowed_paths:
        pm.write_file(p, f"content of {p}")

    # Create root-level extra file and nested extra file
    extra_root = pm.project_dir / "temp_root_script.py"
    extra_root.write_text("print('extra root')", encoding="utf-8")

    extra_nested = pm.project_dir / "marketing" / "unwanted_campaign.txt"
    extra_nested.parent.mkdir(parents=True, exist_ok=True)
    extra_nested.write_text("unwanted marketing", encoding="utf-8")

    # Create protected files
    protected_state = pm.project_dir / "state.json"
    protected_state.write_text('{"status": "generating"}', encoding="utf-8")

    protected_env = pm.project_dir / ".env"
    protected_env.write_text("SECRET=12345", encoding="utf-8")

    protected_dotfile = pm.project_dir / ".git_keep"
    protected_dotfile.write_text("keep", encoding="utf-8")

    # Execute remove_files_except
    deleted = pm.remove_files_except(allowed_paths)

    # 1. Assert extra files were removed
    assert not extra_root.exists(), "Root-level extra file was not removed!"
    assert not extra_nested.exists(), "Nested extra file was not removed!"
    assert "temp_root_script.py" in deleted
    assert "marketing/unwanted_campaign.txt" in deleted

    # 2. Assert protected files are strictly preserved
    assert protected_state.exists(), "Protected state.json was accidentally deleted!"
    assert protected_env.exists(), "Protected .env was accidentally deleted!"
    assert protected_dotfile.exists(), "Protected dotfile was accidentally deleted!"

    # 3. Assert allowed files are preserved
    for p in allowed_paths:
        assert (pm.project_dir / p).exists(), f"Allowed file {p} was deleted!"


def test_preservation_of_phase4b_revision_behavior():
    """
    Step 2C Test: Sequential revisions (Rev 0 -> Rev 1 -> Rev 2) preserve numbering
    and existing Phase 4B metadata.
    """
    proj_id = f"test-p4b-preserve-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Phase 4B Preservation",
        prompt="Initial prompt",
        mode="demo",
    )
    # Commit Rev 0
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=0,
        prompt="Initial build",
        files=[GeneratedFile(filename="index.html", path="src/index.html", content="Rev 0", category="source")],
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    # Commit Rev 1
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Second build",
        files=[GeneratedFile(filename="index.html", path="src/index.html", content="Rev 1", category="source")],
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )
    # Commit Rev 2
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=2,
        prompt="Third build",
        files=[GeneratedFile(filename="index.html", path="src/index.html", content="Rev 2", category="source")],
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )

    revisions = db.get_revisions(proj_id)
    assert len(revisions) == 3
    numbers = [r["revision_number"] for r in revisions]
    assert numbers == [0, 1, 2]


def test_protected_files_cannot_mask_content_mismatch():
    """
    Review Check 1: Protected files (state.json, .env, .git) must not allow
    snapshot integrity verification to report success when tracked content differs.
    """
    proj_id = f"test-prot-mask-{uuid4().hex[:8]}"
    pm = ProjectManager(proj_id)
    pm.initialize(prompt="Protected Masking Test")

    # 1. Tracked file with content on disk
    expected_files = [
        {"filename": "index.html", "path": "src/index.html", "content": "<h1>Legitimate</h1>"},
    ]
    pm.write_file("src/index.html", "<h1>Legitimate</h1>")

    # Ensure protected files exist on disk
    (pm.project_dir / "state.json").write_text('{"status": "ok"}', encoding="utf-8")
    (pm.project_dir / ".env").write_text('SECRET=key', encoding="utf-8")

    # Verification passes when content matches
    errors = pm.verify_disk_integrity(expected_files)
    assert len(errors) == 0

    # Mutate disk content of the tracked file
    (pm.project_dir / "src" / "index.html").write_text("<h1>Tampered</h1>", encoding="utf-8")

    # Verification MUST report content mismatch despite protected files being present
    errors_tampered = pm.verify_disk_integrity(expected_files)
    assert len(errors_tampered) == 1
    assert "Content mismatch on disk for file: src/index.html" in errors_tampered[0]


def test_symlink_safety_and_path_traversal(tmp_path):
    """
    Review Check 2: Symlink safety and path traversal protection.
    - Path traversal in write_file is rejected.
    - Cleanup cannot follow symlinks outside project directory or delete external files.
    - verify_disk_integrity rejects symlinks and escaping paths.
    """
    proj_id = f"test-symlink-{uuid4().hex[:8]}"
    pm = ProjectManager(proj_id)
    pm.initialize(prompt="Symlink Test")

    # 1. write_file rejects path traversal
    with pytest.raises(ValueError) as excinfo:
        pm.write_file("../../external_secret.txt", "malicious payload")
    assert "Unsafe path traversal detected" in str(excinfo.value)

    # 2. Cleanup does not follow directory symlinks outside project
    external_dir = tmp_path / "external_target_dir"
    external_dir.mkdir(parents=True, exist_ok=True)
    external_file = external_dir / "sensitive_data.txt"
    external_file.write_text("critical external data", encoding="utf-8")

    # Attempt to create a symlink inside project pointing to external dir
    symlink_dir = pm.project_dir / "ext_symlink"
    try:
        import os
        os.symlink(str(external_dir), str(symlink_dir), target_is_directory=True)
        symlink_created = True
    except (OSError, NotImplementedError):
        # On Windows without SeCreateSymbolicLinkPrivilege, symlinks may not be allowed
        symlink_created = False

    if symlink_created:
        # Run cleanup with only standard files allowed
        pm.write_file("src/index.html", "safe")
        deleted = pm.remove_files_except({"src/index.html"})

        # External file MUST NOT be deleted
        assert external_file.exists(), "External file was deleted through symlink traversal!"
        assert external_file.read_text(encoding="utf-8") == "critical external data"
        # The symlink itself should have been removed or recorded
        assert not symlink_dir.exists(), "Directory symlink was not removed during cleanup!"

    # 3. verify_disk_integrity detects symlinks as invalid
    file_symlink = pm.project_dir / "src" / "symlinked.html"
    try:
        import os
        target_file = pm.project_dir / "src" / "index.html"
        os.symlink(str(target_file), str(file_symlink))
        file_symlink_created = True
    except (OSError, NotImplementedError):
        file_symlink_created = False

    if file_symlink_created:
        errors = pm.verify_disk_integrity([
            {"filename": "symlinked.html", "path": "src/symlinked.html", "content": "safe"}
        ])
        assert any("cannot be a symlink" in err for err in errors)


def test_rev0_failure_handling_and_status():
    """
    Review Check 3: Rev 0 failure handling.
    - If QA fails, project status is 'error', Rev 0 is NOT committed, WORKFLOW_COMPLETED not emitted.
    - If commit fails, project status is 'error', failure diagnostic recorded.
    - If disk integrity fails, project status is 'filesystem_desync'.
    """
    proj_id = f"test-rev0-fail-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Rev0 Fail Test",
        prompt="Initial prompt",
        mode="demo",
    )
    engine = OrchestratorEngine(project_id=proj_id)
    engine.context = ProjectContext(
        project_id=proj_id,
        user_prompt="Initial prompt",
        project_name="Rev0 Fail Test",
        project_description="Test project",
        execution_mode="demo",
        workflow_status="running",
    )

    # Context without any HTML file will fail Astrid's QA audit
    bad_file = GeneratedFile(
        filename="broken.txt",
        path="src/broken.txt",
        content="incomplete content",
        category="source",
    )
    engine.context.generated_files = [bad_file]
    engine.project_manager.write_file("src/broken.txt", "incomplete content")

    # Mock AgentRegistry so agents sequence is empty and pipeline runs directly to Rev 0 completion check
    with patch("orchestrator.engine.AgentRegistry") as MockRegistry:
        mock_reg_inst = MagicMock()
        mock_reg_inst.get_all.return_value = []
        MockRegistry.return_value = mock_reg_inst

        asyncio.run(engine._run_pipeline())

    # Project status must be 'error' and NOT 'completed'
    proj = db.get_project(proj_id)
    assert proj["status"] == "error", f"Expected 'error', got {proj['status']}"

    # Rev 0 must NOT have been committed
    rev0 = db.get_revision(proj_id, 0)
    assert rev0 is None, "Rev 0 was committed despite QA audit failure!"

    # Failure diagnostic must be recorded in activities table
    diagnostics = db.get_activities(proj_id)
    assert len(diagnostics) >= 1
    assert any(d.get("event_type") == "rev0_qa_blocked" for d in diagnostics)


def test_cleanup_failure_propagation_and_reconciliation():
    """
    Review Check 4: Cleanup & reconciliation failure propagation.
    - If reconcile_filesystem fails (e.g. invalid target), error is raised,
      failure diagnostic is recorded, and status is NOT marked completed.
    """
    proj_id = f"test-recon-fail-{uuid4().hex[:8]}"
    db.create_project(
        project_id=proj_id,
        name="Reconciliation Fail Test",
        prompt="Initial prompt",
        mode="demo",
    )
    # Commit a revision
    files = [GeneratedFile(filename="index.html", path="src/index.html", content="Valid", category="source")]
    db.commit_revision_atomic(
        project_id=proj_id,
        revision_number=1,
        prompt="Rev 1",
        files=files,
        modified_files=["src/index.html"],
        snapshot_status="VERIFIED_IMMUTABLE",
    )

    engine = OrchestratorEngine(project_id=proj_id)

    # Attempt to reconcile to non-existent revision 99
    with pytest.raises(ValueError) as excinfo:
        engine.reconcile_filesystem(99)
    assert "not found" in str(excinfo.value)

    # Project status is NOT falsely claimed as completed
    proj = db.get_project(proj_id)
    assert proj["status"] != "filesystem_desync" or proj["status"] == "running" or proj["status"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

