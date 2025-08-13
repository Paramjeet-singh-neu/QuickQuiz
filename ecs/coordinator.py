# ecs/coordinator.py
from typing import Dict, Any, List
from ecs.agents.document_processor import DocumentProcessor
from ecs.agents.content_analyzer import ContentAnalyzer
from ecs.agents.quiz_generator import QuizGenerator
from ecs.agents.statistical_analyzer import StatisticalAnalyzer
from config import AppConfig, LLMInterface

class Coordinator:
    def __init__(self):
        self.cfg = AppConfig()
        self.doc = DocumentProcessor()
        self.llm = LLMInterface(self.cfg)
        self.analyzer = ContentAnalyzer(self.llm)
        self.quiz = QuizGenerator()
        self.stats = StatisticalAnalyzer()

    def process_pdf_to_quiz(self, pdf_path: str, n_questions: int = 10, retrieval_query: str = "overview of lecture") -> Dict[str, Any]:
        print("→ DocumentProcessor: building vector store… (0 LLM)")
        n_chunks = self.doc.build_store(pdf_path)

        print(f"  Added {n_chunks} chunks. Retrieving passages…")
        passages = [r["text"] for r in self.doc.retrieve(retrieval_query, k=6)]

        print("→ ContentAnalyzer: analyzing concepts/objectives… (1 LLM)")
        analysis = self.analyzer.analyze(passages)

        print("→ StatisticalAnalyzer: analyzing text statistics… (0 LLM)")
        stats_analysis = self.stats.analyze_text_statistics(passages)

        print("→ QuizGenerator: creating quiz… (0 LLM)")
        quiz = self.quiz.generate(analysis.concepts, passages, n_questions=n_questions)

        report = {
            "quiz": quiz,
            "analysis": analysis.model_dump(),
            "statistics": stats_analysis,
            "llm_calls_used": self.llm.call_count,
            "estimated_cost": round(self.llm.estimated_cost(), 4),
            "agents": {
                "DocumentProcessor": "0 LLM",
                "ContentAnalyzer": "1 LLM",
                "StatisticalAnalyzer": "0 LLM",
                "QuizGenerator": "0 LLM",
            }
        }
        return report