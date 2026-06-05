# main.py
import argparse
import json

from ecs.services.quiz_service import QuizService


def main():
    parser = argparse.ArgumentParser(description="Educational Content System: PDF → Quiz")
    parser.add_argument("--pdf", required=True, help="Path to lecture PDF")
    parser.add_argument("--n", type=int, default=10, help="Number of questions")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run in offline mode (skip LLM analysis)",
    )
    args = parser.parse_args()

    service = QuizService()
    if args.offline:
        print("→ Running in OFFLINE mode (no LLM calls)")
        result = service.generate(args.pdf, n_questions=args.n, offline=True)
    else:
        print("→ Running in ONLINE mode (with LLM analysis)")
        result = service.generate(args.pdf, n_questions=args.n, offline=False)

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
        else:
            print(f"\n{i}. [CLOZE] {q['question']}")
            print(f"   → Answer: {q['answer']}")

    print("\n=== STATISTICAL ANALYSIS ===")
    if "statistics" in result:
        stats = result["statistics"]
        if "error" not in stats:
            print("TEXT STATISTICS:")
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
            print(f"Statistical Analysis Error: {stats['error']}")
    else:
        print("No statistical analysis available")

    print("\n=== ANALYSIS ===")
    print(json.dumps(result["analysis"], indent=2))

    print("\n=== METRICS ===")
    print("LLM calls used:", result["llm_calls_used"])
    print(f"Estimated cost: ${result['estimated_cost']:.4f}")
    print("Mode:", "OFFLINE" if args.offline else "ONLINE")


if __name__ == "__main__":
    main()
