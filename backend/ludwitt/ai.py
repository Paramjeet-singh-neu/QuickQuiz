"""Ludwitt AI messages proxy."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from config import AppConfig
from backend.ludwitt.client import LudwittHTTPClient


class LudwittAIClient(LudwittHTTPClient):
    def create_message(
        self,
        access_token: str,
        messages: List[Dict[str, str]],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": model or self.cfg.ludwitt_ai_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            body["system"] = system

        response = self.request(
            "POST",
            "/api/v1/ai/messages",
            access_token=access_token,
            json_body=body,
        )
        payload = response.json()
        credits_header = response.headers.get("x-ludwitt-credits")
        charged_cost_cents = None
        if credits_header:
            try:
                charged_cost_cents = json.loads(credits_header).get("chargedCostCents")
            except json.JSONDecodeError:
                pass

        content_blocks = payload.get("content") or []
        text = ""
        if content_blocks and isinstance(content_blocks, list):
            text = content_blocks[0].get("text", "")
        elif payload.get("choices"):
            text = payload["choices"][0]["message"]["content"]

        return {
            "text": text,
            "charged_cost_cents": charged_cost_cents,
            "raw": payload,
        }

    def create_json_message(
        self,
        access_token: str,
        messages: List[Dict[str, str]],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        json_system = (system or "") + "\nReturn ONLY valid JSON with no markdown fences."
        result = self.create_message(
            access_token=access_token,
            messages=messages,
            system=json_system,
            model=model,
            max_tokens=max_tokens,
        )
        text = result["text"].strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return {
            "json": json.loads(text),
            "charged_cost_cents": result.get("charged_cost_cents"),
            "raw": result.get("raw"),
        }
