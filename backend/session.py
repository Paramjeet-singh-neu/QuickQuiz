"""Signed cookie session helpers for OAuth tokens."""

from __future__ import annotations

import json
import secrets
import time
from typing import Any, Dict, Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import AppConfig


class SessionManager:
    COOKIE_NAME = "quickquiz_session"
    STATE_COOKIE = "quickquiz_oauth_state"
    MAX_AGE = 60 * 60 * 24 * 7

    def __init__(self, cfg: Optional[AppConfig] = None):
        self.cfg = cfg or AppConfig()
        self._serializer = URLSafeTimedSerializer(self.cfg.session_secret, salt="quickquiz-session")

    def create_state(self) -> str:
        return secrets.token_urlsafe(32)

    def sign_state(self, state: str) -> str:
        return self._serializer.dumps({"state": state})

    def verify_state(self, signed_state: str, returned_state: str) -> bool:
        try:
            payload = self._serializer.loads(signed_state, max_age=600)
        except (BadSignature, SignatureExpired):
            return False
        return payload.get("state") == returned_state

    def create_session(self, token_payload: Dict[str, Any], userinfo: Dict[str, Any]) -> str:
        session = {
            "access_token": token_payload["access_token"],
            "refresh_token": token_payload.get("refresh_token"),
            "expires_at": int(time.time()) + int(token_payload.get("expires_in", 3600)),
            "scope": token_payload.get("scope", ""),
            "user": {
                "sub": userinfo.get("sub"),
                "email": userinfo.get("email"),
                "name": userinfo.get("name"),
                "picture": userinfo.get("picture"),
            },
        }
        return self._serializer.dumps(session)

    def load_session(self, cookie_value: str) -> Optional[Dict[str, Any]]:
        try:
            return self._serializer.loads(cookie_value, max_age=self.MAX_AGE)
        except (BadSignature, SignatureExpired):
            return None

    def update_tokens(self, cookie_value: str, token_payload: Dict[str, Any]) -> Optional[str]:
        session = self.load_session(cookie_value)
        if not session:
            return None
        session["access_token"] = token_payload["access_token"]
        session["refresh_token"] = token_payload.get("refresh_token", session.get("refresh_token"))
        session["expires_at"] = int(time.time()) + int(token_payload.get("expires_in", 3600))
        session["scope"] = token_payload.get("scope", session.get("scope", ""))
        return self._serializer.dumps(session)

    def clear_session_cookie(self) -> Dict[str, Any]:
        return {
            "key": self.COOKIE_NAME,
            "value": "",
            "max_age": 0,
            "httponly": True,
            "secure": self.cfg.cookie_secure,
            "samesite": "lax",
            "path": "/",
        }

    def session_cookie(self, signed_value: str) -> Dict[str, Any]:
        return {
            "key": self.COOKIE_NAME,
            "value": signed_value,
            "max_age": self.MAX_AGE,
            "httponly": True,
            "secure": self.cfg.cookie_secure,
            "samesite": "lax",
            "path": "/",
        }

    def state_cookie(self, signed_value: str) -> Dict[str, Any]:
        return {
            "key": self.STATE_COOKIE,
            "value": signed_value,
            "max_age": 600,
            "httponly": True,
            "secure": self.cfg.cookie_secure,
            "samesite": "lax",
            "path": "/",
        }
