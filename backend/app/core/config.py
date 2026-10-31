from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
_LOADED_GEMINI_KEY_SOURCE: str | None = None


def load_local_environment(
    project_root: Path = PROJECT_ROOT,
    backend_root: Path = BACKEND_ROOT,
) -> list[str]:
    """
    Load .env values only when the process environment value is missing or blank.
    Non-empty shell / Render values always take precedence. Root .env is canonical;
    backend/.env is supported as a convenient alternative.
    """
    global _LOADED_GEMINI_KEY_SOURCE

    # Avoid loading a developer's real .env credentials into tests. Tests that
    # explicitly exercise dotenv loading pass isolated temporary paths.
    if (
        os.getenv("APP_ENV", "").strip().lower() == "test"
        and project_root == PROJECT_ROOT
        and backend_root == BACKEND_ROOT
    ):
        return []

    loaded_files: list[str] = []
    for source_name, env_file in (
        ("repository .env", project_root / ".env"),
        ("backend .env", backend_root / ".env"),
    ):
        if not env_file.is_file():
            continue

        loaded_files.append(source_name)
        for key, value in dotenv_values(env_file).items():
            if value is None:
                continue
            current = os.getenv(key, "")
            if not current.strip():
                os.environ[key] = value
                if key == "GEMINI_API_KEY" and value.strip():
                    _LOADED_GEMINI_KEY_SOURCE = source_name

    return loaded_files


def gemini_configuration() -> dict[str, object]:
    loaded_files = load_local_environment()
    api_key_configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
    if not api_key_configured:
        source = "missing"
    elif _LOADED_GEMINI_KEY_SOURCE:
        source = _LOADED_GEMINI_KEY_SOURCE
    else:
        source = "process environment"
    return {
        "configured": api_key_configured,
        "model": os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip() or "gemini-flash-latest",
        "key_source": source,
        "local_env_files_found": loaded_files,
    }


# Load local configuration at startup. analyze_document() rechecks before each upload
# so developers can create or correct .env without relying on import-time discovery.
load_local_environment()


def allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
