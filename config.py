"""Unified application configuration and LLM provider interfaces."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AppConfig:
    """Shared configuration for CLI, API, and Ludwitt integration."""

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o-mini"))
    economy_cost_per_call: float = field(
        default_factory=lambda: float(os.getenv("ECONOMY_COST_PER_CALL", "0.002"))
    )

    ludwitt_base_url: str = field(
        default_factory=lambda: os.getenv("LUDWITT_BASE_URL", "https://www.ludwitt.com")
    )
    cors_origins: str = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "")
    )
    ludwitt_client_id: str = field(default_factory=lambda: os.getenv("LUDWITT_CLIENT_ID", ""))
    ludwitt_client_secret: str = field(
        default_factory=lambda: os.getenv("LUDWITT_CLIENT_SECRET", "")
    )
    ludwitt_redirect_uri: str = field(
        default_factory=lambda: os.getenv(
            "LUDWITT_REDIRECT_URI", "http://localhost:8000/auth/callback"
        )
    )
    ludwitt_ai_model: str = field(
        default_factory=lambda: os.getenv("LUDWITT_AI_MODEL", "claude-haiku-4-5")
    )
    ludwitt_scopes: str = field(
        default_factory=lambda: os.getenv(
            "LUDWITT_SCOPES",
            "profile credits:read credits:spend data:read data:write",
        )
    )

    session_secret: str = field(
        default_factory=lambda: os.getenv("SESSION_SECRET", "dev-change-me-in-production")
    )
    frontend_url: str = field(
        default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:5173")
    )
    cookie_secure: bool = field(
        default_factory=lambda: os.getenv("COOKIE_SECURE", "false").lower() == "true"
    )


class LLMInterface(ABC):
    """Abstract LLM provider used by ContentAnalyzer."""

    call_count: int = 0
    last_charged_cents: Optional[int] = None

    @abstractmethod
    def call_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Return parsed JSON from an LLM chat completion."""

    def estimated_cost(self) -> float:
        if self.last_charged_cents is not None:
            return self.last_charged_cents / 100.0
        return 0.0


class OpenAILLMClient(LLMInterface):
    """Direct OpenAI client for CLI / legacy offline development."""

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.call_count = 0
        self.last_charged_cents = None
        self._client = None
        if cfg.openai_api_key:
            from openai import OpenAI

            self._client = OpenAI(api_key=cfg.openai_api_key)

    def call_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        self.call_count += 1
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY not set. Please set it in .env or environment.")
        resp = self._client.chat.completions.create(
            model=self.cfg.model_name,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        self.last_charged_cents = int(self.cfg.economy_cost_per_call * 100)
        return json.loads(content)

    def estimated_cost(self) -> float:
        return self.call_count * self.cfg.economy_cost_per_call


class LudwittLLMClient(LLMInterface):
    """Routes AI calls through Ludwitt's credit-billed proxy."""

    def __init__(self, access_token: str, cfg: Optional[AppConfig] = None):
        self.cfg = cfg or AppConfig()
        self.access_token = access_token
        self.call_count = 0
        self.last_charged_cents = None

    def call_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        from backend.ludwitt.ai import LudwittAIClient

        self.call_count += 1
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_messages = [m for m in messages if m["role"] != "system"]
        client = LudwittAIClient(self.cfg)
        result = client.create_json_message(
            access_token=self.access_token,
            messages=user_messages,
            system=system,
            model=self.cfg.ludwitt_ai_model,
        )
        self.last_charged_cents = result.get("charged_cost_cents")
        return result["json"]
