"""Authentication routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from backend.deps import get_cfg, get_current_session, get_session_manager
from backend.ludwitt.oauth import LudwittOAuthClient
from backend.session import SessionManager
from config import AppConfig

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login(
    response: Response,
    cfg: AppConfig = Depends(get_cfg),
    manager: SessionManager = Depends(get_session_manager),
):
    oauth = LudwittOAuthClient(cfg)
    state = manager.create_state()
    signed_state = manager.sign_state(state)
    authorize_url = oauth.build_authorize_url(state=state)

    redirect = RedirectResponse(url=authorize_url, status_code=302)
    redirect.set_cookie(**manager.state_cookie(signed_state))
    return redirect


@router.get("/callback")
def callback(
    request: Request,
    code: str,
    state: str,
    quickquiz_oauth_state: str | None = Cookie(default=None),
    cfg: AppConfig = Depends(get_cfg),
    manager: SessionManager = Depends(get_session_manager),
):
    if not quickquiz_oauth_state or not manager.verify_state(quickquiz_oauth_state, state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    oauth = LudwittOAuthClient(cfg)
    try:
        token_payload = oauth.exchange_code(code)
        userinfo = oauth.userinfo(token_payload["access_token"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {exc}") from exc

    signed_session = manager.create_session(token_payload, userinfo)
    redirect = RedirectResponse(url=cfg.frontend_url, status_code=302)
    redirect.set_cookie(**manager.session_cookie(signed_session))
    redirect.delete_cookie(manager.STATE_COOKIE, path="/")
    return redirect


@router.get("/me")
def me(session: Dict[str, Any] = Depends(get_current_session)):
    return {"authenticated": True, "user": session.get("user", {})}


@router.post("/logout")
def logout(
    session: Dict[str, Any] = Depends(get_current_session),
    manager: SessionManager = Depends(get_session_manager),
):
    oauth = LudwittOAuthClient()
    token = session.get("refresh_token") or session.get("access_token")
    if token:
        try:
            oauth.revoke(token)
        except Exception:
            pass

    response = Response(content='{"ok": true}')
    response.media_type = "application/json"
    response.set_cookie(**manager.clear_session_cookie())
    return response
