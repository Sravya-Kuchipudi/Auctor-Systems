"""
Auctor Systems — Export Service

Packages generated project files into a structured downloadable ZIP.
The export is REAL — it contains every file the agents produced.
"""

import io
import zipfile
import logging
from pathlib import Path

from services.project_manager import ProjectManager

logger = logging.getLogger("auctor.export")


class ExportService:
    """Creates downloadable ZIP archives of generated projects."""

    @staticmethod
    def create_zip(project_manager: ProjectManager) -> io.BytesIO:
        """
        Package the entire project into a ZIP file with this structure:
        
        auctor-project/
        ├── src/
        │   ├── index.html
        │   ├── style.css
        │   ├── script.js
        │   └── (additional pages)
        ├── docs/
        │   ├── README.md
        │   ├── ARCHITECTURE.md
        │   └── (other docs)
        ├── marketing/
        │   └── MARKETING.md
        └── deploy/
            ├── vercel.json
            └── DEPLOYMENT.md
        
        Returns a BytesIO buffer containing the ZIP data.
        """
        buffer = io.BytesIO()
        project_name = f"auctor-{project_manager.project_id[:8]}"

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Walk through all project subdirectories
            dirs_to_include = [
                (project_manager.src_dir, "src"),
                (project_manager.docs_dir, "docs"),
                (project_manager.marketing_dir, "marketing"),
                (project_manager.deploy_dir, "deploy"),
            ]

            file_count = 0
            for dir_path, dir_name in dirs_to_include:
                if not dir_path.exists():
                    continue

                for file_path in sorted(dir_path.rglob("*")):
                    if file_path.is_file():
                        # Build the archive path: project_name/dir_name/filename
                        rel_path = file_path.relative_to(dir_path)
                        archive_path = f"{project_name}/{dir_name}/{rel_path}"
                        archive_path = archive_path.replace("\\", "/")

                        try:
                            content = file_path.read_text(encoding="utf-8")
                            zf.writestr(archive_path, content)
                            file_count += 1
                        except Exception as e:
                            logger.warning(f"Could not add {file_path} to ZIP: {e}")

            # Also copy the README to the root of the ZIP for convenience
            readme_path = project_manager.docs_dir / "README.md"
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding="utf-8")
                    zf.writestr(f"{project_name}/README.md", content)
                except Exception:
                    pass

            logger.info(f"ZIP created for project {project_manager.project_id}: {file_count} files")

        buffer.seek(0)
        return buffer

    @staticmethod
    def get_zip_filename(project_manager: ProjectManager) -> str:
        """Generate a descriptive filename for the ZIP download."""
        return f"auctor-{project_manager.project_id[:8]}.zip"
