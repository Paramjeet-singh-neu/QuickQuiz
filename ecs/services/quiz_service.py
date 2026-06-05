"""Shared quiz generation service for CLI, Streamlit, and API routes."""

from __future__ import annotations

import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import AppConfig, LLMInterface, OpenAILLMClient
from ecs.agents.document_processor import DocumentProcessor
from ecs.agents.quiz_generator import QuizGenerator
from ecs.agents.statistical_analyzer import StatisticalAnalyzer
from ecs.agents.content_analyzer import ContentAnalyzer


def _extract_offline_concepts(passages: List[str]) -> List[str]:
    all_text = " ".join(passages)
    words = re.findall(r"\b[A-Z][a-zA-Z\s-]+\b", all_text)
    word_counts = Counter([w.strip() for w in words if len(w.strip()) > 3])
    return [word for word, count in word_counts.most_common(10) if count > 1]


class QuizService:
    """Orchestrates PDF processing and quiz generation."""

    def __init__(self, llm: Optional[LLMInterface] = None, cfg: Optional[AppConfig] = None):
        self.cfg = cfg or AppConfig()
        self.llm = llm
        self._doc: Optional[DocumentProcessor] = None
        self.quiz_gen = QuizGenerator()
        self.stats = StatisticalAnalyzer()

    @property
    def doc(self) -> DocumentProcessor:
        if self._doc is None:
            self._doc = DocumentProcessor()
        return self._doc

    def generate_offline(
        self,
        pdf_path: str,
        n_questions: int = 10,
        retrieval_query: str = "overview of lecture",
    ) -> Dict[str, Any]:
        n_chunks = self.doc.build_store(pdf_path)
        passages = [r["text"] for r in self.doc.retrieve(retrieval_query, k=6)]
        stats_analysis = self.stats.analyze_text_statistics(passages)
        concepts = _extract_offline_concepts(passages)
        quiz = self.quiz_gen.generate(concepts, passages, n_questions=n_questions)

        return {
            "quiz": quiz,
            "analysis": {
                "concepts": concepts,
                "learning_objectives": ["Offline mode: objectives not analyzed"],
                "syllabus_tree": {"Offline Mode": ["Text-based quiz generation"]},
            },
            "statistics": stats_analysis,
            "llm_calls_used": 0,
            "estimated_cost": 0.0,
            "mode": "offline",
            "chunks_processed": n_chunks,
            "agents": {
                "DocumentProcessor": "0 LLM",
                "ContentAnalyzer": "SKIPPED (offline)",
                "StatisticalAnalyzer": "0 LLM",
                "QuizGenerator": "0 LLM",
            },
        }

    def generate_online(
        self,
        pdf_path: str,
        n_questions: int = 10,
        retrieval_query: str = "overview of lecture",
    ) -> Dict[str, Any]:
        if self.llm is None:
            self.llm = OpenAILLMClient(self.cfg)

        analyzer = ContentAnalyzer(self.llm)
        n_chunks = self.doc.build_store(pdf_path)
        passages = [r["text"] for r in self.doc.retrieve(retrieval_query, k=6)]
        analysis = analyzer.analyze(passages)
        stats_analysis = self.stats.analyze_text_statistics(passages)
        quiz = self.quiz_gen.generate(analysis.concepts, passages, n_questions=n_questions)

        return {
            "quiz": quiz,
            "analysis": analysis.model_dump(),
            "statistics": stats_analysis,
            "llm_calls_used": self.llm.call_count,
            "estimated_cost": round(self.llm.estimated_cost(), 4),
            "mode": "online",
            "chunks_processed": n_chunks,
            "agents": {
                "DocumentProcessor": "0 LLM",
                "ContentAnalyzer": "1 LLM",
                "StatisticalAnalyzer": "0 LLM",
                "QuizGenerator": "0 LLM",
            },
        }

    def generate(
        self,
        pdf_path: str,
        n_questions: int = 10,
        offline: bool = False,
        source_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if offline:
            result = self.generate_offline(pdf_path, n_questions=n_questions)
        else:
            result = self.generate_online(pdf_path, n_questions=n_questions)

        result["run_id"] = str(uuid.uuid4())
        result["source_name"] = source_name or pdf_path.split("/")[-1]
        result["created_at"] = datetime.now(timezone.utc).isoformat()
        return result

    @staticmethod
    def compact_for_storage(result: Dict[str, Any]) -> Dict[str, Any]:
        """Trim payload to fit Ludwitt hosted-data quotas."""
        return {
            "runId": result.get("run_id"),
            "sourceName": result.get("source_name"),
            "createdAt": result.get("created_at"),
            "mode": result.get("mode"),
            "questionCount": result.get("quiz", {}).get("count", 0),
            "llmCallsUsed": result.get("llm_calls_used", 0),
            "estimatedCost": result.get("estimated_cost", 0.0),
            "analysis": {
                "concepts": result.get("analysis", {}).get("concepts", [])[:10],
                "learningObjectives": result.get("analysis", {}).get("learning_objectives", [])[:6],
            },
            "statisticsSummary": {
                "wordCount": result.get("statistics", {})
                .get("basic_stats", {})
                .get("word_count"),
                "readabilityLevel": result.get("statistics", {})
                .get("readability", {})
                .get("readability_level"),
            },
            "quiz": result.get("quiz"),
        }
