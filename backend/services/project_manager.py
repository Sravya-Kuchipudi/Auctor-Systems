"""
Auctor Systems — Project Manager Service

Manages generated project files on disk.
Handles parsing agent outputs (===FILE: format), writing files,
reading project state, and serving file content.
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Set, Any, Dict
from datetime import datetime, timezone

from config import PROJECTS_DIR
from models import ProjectFile, ProjectState, ProjectStatus, DeploymentStatus, AgentName

logger = logging.getLogger("auctor.project_manager")


class ProjectManager:
    """Manages the lifecycle of generated project files on disk."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project_dir = PROJECTS_DIR / project_id
        self.src_dir = self.project_dir / "src"
        self.docs_dir = self.project_dir / "docs"
        self.marketing_dir = self.project_dir / "marketing"
        self.deploy_dir = self.project_dir / "deploy"
        self.state_file = self.project_dir / "state.json"

    def initialize(self, prompt: str) -> ProjectState:
        """Create the project directory structure and initial state."""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.src_dir.mkdir(exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)
        self.marketing_dir.mkdir(exist_ok=True)
        self.deploy_dir.mkdir(exist_ok=True)

        state = ProjectState(
            project_id=self.project_id,
            status=ProjectStatus.GENERATING,
            prompt=prompt,
        )
        self._save_state(state)
        logger.info(f"Project initialized: {self.project_id}")
        return state

    def parse_and_save_files(self, agent_name: str, raw_output: str) -> list[ProjectFile]:
        """
        Parse an agent's raw output for ===FILE: filename=== delimited files
        and save them to the appropriate directory.
        
        Returns list of ProjectFile objects for the saved files.
        """
        files = self._extract_files(raw_output)

        if not files:
            # No structured files found — save raw output as a text file
            fallback_name = f"{agent_name.lower()}_output.md"
            target_dir = self._get_dir_for_agent(agent_name)
            file_path = target_dir / fallback_name
            file_path.write_text(raw_output, encoding="utf-8")
            return [ProjectFile(
                filename=fallback_name,
                content=raw_output,
                file_type="md",
            )]

        saved_files = []
        for filename, content in files:
            target_dir = self._get_dir_for_file(filename, agent_name)
            file_path = target_dir / filename
            file_path.write_text(content, encoding="utf-8")

            file_type = filename.rsplit(".", 1)[-1] if "." in filename else "txt"
            saved_files.append(ProjectFile(
                filename=filename,
                content=content,
                file_type=file_type,
            ))
            logger.info(f"Saved file: {file_path}")

        return saved_files

    def get_source_files(self) -> list[ProjectFile]:
        """Get all source files (HTML/CSS/JS) from the src directory."""
        files = []
        if self.src_dir.exists():
            for file_path in sorted(self.src_dir.rglob("*")):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        file_type = file_path.suffix.lstrip(".")
                        files.append(ProjectFile(
                            filename=file_path.name,
                            content=content,
                            file_type=file_type,
                        ))
                    except Exception as e:
                        logger.warning(f"Could not read file {file_path}: {e}")
        return files

    def get_all_files(self) -> list[ProjectFile]:
        """Get all project files across all directories and project root."""
        files = []
        # Include root files like README.md (excluding state.json)
        if self.project_dir.exists():
            for root_file in sorted(self.project_dir.iterdir()):
                if root_file.is_file() and root_file.name != "state.json":
                    try:
                        content = root_file.read_text(encoding="utf-8")
                        file_type = root_file.suffix.lstrip(".")
                        files.append(ProjectFile(
                            filename=root_file.name,
                            content=content,
                            file_type=file_type,
                        ))
                    except Exception as e:
                        logger.warning(f"Could not read root file {root_file}: {e}")

        for subdir in [self.src_dir, self.docs_dir, self.marketing_dir, self.deploy_dir]:
            if subdir.exists():
                for file_path in sorted(subdir.rglob("*")):
                    if file_path.is_file():
                        try:
                            content = file_path.read_text(encoding="utf-8")
                            rel_path = file_path.relative_to(self.project_dir)
                            file_type = file_path.suffix.lstrip(".")
                            files.append(ProjectFile(
                                filename=str(rel_path).replace("\\", "/"),
                                content=content,
                                file_type=file_type,
                            ))
                        except Exception as e:
                            logger.warning(f"Could not read file {file_path}: {e}")
        return files

    def _is_safe_path(self, target: Path) -> bool:
        """Verify that resolved target path is strictly within the project directory."""
        try:
            target.resolve().relative_to(self.project_dir.resolve())
            return True
        except (ValueError, RuntimeError):
            return False

    def write_file(self, rel_path: str, content: str) -> Path:
        """
        Write a file directly by relative path (e.g. 'src/index.html').
        Guards against directory traversal and refuses to write through symlinks.
        """
        clean_path = rel_path.replace("\\", "/").lstrip("/")
        target = self.project_dir / clean_path

        # Verify target does not escape project directory
        if not self._is_safe_path(target):
            raise ValueError(f"Unsafe path traversal detected: {rel_path} escapes project directory {self.project_dir}")

        # Guard against writing through existing symlinks
        if target.is_symlink():
            target.unlink()

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info(f"Directly wrote file: {target}")
        return target

    PROTECTED_ROOT_FILES: Set[str] = {"state.json", ".git", ".env"}

    def _is_protected_file(self, rel_path: str) -> bool:
        """Check if relative path refers to protected system metadata or system files."""
        clean = rel_path.replace("\\", "/").lstrip("/")
        parts = clean.split("/")
        if clean in self.PROTECTED_ROOT_FILES or parts[0] in self.PROTECTED_ROOT_FILES:
            return True
        for part in parts:
            if part.startswith(".") and part != "." and part != "..":
                return True
        return False

    def remove_files_except(self, allowed_rel_paths: Set[str]) -> List[str]:
        """
        Removes any files under project_dir whose relative path (normalized with forward slashes)
        is NOT present in allowed_rel_paths.
        Covers both root-level files and nested files across all subdirectories.
        Preserves state.json, dotfiles, and system metadata.
        Guarantees symlink safety: directory symlinks are never followed, and file symlinks
        are unlinked without deleting external target contents.
        Returns list of deleted relative paths.
        Raises IOError if any absent files could not be removed.
        """
        deleted: List[str] = []
        failed_deletions: List[str] = []
        normalized_allowed = {p.replace("\\", "/").lstrip("/") for p in allowed_rel_paths}

        if not self.project_dir.exists():
            return deleted

        # 1. Root-level files and symlinks
        for root_item in list(self.project_dir.iterdir()):
            if root_item.is_file() or root_item.is_symlink():
                rel = root_item.name
                if self._is_protected_file(rel):
                    continue
                if rel not in normalized_allowed:
                    try:
                        # unlink removes the file or the symlink itself without following it
                        root_item.unlink()
                        deleted.append(rel)
                        logger.info(f"Exact restoration removed absent root file/symlink from disk: {rel}")
                    except Exception as e:
                        logger.error(f"Failed to remove absent root item {root_item}: {e}")
                        failed_deletions.append(f"{rel}: {str(e)}")

        # 2. Nested files across tracked and untracked non-hidden subdirectories
        for item in list(self.project_dir.iterdir()):
            if item.name.startswith("."):
                continue

            # If a top-level directory item is a symlink, DO NOT traverse it with rglob!
            # Unlink the symlink itself if not allowed
            if item.is_symlink():
                if item.name not in normalized_allowed and not self._is_protected_file(item.name):
                    try:
                        item.unlink()
                        deleted.append(item.name)
                        logger.info(f"Exact restoration removed absent directory symlink: {item.name}")
                    except Exception as e:
                        failed_deletions.append(f"{item.name}: {str(e)}")
                continue

            if item.is_dir():
                for file_path in list(item.rglob("*")):
                    # If any intermediate path or file is a symlink, do not follow it
                    if file_path.is_symlink():
                        rel = str(file_path.relative_to(self.project_dir)).replace("\\", "/")
                        if not self._is_protected_file(rel) and rel not in normalized_allowed:
                            try:
                                file_path.unlink()
                                deleted.append(rel)
                                logger.info(f"Exact restoration removed nested symlink: {rel}")
                            except Exception as e:
                                failed_deletions.append(f"{rel}: {str(e)}")
                        continue

                    if file_path.is_file():
                        # Verify file does not escape project directory via nested links
                        if not self._is_safe_path(file_path):
                            continue
                        rel = str(file_path.relative_to(self.project_dir)).replace("\\", "/")
                        if self._is_protected_file(rel):
                            continue
                        if rel not in normalized_allowed:
                            try:
                                file_path.unlink()
                                deleted.append(rel)
                                logger.info(f"Exact restoration removed absent nested file from disk: {rel}")
                            except Exception as e:
                                logger.error(f"Failed to remove absent nested file {file_path}: {e}")
                                failed_deletions.append(f"{rel}: {str(e)}")

        if failed_deletions:
            raise IOError(f"Filesystem restoration cleanup failed for {len(failed_deletions)} file(s): {', '.join(failed_deletions)}")
        return deleted

    def verify_disk_integrity(self, expected_files: List[Any]) -> List[str]:
        """
        Verify that all expected files exist on disk with the exact expected content,
        and that no unexpected files exist in root or tracked subdirectories.
        Guarantees:
        - Tracked files are verified unconditionally (protection cannot mask content mismatch).
        - Expected files cannot be symlinks or escape project directory.
        - Directory symlinks are never followed.
        Returns a list of error descriptions (empty if 100% verified).
        """
        errors = []
        expected_map = {}
        for f in expected_files:
            p = getattr(f, "path", None) or (f.get("path") if isinstance(f, dict) else None)
            c = getattr(f, "content", None) or (f.get("content") if isinstance(f, dict) else "")
            if p:
                clean_p = p.replace("\\", "/").lstrip("/")
                expected_map[clean_p] = c

        # 1. Check all expected files exist, match content, and are regular safe files
        for clean_p, exp_content in expected_map.items():
            disk_file = self.project_dir / clean_p
            if not self._is_safe_path(disk_file):
                errors.append(f"Expected file path escapes project directory: {clean_p}")
                continue

            if disk_file.is_symlink():
                errors.append(f"Expected file cannot be a symlink: {clean_p}")
            elif not disk_file.exists():
                errors.append(f"Missing file on disk: {clean_p}")
            elif not disk_file.is_file():
                errors.append(f"Expected file is not a regular file: {clean_p}")
            else:
                try:
                    actual_content = disk_file.read_text(encoding="utf-8")
                    if actual_content != exp_content:
                        errors.append(f"Content mismatch on disk for file: {clean_p}")
                except Exception as e:
                    errors.append(f"Failed to read file {clean_p}: {e}")

        # 2. Check no unexpected root-level files or symlinks exist
        if self.project_dir.exists():
            for root_item in self.project_dir.iterdir():
                if root_item.is_file() or root_item.is_symlink():
                    rel = root_item.name
                    if not self._is_protected_file(rel) and rel not in expected_map:
                        errors.append(f"Unexpected root file on disk: {rel}")

        # 3. Check no unexpected nested files or symlinks exist in subdirectories
        if self.project_dir.exists():
            for item in self.project_dir.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_symlink():
                    errors.append(f"Unexpected directory symlink on disk: {item.name}")
                    continue
                if item.is_dir():
                    for file_path in item.rglob("*"):
                        if file_path.is_symlink() or file_path.is_file():
                            if not self._is_safe_path(file_path):
                                errors.append(f"File path escapes project directory: {file_path}")
                                continue
                            rel = str(file_path.relative_to(self.project_dir)).replace("\\", "/")
                            if not self._is_protected_file(rel) and rel not in expected_map:
                                errors.append(f"Unexpected file on disk: {rel}")

        return errors

    def get_file_content(self, filename: str) -> Optional[str]:
        """Get content of a specific file by relative path or name."""
        clean_name = filename.replace("\\", "/").lstrip("/")

        # 1. Direct path check under project_dir (e.g. docs/README.md or README.md)
        direct = self.project_dir / clean_name
        if direct.exists() and direct.is_file():
            return direct.read_text(encoding="utf-8")

        # 2. Search across all subdirectories by basename
        base_name = clean_name.split("/")[-1]
        for subdir in [self.src_dir, self.docs_dir, self.marketing_dir, self.deploy_dir]:
            file_path = subdir / base_name
            if file_path.exists() and file_path.is_file():
                return file_path.read_text(encoding="utf-8")
        return None

    def update_state(self, **kwargs) -> ProjectState:
        """Update and save project state."""
        state = self.load_state()
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        state.update_timestamp()
        self._save_state(state)
        return state

    def load_state(self) -> ProjectState:
        """Load project state from disk."""
        if self.state_file.exists():
            import json
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            return ProjectState(**data)
        return ProjectState(project_id=self.project_id)

    def _save_state(self, state: ProjectState):
        """Save project state to disk."""
        import json
        self.state_file.write_text(
            json.dumps(state.model_dump(), default=str, indent=2),
            encoding="utf-8",
        )

    def _extract_files(self, text: str) -> list[tuple[str, str]]:
        """
        Extract files from ===FILE: filename=== ... ===END_FILE=== blocks.
        Returns list of (filename, content) tuples.
        """
        pattern = r"===FILE:\s*(.+?)\s*===\s*\n(.*?)===END_FILE==="
        matches = re.findall(pattern, text, re.DOTALL)

        files = []
        for filename, content in matches:
            # Clean up the filename and content
            filename = filename.strip()
            content = content.strip()

            # Remove any markdown code block markers that the LLM might add
            if content.startswith("```"):
                # Remove opening ```lang
                first_newline = content.index("\n") if "\n" in content else len(content)
                content = content[first_newline + 1:]
            if content.endswith("```"):
                content = content[:-3].rstrip()

            files.append((filename, content))

        return files

    def _get_dir_for_agent(self, agent_name: str) -> Path:
        """Determine which directory to use based on agent name."""
        agent_dir_map = {
            AgentName.DEVELOPMENT.value: self.src_dir,
            AgentName.TESTING.value: self.src_dir,  # Corrected files go to src
            AgentName.DOCUMENTATION.value: self.docs_dir,
            AgentName.DEPLOYMENT.value: self.deploy_dir,
            AgentName.MARKETING.value: self.marketing_dir,
        }
        return agent_dir_map.get(agent_name, self.docs_dir)

    def _get_dir_for_file(self, filename: str, agent_name: str) -> Path:
        """Determine directory based on file extension and agent."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # Source code files always go to src/
        if ext in ("html", "css", "js", "json") and agent_name in (
            AgentName.DEVELOPMENT.value, AgentName.TESTING.value
        ):
            return self.src_dir

        # Deployment configs go to deploy/
        if agent_name == AgentName.DEPLOYMENT.value:
            if filename == "vercel.json":
                return self.deploy_dir
            return self.deploy_dir

        # Marketing files
        if agent_name == AgentName.MARKETING.value:
            return self.marketing_dir

        # Documentation and everything else
        if ext == "md" and agent_name in (
            AgentName.DOCUMENTATION.value,
            AgentName.PLANNING.value,
            AgentName.REQUIREMENTS.value,
            AgentName.DESIGN.value,
        ):
            return self.docs_dir

        return self._get_dir_for_agent(agent_name)
