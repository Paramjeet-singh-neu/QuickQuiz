"""Ludwitt credits balance API."""

from __future__ import annotations

from typing import Any, Dict, Optional

from config import AppConfig
from backend.ludwitt.client import LudwittHTTPClient


class LudwittCreditsClient(LudwittHTTPClient):
    def get_balance(self, access_token: str) -> Dict[str, Any]:
        response = self.request(
            "GET",
            "/api/v1/credits/balance",
            access_token=access_token,
        )
        payload = response.json()
        return {
            "spendable_cents": payload.get("spendableCents", 0),
            "balance_cents": payload.get("balanceCents", 0),
            "raw": payload,
        }
