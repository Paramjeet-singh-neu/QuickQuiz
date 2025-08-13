# ecs/config.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os

class AppConfig:
    """Application configuration"""
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.model_name = os.getenv('MODEL_NAME', 'gpt-4o-mini')
        self.economy_cost_per_call = float(os.getenv('ECONOMY_COST_PER_CALL', '0.002'))

class LLMInterface(ABC):
    """Abstract interface for LLM interactions"""
    
    @abstractmethod
    def call_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call LLM and return JSON response"""
        pass
