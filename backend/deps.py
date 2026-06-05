"""FastAPI dependencies for authenticated Ludwitt sessions."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import Cookie, HTTPException, Request

from config import AppConfig
from backend.ludwitt.oauth import LudwittOAuthClient
from backend.session import SessionManager


def get_cfg() -> AppConfig:
    return AppConfig()


def get_session_manager() -> SessionManager:
    return SessionManager(AppConfig())


async def get_current_session(
    request: Request,
    quickquiz_session: Optional[str] = Cookie(default=None, alias="quickquiz_session"),
) -> Dict[str, Any]:
    if not quickquiz_session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    manager = SessionManager()
    session = manager.load_session(quickquiz_session)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    if session.get("expires_at", 0) <= int(time.time()) + 60:
        refresh_token = session.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Session expired")
        oauth = LudwittOAuthClient()
        try:
            refreshed = oauth.refresh_token(refresh_token)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Unable to refresh session") from exc

        new_cookie = manager.update_tokens(quickquiz_session, refreshed)
        if new_cookie:
            request.state.new_session_cookie = manager.session_cookie(new_cookie)
            session = manager.load_session(new_cookie)

    return session
