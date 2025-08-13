# ecs/agents/quiz_generator.py
import random
from typing import List, Dict, Any
from collections import defaultdict

def _make_mcq(concept: str, source_text: str) -> Dict[str, Any]:
    # Naive, but effective: define the correct answer as the best single-sentence definition found
    # We'll grab a sentence mentioning the concept; distractors are other concept sentences.
    sentences = [s.strip() for s in source_text.split(".") if len(s.split()) > 6]
    candidates = [s for s in sentences if concept.lower() in s.lower()]
    correct = candidates[0] if candidates else sentences[0] if sentences else f"{concept} relates to the lecture content."
    return {
        "type": "mcq",
        "question": f"What best describes '{concept}'?",
        "options": [],   # we'll fill later
        "answer": correct
    }

def _make_tf(concept: str, source_text: str) -> Dict[str, Any]:
    # Randomly assert something about presence/role; flip truth with 50% chance
    true_statement = f"'{concept}' is discussed in the lecture excerpts."
    false_statement = f"'{concept}' is not mentioned anywhere in the lecture excerpts."
    if random.random() < 0.5:
        return {"type": "true_false", "question": true_statement, "answer": True}
    else:
        return {"type": "true_false", "question": false_statement, "answer": False}

def _make_cloze(concept: str, source_text: str) -> Dict[str, Any]:
    # Find a sentence and blank out the concept
    sentences = [s.strip() for s in source_text.split(".") if len(s.split()) > 6]
    for s in sentences:
        if concept.lower() in s.lower():
            q = s.replace(concept, "____")
            q = q.replace(concept.capitalize(), "____")
            return {"type": "cloze", "question": q, "answer": concept}
    # fallback
    return {"type": "cloze", "question": f"____ is related to: {concept}", "answer": concept}

class QuizGenerator:
    """
    0-LLM agent: builds a quiz deterministically from concepts + passages.
    """
    def __init__(self):
        pass

    def generate(self, concepts: List[str], passages: List[str], n_questions: int = 10) -> Dict[str, Any]:
        random.seed(42)
        pool = []
        # Map each concept to a passage containing it (or default)
        concept_to_text = defaultdict(lambda: passages[0] if passages else "")
        for p in passages:
            lower = p.lower()
            for c in concepts:
                if c.lower() in lower:
                    concept_to_text[c] = p

        # Build candidates of each type
        for c in concepts:
            txt = concept_to_text[c]
            pool.append(_make_mcq(c, txt))
            pool.append(_make_tf(c, txt))
            pool.append(_make_cloze(c, txt))

        # Fill MCQ options using other answers as distractors
        mcqs = [q for q in pool if q["type"] == "mcq"]
        all_defs = [q["answer"] for q in mcqs]
        for q in mcqs:
            distractors = [d for d in all_defs if d != q["answer"]]
            random.shuffle(distractors)
            q["options"] = [q["answer"]] + distractors[:3]
            random.shuffle(q["options"])

        # Sample final quiz with mix
        random.shuffle(pool)
        selected = []
        seen = set()
        for q in pool:
            key = (q["type"], q.get("question",""))  # avoid exact duplicate
            if key not in seen:
                selected.append(q)
                seen.add(key)
            if len(selected) >= n_questions:
                break

        return {
            "questions": selected,
            "count": len(selected)
        }
