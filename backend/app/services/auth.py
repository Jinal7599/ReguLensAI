from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import allowed_origins
from app.db.models import User
from app.db.session import get_optional_db

SESSION_COOKIE_NAME = "regulens_session"
SESSION_TTL_SECONDS = 12 * 60 * 60
SESSION_ISSUER = "regulens-ai"
SESSION_AUDIENCE = "regulens-ai"


def auth_configuration() -> dict[str, bool]:
    secret = os.getenv("SESSION_SECRET", "").strip()
    return {
        "google_client_configured": bool(os.getenv("GOOGLE_CLIENT_ID", "").strip()),
        "session_secret_configured": len(secret) >= 32,
    }


def _session_secret() -> str:
    secret = os.getenv("SESSION_SECRET", "").strip()
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured. Set GOOGLE_CLIENT_ID and a SESSION_SECRET of at least 32 characters.")
    return secret


def verify_google_credential(credential: str) -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured. Set GOOGLE_CLIENT_ID on the API service.")
    try:
        claims = id_token.verify_oauth2_token(credential, GoogleRequest(), client_id)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified. Please sign in again.") from exc
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Invalid Google token issuer.")
    if claims.get("email_verified") is not True or not claims.get("sub") or not claims.get("email"):
        raise HTTPException(status_code=403, detail="A verified Google account is required.")
    return claims


def create_session_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "iss": SESSION_ISSUER, "aud": SESSION_AUDIENCE,
         "iat": now, "exp": now + timedelta(seconds=SESSION_TTL_SECONDS)},
        _session_secret(), algorithm="HS256",
    )


def _decode_session_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, _session_secret(), algorithms=["HS256"],
            issuer=SESSION_ISSUER, audience=SESSION_AUDIENCE,
            options={"require": ["sub", "iat", "exp", "iss", "aud"]},
        )
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("Missing session subject")
        return subject
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Your session is invalid or has expired. Please sign in again.") from exc


def set_session_cookie(response, token: str) -> None:
    production = os.getenv("APP_ENV", "development").strip().lower() == "production"
    response.set_cookie(
        key=SESSION_COOKIE_NAME, value=token, max_age=SESSION_TTL_SECONDS,
        httponly=True, secure=production, samesite="none" if production else "lax", path="/",
    )


def clear_session_cookie(response) -> None:
    production = os.getenv("APP_ENV", "development").strip().lower() == "production"
    response.delete_cookie(
        SESSION_COOKIE_NAME, path="/", secure=production, httponly=True,
        samesite="none" if production else "lax",
    )


def require_browser_request(request: Request) -> None:
    origin = request.headers.get("origin", "").rstrip("/")
    if not origin and os.getenv("APP_ENV", "development").strip().lower() != "production":
        return
    if not origin or origin not in allowed_origins():
        raise HTTPException(status_code=403, detail="Request origin is not allowed.")
    if request.headers.get("x-regulens-request") != "browser":
        raise HTTPException(status_code=403, detail="A valid browser request header is required.")


def _local_user(session: Session) -> User:
    user = session.scalar(select(User).where(User.google_sub == "local-development-user"))
    if user is None:
        user = User(google_sub="local-development-user", email="developer@localhost", display_name="Local Developer")
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def get_optional_user(
    request: Request,
    session: Session | None = Depends(get_optional_db),
) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        if os.getenv("APP_ENV", "development").strip().lower() != "production":
            if session is None:
                return None
            return _local_user(session)
        return None
    if session is None:
        raise HTTPException(status_code=503, detail="Persistent storage is not configured.")
    user_id = _decode_session_token(token)
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Your account is no longer available. Please sign in again.")
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in with Google to access your documents.")
    return user
