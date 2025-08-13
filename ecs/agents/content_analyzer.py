# ecs/agents/content_analyzer.py
from typing import Dict, Any, List, Union
from pydantic import BaseModel, Field, ConfigDict
from config import LLMInterface

class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=False)
    
    concepts: List[str] = Field(description="Key concepts/terms")
    learning_objectives: List[str] = Field(description="Bloom-style objectives")
    syllabus_tree: Any = Field(description="Module-to-sections map")

ANALYZER_SYS = """You are a precise academic content analyzer.
Extract key concepts, Bloom-style learning objectives, and a topic tree.
Return STRICT JSON with keys: concepts, learning_objectives, syllabus_tree."""

ANALYZER_USER_TEMPLATE = """Analyze the following lecture excerpts and extract:
- 5–10 key concepts (single-phrase terms)
- 3–6 learning objectives in Bloom's taxonomy language
- Topic hierarchy with 1–3 top modules, each listing 2–5 sections
TEXT:
{joined_text}
"""

class ContentAnalyzer:
    """
    1-LLM agent: reads retrieved chunks and produces structured teaching targets.
    """
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.calls_made = 0

    def analyze(self, passages: List[str]) -> AnalysisResult:
        joined = "\n\n---\n\n".join(passages[:6])
        user = ANALYZER_USER_TEMPLATE.format(joined_text=joined)
        out = self.llm.call_json([
            {"role":"system","content":ANALYZER_SYS},
            {"role":"user","content":user}
        ])
        self.calls_made += 1
        
        # Use model_validate with strict=False to handle validation errors
        try:
            return AnalysisResult.model_validate(out, strict=False)
        except Exception as e:
            print(f"Validation error: {e}")
            # Fallback: create with minimal validation
            result = AnalysisResult(concepts=[], learning_objectives=[], syllabus_tree={})
            result.concepts = out.get('concepts', [])
            result.learning_objectives = out.get('learning_objectives', [])
            result.syllabus_tree = out.get('syllabus_tree', {})
            return result
