"""
Auctor Systems — Database Persistence Layer (Phase 4A)

SQLite-backed persistent workspace supporting:
- projects: Project metadata, requirements, clarification, QA status, completion summary
- project_files: Generated file contents with relative paths and categories
- project_activities: Complete chronological agent activity stream

Guarantees full project isolation, reload survival, and zero fake events on restoration.
"""

import json
import sqlite3
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from config import DATABASE_PATH

logger = logging.getLogger("auctor.database")


def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_content_sha256(content: str) -> str:
    """
    Computes canonical SHA-256 hex digest for project file content string.
    Exact byte representation: UTF-8 encoding of the string content.
    """
    if content is None:
        content = ""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class Database:
    """Thread-safe SQLite database manager for Auctor persistent workspace."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'idle',
                    mode TEXT NOT NULL DEFAULT 'real',
                    current_agent TEXT,
                    agent_statuses TEXT,
                    requirements TEXT,
                    clarification TEXT,
                    qa_state TEXT,
                    qa_revision_count INTEGER DEFAULT 0,
                    completion_summary TEXT,
                    deployment_status TEXT DEFAULT 'not_configured',
                    deployment_url TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 2. Project files table (stores full content)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'source',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE (project_id, path)
                );
            """)

            # 3. Project activities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
            """)

            # 4. Project revisions table (Phase 4B / 4C)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    revision_number INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    modified_files TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'completed',
                    qa_summary TEXT,
                    snapshot_status TEXT NOT NULL DEFAULT 'LEGACY_UNAVAILABLE',
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE (project_id, revision_number)
                );
            """)

            # Repeatable, idempotent migration: ensure snapshot_status column exists in legacy tables
            cursor.execute("PRAGMA table_info(project_revisions);")
            rev_columns = {row[1] for row in cursor.fetchall()}
            if "snapshot_status" not in rev_columns:
                cursor.execute("""
                    ALTER TABLE project_revisions 
                    ADD COLUMN snapshot_status TEXT NOT NULL DEFAULT 'LEGACY_UNAVAILABLE';
                """)
                logger.info("Migrated project_revisions: added snapshot_status column with LEGACY_UNAVAILABLE default.")

            # 5. Project revision files table (Phase 4C Stage 1 - Immutable Snapshots & SHA-256 Hashes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_revision_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    revision_number INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'source',
                    sha256 TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE (project_id, revision_number, path)
                );
            """)

            # Repeatable, idempotent migration: ensure sha256 column exists in project_revision_files
            cursor.execute("PRAGMA table_info(project_revision_files);")
            rev_file_columns = {row[1] for row in cursor.fetchall()}
            if "sha256" not in rev_file_columns:
                cursor.execute("ALTER TABLE project_revision_files ADD COLUMN sha256 TEXT;")
                logger.info("Migrated project_revision_files: added sha256 column.")

            # Indexes for fast lookup
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_project ON project_files(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_project ON project_activities(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON project_activities(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_revisions_project ON project_revisions(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_files_project_rev ON project_revision_files(project_id, revision_number);")
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    # ── Project CRUD ──────────────────────────────────────────────────────────

    def create_project(
        self,
        project_id: str,
        prompt: str,
        name: str = "Auctor Project",
        description: str = "",
        mode: str = "real",
        status: str = "generating",
        agent_statuses: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new project record or replace if it already exists."""
        now = get_utc_now()
        initial_statuses = agent_statuses or {
            "planning": "idle",
            "requirements": "idle",
            "design": "idle",
            "development": "idle",
            "testing": "idle",
            "documentation": "idle",
            "deployment": "idle",
            "marketing": "idle",
        }

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (
                    id, name, prompt, description, status, mode,
                    current_agent, agent_statuses, requirements, clarification,
                    qa_state, qa_revision_count, completion_summary,
                    deployment_status, deployment_url, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    prompt = excluded.prompt,
                    description = excluded.description,
                    status = excluded.status,
                    mode = excluded.mode,
                    updated_at = excluded.updated_at
            """, (
                project_id,
                name,
                prompt,
                description,
                status,
                mode,
                None,
                json.dumps(initial_statuses),
                json.dumps({}),
                None,
                json.dumps({}),
                0,
                None,
                "not_configured",
                None,
                now,
                now,
            ))
            conn.commit()

        return self.get_project(project_id) or {}

    def update_project(self, project_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update arbitrary project columns dynamically."""
        if not kwargs:
            return self.get_project(project_id)

        allowed_columns = {
            "name", "prompt", "description", "status", "mode",
            "current_agent", "agent_statuses", "requirements",
            "clarification", "qa_state", "qa_revision_count",
            "completion_summary", "deployment_status", "deployment_url",
        }

        updates = []
        params = []
        for key, value in kwargs.items():
            if key in allowed_columns:
                updates.append(f"{key} = ?")
                # Serialize dicts/lists to JSON strings
                if isinstance(value, (dict, list)):
                    params.append(json.dumps(value))
                else:
                    params.append(value)

        if not updates:
            return self.get_project(project_id)

        updates.append("updated_at = ?")
        params.append(get_utc_now())
        params.append(project_id)

        sql = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()

        return self.get_project(project_id)

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID with deserialized JSON columns."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_project_dict(row)

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects sorted by updated_at descending with file/activity counts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.*,
                    (SELECT COUNT(*) FROM project_files WHERE project_id = p.id) AS file_count,
                    (SELECT COUNT(*) FROM project_activities WHERE project_id = p.id) AS activity_count
                FROM projects p
                ORDER BY p.updated_at DESC
            """)
            rows = cursor.fetchall()
            return [self._row_to_project_dict(r) for r in rows]

    def delete_project(self, project_id: str) -> bool:
        """Delete project and all associated files and activities (cascade)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Project {project_id} deleted from database.")
            return deleted

    # ── File Persistence ──────────────────────────────────────────────────────

    def save_file(
        self,
        project_id: str,
        path: str,
        filename: str,
        content: str,
        file_type: str,
        category: str = "source",
    ) -> Dict[str, Any]:
        """Save or update a generated file with full content."""
        clean_path = path.replace("\\", "/").lstrip("/")
        now = get_utc_now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_files (
                    project_id, path, filename, content, file_type, category, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, path) DO UPDATE SET
                    filename = excluded.filename,
                    content = excluded.content,
                    file_type = excluded.file_type,
                    category = excluded.category,
                    updated_at = excluded.updated_at
            """, (project_id, clean_path, filename, content, file_type, category, now, now))
            conn.commit()

        return {
            "project_id": project_id,
            "path": clean_path,
            "filename": filename,
            "content": content,
            "file_type": file_type,
            "category": category,
        }

    def get_files(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all files for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_files WHERE project_id = ? ORDER BY path ASC",
                (project_id,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_file(self, project_id: str, path_or_filename: str) -> Optional[Dict[str, Any]]:
        """Find a file by exact path or filename."""
        clean = path_or_filename.replace("\\", "/").lstrip("/")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Exact path
            cursor.execute(
                "SELECT * FROM project_files WHERE project_id = ? AND path = ?",
                (project_id, clean),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

            # 2. Filename match
            base = clean.split("/")[-1]
            cursor.execute(
                "SELECT * FROM project_files WHERE project_id = ? AND filename = ?",
                (project_id, base),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

            # 3. Suffix match
            cursor.execute(
                "SELECT * FROM project_files WHERE project_id = ? AND path LIKE ?",
                (project_id, f"%/{base}"),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

            return None

    # ── Activity Stream Persistence ───────────────────────────────────────────

    def save_activity(
        self,
        project_id: str,
        event_type: str,
        agent_id: str,
        agent_name: str,
        message: str,
        data: Optional[Any] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record an activity event into the chronological log."""
        ts = timestamp or get_utc_now()
        data_str = json.dumps(data) if data is not None else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_activities (
                    project_id, event_type, agent_id, agent_name, message, data, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, event_type, agent_id, agent_name, message, data_str, ts))
            conn.commit()

        return {
            "project_id": project_id,
            "event_type": event_type,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "message": message,
            "data": data,
            "timestamp": ts,
        }

    def get_activities(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all chronological activity events for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_activities WHERE project_id = ? ORDER BY id ASC",
                (project_id,),
            )
            rows = cursor.fetchall()
            activities = []
            for r in rows:
                item = dict(r)
                if item.get("data"):
                    try:
                        item["data"] = json.loads(item["data"])
                    except Exception:
                        pass
                activities.append(item)
            return activities

    # ── Project Revisions (Phase 4B) ──────────────────────────────────────────

    def add_revision(
        self,
        project_id: str,
        revision_number: int,
        prompt: str,
        modified_files: List[str],
        status: str = "completed",
        qa_summary: Optional[str] = None,
        snapshot_status: str = "VERIFIED_IMMUTABLE",
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a successful or audited revision in SQLite."""
        ts = timestamp or get_utc_now()
        files_json = json.dumps(modified_files)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT snapshot_status FROM project_revisions WHERE project_id = ? AND revision_number = ?",
                (project_id, revision_number),
            )
            existing = cursor.fetchone()
            if existing and existing["snapshot_status"] == "VERIFIED_IMMUTABLE":
                raise ValueError(
                    f"Immutable revision violation: Revision {revision_number} for project {project_id} is already VERIFIED_IMMUTABLE and cannot be modified."
                )

            cursor.execute(
                """
                INSERT INTO project_revisions (
                    project_id, revision_number, prompt, modified_files, status, qa_summary, snapshot_status, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, revision_number) DO UPDATE SET
                    prompt = excluded.prompt,
                    modified_files = excluded.modified_files,
                    status = excluded.status,
                    qa_summary = excluded.qa_summary,
                    snapshot_status = excluded.snapshot_status,
                    timestamp = excluded.timestamp
                """,
                (
                    project_id,
                    revision_number,
                    prompt,
                    files_json,
                    status,
                    qa_summary,
                    snapshot_status,
                    ts,
                ),
            )
            # Also sync revision_count on the project record
            cursor.execute(
                "UPDATE projects SET qa_revision_count = ?, updated_at = ? WHERE id = ?",
                (revision_number, ts, project_id),
            )
            conn.commit()

        return {
            "project_id": project_id,
            "revision_number": revision_number,
            "prompt": prompt,
            "modified_files": modified_files,
            "status": status,
            "qa_summary": qa_summary,
            "snapshot_status": snapshot_status,
            "timestamp": ts,
        }

    def update_revision_status(
        self,
        project_id: str,
        revision_number: int,
        status: str,
    ) -> bool:
        """Update the status of a specific revision (e.g. 'completed' or 'filesystem_desync')."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE project_revisions SET status = ? WHERE project_id = ? AND revision_number = ?",
                (status, project_id, revision_number),
            )
            conn.commit()
            return cursor.rowcount > 0

    def commit_revision_atomic(
        self,
        project_id: str,
        revision_number: int,
        prompt: str,
        files: List[Any],
        modified_files: List[str],
        qa_summary: Optional[str] = None,
        snapshot_status: str = "VERIFIED_IMMUTABLE",
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Atomically commit active files, revision metadata, and immutable snapshot in a single transaction.
        If any step fails or count mismatches, rolls back the entire transaction leaving 0 partial records.
        Protects existing VERIFIED_IMMUTABLE revisions from modification.
        """
        ts = timestamp or get_utc_now()
        files_json = json.dumps(modified_files)

        # Normalize files
        normalized_files = []
        target_paths = []
        for f in files:
            path = getattr(f, "path", None) or (f.get("path") if isinstance(f, dict) else None)
            filename = getattr(f, "filename", None) or (f.get("filename") if isinstance(f, dict) else None) or (path.split("/")[-1] if path else "file.txt")
            content = getattr(f, "content", None) or (f.get("content") if isinstance(f, dict) else "")
            category = getattr(f, "category", None) or (f.get("category") if isinstance(f, dict) else "source")
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
            normalized_files.append({
                "path": path,
                "filename": filename,
                "content": content,
                "file_type": ext,
                "category": category,
            })
            target_paths.append(path)

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")

            # Immutability Protection: prevent overwriting VERIFIED_IMMUTABLE revisions or snapshots
            cursor.execute(
                "SELECT status, snapshot_status FROM project_revisions WHERE project_id = ? AND revision_number = ?",
                (project_id, revision_number),
            )
            existing_rev = cursor.fetchone()
            if existing_rev:
                if existing_rev["snapshot_status"] == "VERIFIED_IMMUTABLE":
                    raise ValueError(
                        f"Immutable revision violation: Revision {revision_number} for project {project_id} is already VERIFIED_IMMUTABLE and cannot be modified."
                    )

            cursor.execute(
                "SELECT COUNT(*) FROM project_revision_files WHERE project_id = ? AND revision_number = ?",
                (project_id, revision_number),
            )
            existing_snapshot_count = cursor.fetchone()[0]
            if existing_snapshot_count > 0:
                raise ValueError(
                    f"Immutable snapshot violation: Project {project_id} Revision {revision_number} already has {existing_snapshot_count} snapshot rows."
                )

            # 1. Exact active files: remove active files absent from the target snapshot
            if target_paths:
                placeholders = ",".join("?" for _ in target_paths)
                cursor.execute(
                    f"DELETE FROM project_files WHERE project_id = ? AND path NOT IN ({placeholders})",
                    [project_id] + target_paths,
                )
            else:
                cursor.execute("DELETE FROM project_files WHERE project_id = ?", (project_id,))

            # Upsert active files
            for nf in normalized_files:
                cursor.execute(
                    """
                    INSERT INTO project_files (
                        project_id, path, filename, content, file_type, category, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, path) DO UPDATE SET
                        content = excluded.content,
                        filename = excluded.filename,
                        file_type = excluded.file_type,
                        category = excluded.category,
                        updated_at = excluded.updated_at
                    """,
                    (
                        project_id,
                        nf["path"],
                        nf["filename"],
                        nf["content"],
                        nf["file_type"],
                        nf["category"],
                        ts,
                        ts,
                    ),
                )

            # 2. Record revision metadata with snapshot_status
            if existing_rev:
                cursor.execute(
                    """
                    UPDATE project_revisions
                    SET prompt = ?, modified_files = ?, status = 'completed', qa_summary = ?, snapshot_status = ?, timestamp = ?
                    WHERE project_id = ? AND revision_number = ?
                    """,
                    (
                        prompt,
                        files_json,
                        qa_summary,
                        snapshot_status,
                        ts,
                        project_id,
                        revision_number,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO project_revisions (
                        project_id, revision_number, prompt, modified_files, status, qa_summary, snapshot_status, timestamp
                    )
                    VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
                    """,
                    (
                        project_id,
                        revision_number,
                        prompt,
                        files_json,
                        qa_summary,
                        snapshot_status,
                        ts,
                    ),
                )

            # 3. Store immutable snapshot in project_revision_files (without deleting historical rows)
            for nf in normalized_files:
                sha256_hash = compute_content_sha256(nf["content"])
                cursor.execute(
                    """
                    INSERT INTO project_revision_files (
                        project_id, revision_number, path, filename, content, file_type, category, sha256, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        revision_number,
                        nf["path"],
                        nf["filename"],
                        nf["content"],
                        nf["file_type"],
                        nf["category"],
                        sha256_hash,
                        ts,
                    ),
                )

            # Integrity check: verify snapshot row count matches file count
            cursor.execute(
                "SELECT COUNT(*) FROM project_revision_files WHERE project_id = ? AND revision_number = ?",
                (project_id, revision_number),
            )
            count = cursor.fetchone()[0]
            if count != len(normalized_files):
                raise ValueError(f"Snapshot integrity failure: expected {len(normalized_files)} files, wrote {count}")

            # 4. Sync revision count in projects table (preserve non-zero qa_revision_count for Rev 0)
            if revision_number > 0:
                cursor.execute(
                    "UPDATE projects SET qa_revision_count = ?, updated_at = ? WHERE id = ?",
                    (revision_number, ts, project_id),
                )
            else:
                cursor.execute(
                    "UPDATE projects SET updated_at = ? WHERE id = ?",
                    (ts, project_id),
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back for project {project_id} (Rev {revision_number}): {e}")
            raise e
        finally:
            conn.close()

    def record_failure_diagnostic(
        self,
        project_id: str,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a failure diagnostic in a separate, independent transaction.
        Guaranteed to persist even when the main revision transaction was rolled back.
        """
        try:
            ts = get_utc_now()
            data_str = json.dumps(data) if data is not None else None
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO project_activities (
                        project_id, event_type, agent_id, agent_name, message, data, timestamp
                    ) VALUES (?, ?, 'orchestrator', 'Auctor Studio', ?, ?, ?)
                    """,
                    (project_id, event_type, message, data_str, ts),
                )
                conn.commit()
        except Exception as e:
            logger.critical(f"Failed to record independent failure diagnostic for {project_id}: {e}")

    def get_revision(self, project_id: str, revision_number: int) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a specific revision."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_revisions WHERE project_id = ? AND revision_number = ?",
                (project_id, revision_number),
            )
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get("modified_files"):
                try:
                    item["modified_files"] = json.loads(item["modified_files"])
                except Exception:
                    item["modified_files"] = []
            return item

    def get_revision_snapshot(self, project_id: str, revision_number: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve all file snapshots for a verified revision."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_revision_files WHERE project_id = ? AND revision_number = ? ORDER BY path ASC",
                (project_id, revision_number),
            )
            rows = cursor.fetchall()
            if not rows:
                return None
            return [dict(r) for r in rows]

    def verify_snapshot_integrity(
        self, project_id: str, revision_number: int
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]], List[str]]:
        """
        Verify the cryptographic SHA-256 and structural integrity of an immutable snapshot.
        Returns:
            (is_valid: bool, snapshot_files: Optional[List[Dict[str, Any]]], errors: List[str])

        Enforces:
        - Revision record must exist in project_revisions.
        - snapshot_status must be 'VERIFIED_IMMUTABLE'.
        - If snapshot_status is 'LEGACY_UNAVAILABLE', rejects with legacy diagnostic without fabricating hashes.
        - Must contain at least one snapshot file row.
        - For every file row:
            * Content must be non-null.
            * If sha256 is present, computed hash must strictly match stored sha256.
            * If sha256 is missing (legacy unhashed snapshot row), flags that content lacks cryptographic verification.
        """
        rev = self.get_revision(project_id, revision_number)
        if not rev:
            return False, None, [f"Revision {revision_number} not found for project {project_id}"]

        if rev.get("snapshot_status") != "VERIFIED_IMMUTABLE":
            status_val = rev.get("snapshot_status", "LEGACY_UNAVAILABLE")
            return False, None, [
                f"Revision {revision_number} snapshot_status is '{status_val}'. Only VERIFIED_IMMUTABLE snapshots can be restored."
            ]

        snapshot_rows = self.get_revision_snapshot(project_id, revision_number)
        if not snapshot_rows:
            return False, None, [f"No snapshot files recorded for Revision {revision_number}"]

        errors = []
        verified_files = []

        for row in snapshot_rows:
            path = row.get("path")
            content = row.get("content")
            stored_sha = row.get("sha256")

            if content is None:
                errors.append(f"Snapshot file '{path}' has NULL content.")
                continue

            if not stored_sha:
                errors.append(f"Snapshot file '{path}' lacks cryptographic SHA-256 hash (legacy unhashed snapshot).")
                continue

            computed_sha = compute_content_sha256(content)
            if computed_sha != stored_sha:
                errors.append(
                    f"Cryptographic SHA-256 hash mismatch for '{path}' (Rev {revision_number}): stored {stored_sha}, computed {computed_sha}"
                )
                continue

            verified_files.append(row)

        if errors:
            return False, None, errors

        return True, verified_files, []

    def get_revisions(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all revision history items for a project in ascending order."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_revisions WHERE project_id = ? ORDER BY revision_number ASC",
                (project_id,),
            )
            rows = cursor.fetchall()
            revisions = []
            for r in rows:
                item = dict(r)
                if item.get("modified_files"):
                    try:
                        item["modified_files"] = json.loads(item["modified_files"])
                    except Exception:
                        item["modified_files"] = []
                revisions.append(item)
            return revisions

    # ── Complete State Restoration ────────────────────────────────────────────

    def get_complete_project_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Assemble the complete, persisted project state ready for frontend restoration.
        Includes metadata, agent statuses, requirements, clarification, QA status,
        full files, activity history, revisions, and completion summary.
        """
        project = self.get_project(project_id)
        if not project:
            return None

        files = self.get_files(project_id)
        activities = self.get_activities(project_id)
        revisions = self.get_revisions(project_id)

        # Build output dictionary mapping agent names to text if available
        outputs = {}
        for a in activities:
            if a.get("event_type") == "agent_completed" and a.get("message"):
                outputs[a.get("agent_id", "")] = a.get("message")

        state = {
            "project": project,
            "project_id": project["id"],
            "id": project["id"],
            "prompt": project["prompt"],
            "project_name": project["name"],
            "name": project["name"],
            "project_description": project["description"],
            "status": project["status"],
            "current_agent": project["current_agent"],
            "execution_mode": project["mode"],
            "mode": project["mode"],
            "agent_statuses": project.get("agent_statuses") or {},
            "requirements": project.get("requirements") or {},
            "clarification": project.get("clarification"),
            "qa_state": project.get("qa_state") or {},
            "qa_revision_count": project.get("qa_revision_count", 0),
            "revision_count": project.get("qa_revision_count", 0),
            "revisions": revisions,
            "completion_summary": project.get("completion_summary"),
            "deployment_status": project.get("deployment_status", "not_configured"),
            "deployment_url": project.get("deployment_url"),
            "created_at": project["created_at"],
            "updated_at": project["updated_at"],
            "files": [
                {
                    "path": f["path"],
                    "filename": f["filename"],
                    "content": f["content"],
                    "file_type": f["file_type"],
                    "category": f["category"],
                }
                for f in files
            ],
            "activities": activities,
            "outputs": outputs,
        }
        return state

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _row_to_project_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a project row to a dictionary, deserializing JSON fields."""
        d = dict(row)
        for json_col in [
            "agent_statuses",
            "requirements",
            "clarification",
            "qa_state",
            "completion_summary",
        ]:
            if d.get(json_col) and isinstance(d[json_col], str):
                try:
                    d[json_col] = json.loads(d[json_col])
                except Exception:
                    pass
        return d


# Singleton instance
db = Database()
