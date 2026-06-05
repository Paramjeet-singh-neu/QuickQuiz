# ecs/coordinator.py
from typing import Dict, Any, Optional

from config import AppConfig, LLMInterface, OpenAILLMClient
from ecs.services.quiz_service import QuizService


class Coordinator:
    """Backward-compatible coordinator wrapper around QuizService."""

    def __init__(self, llm: Optional[LLMInterface] = None, cfg: Optional[AppConfig] = None):
        self.cfg = cfg or AppConfig()
        self.llm = llm or OpenAILLMClient(self.cfg)
        self.service = QuizService(llm=self.llm, cfg=self.cfg)

    def process_pdf_to_quiz(
        self,
        pdf_path: str,
        n_questions: int = 10,
        retrieval_query: str = "overview of lecture",
    ) -> Dict[str, Any]:
        print("→ DocumentProcessor: building vector store… (0 LLM)")
        print("→ ContentAnalyzer: analyzing concepts/objectives… (1 LLM)")
        print("→ StatisticalAnalyzer: analyzing text statistics… (0 LLM)")
        print("→ QuizGenerator: creating quiz… (0 LLM)")
        return self.service.generate_online(
            pdf_path,
            n_questions=n_questions,
            retrieval_query=retrieval_query,
        )
