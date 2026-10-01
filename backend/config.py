"""
Auctor Systems — Central Configuration

All application-wide settings are loaded here from environment variables.
A single Gemini model is used consistently across all 8 agents.
Configuration can be changed by updating the .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── LLM Configuration ────────────────────────────────────────────────────────
# Single model for all 8 agents — completely configurable via GEMINI_MODEL
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "")
GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

# Ensure environment variables are synchronized for CrewAI's Gemini provider
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    os.environ.setdefault("GOOGLE_API_KEY", GEMINI_API_KEY)

# ── Deployment Configuration ─────────────────────────────────────────────────
VERCEL_TOKEN: str = os.getenv("VERCEL_TOKEN", "")

# ── Path Configuration ────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).parent
PROJECTS_DIR: Path = BASE_DIR / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)
DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "auctor.db")))

# ── Application Configuration ────────────────────────────────────────────────
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))


def validate_config() -> dict:
    """
    Validate critical configuration and return a status report.
    Does not raise — Auctor should start even without all credentials,
    but features degrade gracefully.
    """
    current_model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
    status = {
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)),
        "model_configured": bool(current_model),
        "model": current_model,
        "vercel_configured": bool(os.getenv("VERCEL_TOKEN", VERCEL_TOKEN)),
        "projects_dir": str(PROJECTS_DIR),
    }
    return status
