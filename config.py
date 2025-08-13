# ecs/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List, Dict, Any
from openai import OpenAI

load_dotenv()

@dataclass
class AppConfig:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    # course uses $0.002 per call for estimates; keep it configurable
    economy_cost_per_call: float = float(os.getenv("ECONOMY_COST_PER_CALL", "0.002"))

class LLMInterface:
    """
    Centralized LLM manager. Tracks calls & estimates cost.
    """
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.client = OpenAI(api_key=self.cfg.openai_api_key) if self.cfg.openai_api_key else None
        self.call_count = 0

    def call_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        self.call_count += 1
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY not set. Please set it in .env or environment.")
        resp = self.client.chat.completions.create(
            model=self.cfg.model_name,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        content = resp.choices[0].message.content
        import json
        return json.loads(content)

    def estimated_cost(self) -> float:
        # Simple, course-style estimate: flat per call
        return self.call_count * self.cfg.economy_cost_per_call
