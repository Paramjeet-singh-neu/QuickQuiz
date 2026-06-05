# streamlit_app.py
import os
import tempfile

import streamlit as st

from ecs.services.quiz_service import QuizService


def main():
    st.set_page_config(
        page_title="QuickQuiz - Educational Content System",
        page_icon="🎓",
        layout="wide",
    )

    st.title("QuickQuiz: Educational Content System")
    st.markdown("Convert PDF lectures into interactive quizzes with AI-powered analysis")
    st.info("For Ludwitt login, credits, and hosted storage use the new web app in `frontend/`.")

    st.sidebar.header("Configuration")
    mode = st.sidebar.radio(
        "Select Mode:",
        ["Online (AI Analysis)", "Offline (No LLM)"],
    )
    n_questions = st.sidebar.slider("Number of Questions:", 5, 30, 10, 5)
    uploaded_file = st.sidebar.file_uploader("Upload PDF Lecture", type=["pdf"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name

        try:
            service = QuizService()
            offline = mode.startswith("Offline")
            if not offline and not os.getenv("OPENAI_API_KEY"):
                st.error("OpenAI API key not found. Set OPENAI_API_KEY or use Offline mode.")
                return

            with st.spinner("Generating quiz..."):
                result = service.generate(
                    pdf_path,
                    n_questions=n_questions,
                    offline=offline,
                    source_name=uploaded_file.name,
                )
            display_results(result, mode)
        except Exception as exc:
            st.error(f"Error processing PDF: {exc}")
            st.exception(exc)
        finally:
            os.unlink(pdf_path)
    else:
        st.markdown(
            """
            ## Get Started
            1. Upload a PDF lecture using the sidebar
            2. Choose Online or Offline mode
            3. Generate your quiz and analysis
            """
        )


def display_results(result, mode):
    tab1, tab2, tab3, tab4 = st.tabs(["Quiz", "Statistics", "Analysis", "Metrics"])

    with tab1:
        st.header("Generated Quiz")
        for i, q in enumerate(result["quiz"]["questions"], start=1):
            with st.expander(f"Question {i}: {q['question'][:50]}..."):
                if q["type"] == "mcq":
                    st.write(f"**Question:** {q['question']}")
                    for j, opt in enumerate(q["options"], start=1):
                        st.write(f"{j}) {opt}")
                    st.success(f"**Answer:** {q['answer']}")
                elif q["type"] == "true_false":
                    st.write(f"**Question:** {q['question']}")
                    st.success(f"**Answer:** {q['answer']}")
                else:
                    st.write(f"**Question:** {q['question']}")
                    st.success(f"**Answer:** {q['answer']}")

    with tab2:
        stats = result.get("statistics", {})
        if stats and "error" not in stats:
            st.json(stats)
        else:
            st.error("Statistical analysis not available")

    with tab3:
        st.json(result.get("analysis", {}))

    with tab4:
        st.metric("LLM Calls Used", result["llm_calls_used"])
        st.metric("Estimated Cost", f"${result['estimated_cost']:.4f}")
        st.metric("Mode", mode)


if __name__ == "__main__":
    main()
