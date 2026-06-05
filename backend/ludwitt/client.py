"""Shared Ludwitt HTTP helpers and typed errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from config import AppConfig


@dataclass
class LudwittError(Exception):
    status_code: int
    error: str
    description: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"{self.error}: {self.description}"


class LudwittHTTPClient:
    def __init__(self, cfg: Optional[AppConfig] = None):
        self.cfg = cfg or AppConfig()
        self.base_url = self.cfg.ludwitt_base_url.rstrip("/")

    def _parse_error(self, response: httpx.Response) -> LudwittError:
        try:
            payload = response.json()
        except Exception:
            payload = {}
        return LudwittError(
            status_code=response.status_code,
            error=payload.get("error", "unknown_error"),
            description=payload.get("error_description", response.text or "Request failed"),
            code=payload.get("code"),
            details=payload.get("details"),
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        access_token: Optional[str] = None,
        json_body: Optional[Dict[str, Any]] = None,
        form_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        req_headers = dict(headers or {})
        if access_token:
            req_headers["Authorization"] = f"Bearer {access_token}"
        if json_body is not None:
            req_headers.setdefault("Content-Type", "application/json")

        with httpx.Client(timeout=60.0) as client:
            response = client.request(
                method,
                url,
                json=json_body,
                data=form_body,
                params=params,
                headers=req_headers,
            )

        if response.status_code >= 400:
            raise self._parse_error(response)
        return response
