"""Ludwitt OAuth token and userinfo helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlencode

from config import AppConfig
from backend.ludwitt.client import LudwittHTTPClient


class LudwittOAuthClient(LudwittHTTPClient):
    def build_authorize_url(self, state: str, code_challenge: Optional[str] = None) -> str:
        params = {
            "client_id": self.cfg.ludwitt_client_id,
            "redirect_uri": self.cfg.ludwitt_redirect_uri,
            "response_type": "code",
            "scope": self.cfg.ludwitt_scopes,
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"{self.base_url}/oauth/authorize?{urlencode(params)}"

    def exchange_code(self, code: str) -> Dict[str, Any]:
        response = self.request(
            "POST",
            "/api/oauth/token",
            form_body={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.cfg.ludwitt_redirect_uri,
                "client_id": self.cfg.ludwitt_client_id,
                "client_secret": self.cfg.ludwitt_client_secret,
            },
        )
        return response.json()

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        response = self.request(
            "POST",
            "/api/oauth/token",
            form_body={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.cfg.ludwitt_client_id,
                "client_secret": self.cfg.ludwitt_client_secret,
            },
        )
        return response.json()

    def userinfo(self, access_token: str) -> Dict[str, Any]:
        response = self.request("GET", "/api/oauth/userinfo", access_token=access_token)
        return response.json()

    def revoke(self, token: str) -> None:
        self.request(
            "POST",
            "/api/oauth/revoke",
            form_body={"token": token},
        )
