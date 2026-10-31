from __future__ import annotations

from datetime import datetime, timezone
import secrets
import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.services.auth import (
    SESSION_TTL_SECONDS, auth_configuration, clear_session_cookie,
    create_session_token, get_current_user, require_browser_request,
    set_session_cookie, verify_google_credential,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
OAUTH_NONCE_COOKIE = "regulens_oauth_nonce"
OAUTH_NONCE_TTL_SECONDS = 300


class GoogleCredentialRequest(BaseModel):
    credential: str = Field(min_length=20, max_length=10000)


def _user_payload(user: User) -> dict:
    return {"id": user.id, "email": user.email, "name": user.display_name, "picture": user.picture_url}


@router.post("/nonce")
def create_oauth_nonce(request: Request, response: Response) -> dict[str, str]:
    require_browser_request(request)
    nonce = secrets.token_urlsafe(32)
    production = os.getenv("APP_ENV", "development").strip().lower() == "production"
    response.set_cookie(
        key=OAUTH_NONCE_COOKIE, value=nonce, max_age=OAUTH_NONCE_TTL_SECONDS,
        httponly=True, secure=production, samesite="none" if production else "lax", path="/",
    )
    return {"nonce": nonce}


@router.post("/google")
def google_login(payload: GoogleCredentialRequest, request: Request, response: Response, session: Session = Depends(get_db)) -> dict:
    require_browser_request(request)
    if not all(auth_configuration().values()):
        raise HTTPException(status_code=503, detail="Authentication is not configured. Set GOOGLE_CLIENT_ID and SESSION_SECRET (minimum 32 characters) on the API service.")
    claims = verify_google_credential(payload.credential)
    expected_nonce = request.cookies.get(OAUTH_NONCE_COOKIE, "")
    token_nonce = str(claims.get("nonce") or "")
    if not expected_nonce or not token_nonce or not hmac.compare_digest(expected_nonce, token_nonce):
        raise HTTPException(status_code=401, detail="Google sign-in challenge is invalid or expired. Please try again.")
    response.delete_cookie(
        OAUTH_NONCE_COOKIE, path="/",
        secure=os.getenv("APP_ENV", "development").strip().lower() == "production",
        httponly=True,
        samesite="none" if os.getenv("APP_ENV", "development").strip().lower() == "production" else "lax",
    )
    google_sub = str(claims["sub"])
    email = str(claims["email"]).strip().lower()
    user = session.scalar(select(User).where(User.google_sub == google_sub))
    now = datetime.now(timezone.utc)
    if user is None:
        user = User(
            google_sub=google_sub, email=email,
            display_name=str(claims.get("name") or email)[:240],
            picture_url=str(claims.get("picture") or "")[:1000] or None,
            last_login_at=now,
        )
        session.add(user)
    else:
        user.email = email
        user.display_name = str(claims.get("name") or user.display_name or email)[:240]
        user.picture_url = str(claims.get("picture") or user.picture_url or "")[:1000] or None
        user.last_login_at = now
    session.commit()
    session.refresh(user)
    set_session_cookie(response, create_session_token(user.id))
    return {"user": _user_payload(user), "expires_in": SESSION_TTL_SECONDS}


@router.get("/me")
def current_session(user: User = Depends(get_current_user)) -> dict:
    return {"user": _user_payload(user)}


@router.post("/logout")
def logout(request: Request, response: Response, user: User = Depends(get_current_user)) -> dict[str, bool]:
    require_browser_request(request)
    clear_session_cookie(response)
    return {"success": True}
