# main.py
import argparse, json
from ecs.coordinator import Coordinator
from ecs.agents.document_processor import DocumentProcessor
from ecs.agents.quiz_generator import QuizGenerator
from ecs.agents.statistical_analyzer import StatisticalAnalyzer

def main():
    parser = argparse.ArgumentParser(description="Educational Content System: PDF → Quiz")
    parser.add_argument("--pdf", required=True, help="Path to lecture PDF")
    parser.add_argument("--n", type=int, default=10, help="Number of questions")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode (skip LLM analysis)")
    args = parser.parse_args()

    if args.offline:
        # Offline mode: skip ContentAnalyzer, use only DocumentProcessor + QuizGenerator + StatisticalAnalyzer
        print("→ Running in OFFLINE mode (no LLM calls)")
        
        # Process PDF and extract text chunks
        dp = DocumentProcessor()
        print("→ DocumentProcessor: building vector store… (0 LLM)")
        n_chunks = dp.build_store(args.pdf)
        print(f"  Added {n_chunks} chunks. Retrieving passages…")
        
        # Get passages for quiz generation
        passages = [r["text"] for r in dp.retrieve("overview of lecture", k=6)]
        
        # Statistical analysis (0 LLM)
        print("→ StatisticalAnalyzer: analyzing text statistics… (0 LLM)")
        stats_analyzer = StatisticalAnalyzer()
        stats_analysis = stats_analyzer.analyze_text_statistics(passages)
        
        # Generate quiz directly from text (no concept analysis)
        print("→ QuizGenerator: creating quiz from text… (0 LLM)")
        quiz_gen = QuizGenerator()
        
        # Extract basic concepts from text for quiz generation
        # Simple heuristic: find key terms that appear multiple times
        import re
        from collections import Counter
        
        # Find potential concepts (words that appear multiple times and are capitalized)
        all_text = " ".join(passages)
        words = re.findall(r'\b[A-Z][a-zA-Z\s-]+\b', all_text)
        word_counts = Counter([w.strip() for w in words if len(w.strip()) > 3])
        concepts = [word for word, count in word_counts.most_common(10) if count > 1]
        
        # Generate quiz
        quiz = quiz_gen.generate(concepts, passages, n_questions=args.n)
        
        result = {
            "quiz": quiz,
            "analysis": {
                "concepts": concepts,
                "learning_objectives": ["Offline mode: objectives not analyzed"],
                "syllabus_tree": {"Offline Mode": ["Text-based quiz generation"]}
            },
            "statistics": stats_analysis,
            "llm_calls_used": 0,
            "estimated_cost": 0.0,
            "agents": {
                "DocumentProcessor": "0 LLM",
                "ContentAnalyzer": "SKIPPED (offline)",
                "StatisticalAnalyzer": "0 LLM",
                "QuizGenerator": "0 LLM",
            }
        }
        
    else:
        # Online mode: use full Coordinator with LLM analysis
        print("→ Running in ONLINE mode (with LLM analysis)")
        app = Coordinator()
        result = app.process_pdf_to_quiz(args.pdf, n_questions=args.n)

    print("\n=== QUIZ (with answers) ===")
    for i, q in enumerate(result["quiz"]["questions"], start=1):
        if q["type"] == "mcq":
            print(f"\n{i}. [MCQ] {q['question']}")
            for j, opt in enumerate(q["options"], start=1):
                print(f"   {j}) {opt}")
            print(f"   → Answer: {q['answer']}")
        elif q["type"] == "true_false":
            print(f"\n{i}. [T/F] {q['question']}")
            print(f"   → Answer: {q['answer']}")
        else:  # cloze
            print(f"\n{i}. [CLOZE] {q['question']}")
            print(f"   → Answer: {q['answer']}")

    print("\n=== STATISTICAL ANALYSIS ===")
    if "statistics" in result:
        stats = result["statistics"]
        if "error" not in stats:
            print("📊 TEXT STATISTICS:")
            basic = stats["basic_stats"]
            readability = stats["readability"]
            print(f"• Words: {basic['word_count']:,} | Characters: {basic['character_count']:,}")
            print(f"• Sentences: {basic['sentence_count']} | Paragraphs: {basic['paragraph_count']}")
            print(f"• Avg Word Length: {basic['avg_word_length']} | Avg Sentence: {basic['avg_sentence_length']:.1f}")
            print(f"• Readability: {readability['flesch_score']} ({readability['readability_level']})")
            print(f"• Technical Terms: {stats['complexity']['technical_terms_count']}")
            print(f"• Math Expressions: {stats['numerical_analysis']['math_expressions']}")
            print(f"• Numbers Found: {stats['numerical_analysis']['numbers_found']}")
        else:
            print(f"❌ Statistical Analysis Error: {stats['error']}")
    else:
        print("❌ No statistical analysis available")

    print("\n=== ANALYSIS ===")
    print(json.dumps(result["analysis"], indent=2))

    print("\n=== METRICS ===")
    print("LLM calls used:", result["llm_calls_used"])
    print("Estimated cost:", f"${result['estimated_cost']:.4f}")
    if args.offline:
        print("Mode: OFFLINE (no LLM calls)")
    else:
        print("Mode: ONLINE (with LLM analysis)")

if __name__ == "__main__":
    main()