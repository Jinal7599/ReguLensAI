from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


def load_local_environment(
    project_root: Path = PROJECT_ROOT,
    backend_root: Path = BACKEND_ROOT,
) -> None:
    """
    Load developer .env files without overriding explicit process / Render variables.
    The repository-root .env is the canonical location; backend/.env is also supported.
    """
    for env_file in (project_root / ".env", backend_root / ".env"):
        if env_file.is_file():
            load_dotenv(dotenv_path=env_file, override=False)


# Render supplies environment variables directly; this is a no-op when no local .env exists.
load_local_environment()


def allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
