from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Generator

from fastapi import HTTPException
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import BACKEND_ROOT, load_local_environment

_engine: Engine | None = None
_engine_url: str | None = None
_session_factory: sessionmaker[Session] | None = None
_engine_override_url: str | None = None
_lock = Lock()


def resolve_database_url() -> str | None:
    """Return a configured database URL; local development defaults to SQLite."""
    load_local_environment()
    if _engine_override_url is not None:
        return _engine_override_url
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured:
        if configured.startswith("postgres://"):
            return "postgresql+psycopg://" + configured[len("postgres://"):]
        if configured.startswith("postgresql://"):
            return "postgresql+psycopg://" + configured[len("postgresql://"):]
        return configured
    if os.getenv("APP_ENV", "development").strip().lower() == "production":
        return None
    local_dir = BACKEND_ROOT / ".local"
    local_dir.mkdir(parents=True, exist_ok=True)
    return "sqlite:///" + str(local_dir / "regulens.db")


def configure_database(url: str | None = None) -> Engine | None:
    """Configure or reset the engine. Primarily useful for isolated tests."""
    global _engine, _engine_url, _session_factory, _engine_override_url
    with _lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None
        _engine_url = None
        _session_factory = None
        _engine_override_url = url
        if url is None:
            return None
        return _build_engine(url)


def _build_engine(url: str) -> Engine:
    global _engine, _engine_url, _session_factory
    options: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if url.endswith(":memory:"):
            options["poolclass"] = StaticPool
    _engine = create_engine(url, **options)
    _engine_url = url
    _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_engine() -> Engine | None:
    global _engine
    url = resolve_database_url()
    if not url:
        return None
    if _engine is None or _engine_url != url:
        with _lock:
            if _engine is None or _engine_url != url:
                return _build_engine(url)
    return _engine


def get_session_factory() -> sessionmaker[Session] | None:
    get_engine()
    return _session_factory


def private_document_access_enabled() -> bool:
    """Private document APIs remain local-only until authentication is implemented."""
    return os.getenv("APP_ENV", "development").strip().lower() != "production"


def get_db() -> Generator[Session, None, None]:
    if not private_document_access_enabled():
        raise HTTPException(
            status_code=503,
            detail="Private document APIs are disabled on this public deployment until authentication and access controls are enabled.",
        )
    factory = get_session_factory()
    if factory is None:
        raise HTTPException(
            status_code=503,
            detail="Persistent storage is not configured. Set DATABASE_URL to a PostgreSQL connection string.",
        )
    with factory() as session:
        yield session


def get_optional_db() -> Generator[Session | None, None, None]:
    if not private_document_access_enabled():
        yield None
        return
    factory = get_session_factory()
    if factory is None:
        yield None
        return
    with factory() as session:
        yield session
