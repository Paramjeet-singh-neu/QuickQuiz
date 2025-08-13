# streamlit_app.py
import streamlit as st
import tempfile
import os
from pathlib import Path
import json
from ecs.coordinator import Coordinator
from ecs.agents.document_processor import DocumentProcessor
from ecs.agents.quiz_generator import QuizGenerator
from ecs.agents.statistical_analyzer import StatisticalAnalyzer
import re
from collections import Counter

def create_offline_result(pdf_path, n_questions):
    """Generate offline mode result without LLM calls"""
    # Process PDF and extract text chunks
    dp = DocumentProcessor()
    n_chunks = dp.build_store(pdf_path)
    passages = [r["text"] for r in dp.retrieve("overview of lecture", k=6)]
    
    # Statistical analysis (0 LLM)
    stats_analyzer = StatisticalAnalyzer()
    stats_analysis = stats_analyzer.analyze_text_statistics(passages)
    
    # Generate quiz directly from text (no concept analysis)
    quiz_gen = QuizGenerator()
    
    # Extract basic concepts from text for quiz generation
    all_text = " ".join(passages)
    words = re.findall(r'\b[A-Z][a-zA-Z\s-]+\b', all_text)
    word_counts = Counter([w.strip() for w in words if len(w.strip()) > 3])
    concepts = [word for word, count in word_counts.most_common(10) if count > 1]
    
    # Generate quiz
    quiz = quiz_gen.generate(concepts, passages, n_questions=n_questions)
    
    return {
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

def main():
    st.set_page_config(
        page_title="QuickQuiz - Educational Content System",
        page_icon="��",
        layout="wide"
    )
    
    st.title("🎓 QuickQuiz: Educational Content System")
    st.markdown("Convert PDF lectures into interactive quizzes with AI-powered analysis")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Mode selection
    mode = st.sidebar.radio(
        "Select Mode:",
        ["🟢 Online (AI Analysis)", "🔴 Offline (No LLM)"],
        help="Online mode uses AI for concept analysis, Offline mode is free but basic"
    )
    
    # Question count
    n_questions = st.sidebar.slider(
        "Number of Questions:",
        min_value=5,
        max_value=30,
        value=10,
        step=5
    )
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "�� Upload PDF Lecture",
        type=['pdf'],
        help="Upload your lecture PDF file"
    )
    
    # Main content area
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name
        
        try:
            # Process based on mode
            if mode == "🟢 Online (AI Analysis)":
                # Check for OpenAI API key
                if not os.getenv('OPENAI_API_KEY'):
                    st.error("❌ OpenAI API key not found! Please set OPENAI_API_KEY environment variable.")
                    st.info("💡 You can still use Offline mode without an API key.")
                    return
                
                st.info("�� Processing with AI analysis... (1 LLM call)")
                with st.spinner("Analyzing content with AI..."):
                    app = Coordinator()
                    result = app.process_pdf_to_quiz(pdf_path, n_questions=n_questions)
                
            else:  # Offline mode
                st.info("🔴 Processing in offline mode... (0 LLM calls)")
                with st.spinner("Generating quiz without AI..."):
                    result = create_offline_result(pdf_path, n_questions)
            
            # Display results
            display_results(result, mode)
            
        except Exception as e:
            st.error(f"❌ Error processing PDF: {str(e)}")
            st.exception(e)
        finally:
            # Clean up temporary file
            os.unlink(pdf_path)
    else:
        # Welcome screen
        st.markdown("""
        ## 🚀 Get Started
        
        1. **Upload a PDF lecture** using the sidebar
        2. **Choose your mode**: Online (AI) or Offline (Free)
        3. **Configure settings**: Number of questions
        4. **Generate your quiz** and analysis!
        
        ---
        
        ### ✨ Features
        
        - **📚 PDF Processing**: Extract and analyze lecture content
        - **🧠 AI Analysis**: Generate key concepts and learning objectives
        - **�� Statistics**: Text complexity and readability metrics
        - **�� Quiz Generation**: MCQ, True/False, and Cloze questions
        - **💰 Cost Tracking**: Monitor LLM usage and costs
        - **🔄 Offline Mode**: Generate quizzes without API calls
        
        ### 🔧 Requirements
        
        - **Online Mode**: OpenAI API key required
        - **Offline Mode**: No external dependencies
        - **Both Modes**: PDF file upload
        """)

def display_results(result, mode):
    """Display quiz results and analysis"""
    
    # Create tabs for organized display
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Quiz", "📊 Statistics", "🧠 Analysis", "📈 Metrics", "🔍 Raw Data"
    ])
    
    with tab1:
        st.header("🎯 Generated Quiz")
        
        # Quiz type distribution
        quiz_types = {}
        for q in result["quiz"]["questions"]:
            quiz_types[q["type"]] = quiz_types.get(q["type"], 0) + 1
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions", len(result["quiz"]["questions"]))
        with col2:
            st.metric("MCQ Questions", quiz_types.get("mcq", 0))
        with col3:
            st.metric("True/False", quiz_types.get("true_false", 0))
        
        # Display questions
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
                else:  # cloze
                    st.write(f"**Question:** {q['question']}")
                    st.success(f"**Answer:** {q['answer']}")
    
    with tab2:
        st.header("�� Text Statistics")
        
        if "statistics" in result and "error" not in result["statistics"]:
            stats = result["statistics"]
            
            # Basic stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Words", f"{stats['basic_stats']['word_count']:,}")
                st.metric("Characters", f"{stats['basic_stats']['character_count']:,}")
            with col2:
                st.metric("Sentences", stats['basic_stats']['sentence_count'])
                st.metric("Paragraphs", stats['basic_stats']['paragraph_count'])
            with col3:
                st.metric("Avg Word Length", stats['basic_stats']['avg_word_length'])
                st.metric("Avg Sentence", f"{stats['basic_stats']['avg_sentence_length']:.1f}")
            with col4:
                st.metric("Readability Score", f"{stats['readability']['flesch_score']}")
                st.metric("Level", stats['readability']['readability_level'])
            
            # Complexity metrics
            st.subheader("🔬 Complexity Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Technical Terms", stats['complexity']['technical_terms_count'])
                st.metric("Math Expressions", stats['numerical_analysis']['math_expressions'])
            with col2:
                st.metric("Numbers Found", stats['numerical_analysis']['numbers_found'])
                st.metric("Vocabulary Diversity", f"{stats['readability']['vocabulary_diversity']:.1%}")
            
            # Technical terms list
            if stats['complexity']['technical_terms']:
                st.subheader("🔤 Top Technical Terms")
                terms_text = ", ".join(stats['complexity']['technical_terms'][:10])
                st.info(terms_text)
        else:
            st.error("Statistical analysis not available")
    
    with tab3:
        st.header("🧠 Content Analysis")
        
        analysis = result["analysis"]
        
        # Concepts
        st.subheader("🎯 Key Concepts")
        if analysis.get("concepts"):
            concepts_text = ", ".join(analysis["concepts"])
            st.info(concepts_text)
        else:
            st.warning("No concepts extracted")
        
        # Learning objectives
        st.subheader("🎓 Learning Objectives")
        if analysis.get("learning_objectives"):
            for i, obj in enumerate(analysis["learning_objectives"], 1):
                st.write(f"{i}. {obj}")
        else:
            st.warning("No learning objectives available")
        
        # Syllabus tree
        st.subheader("�� Syllabus Structure")
        if analysis.get("syllabus_tree"):
            st.json(analysis["syllabus_tree"])
        else:
            st.warning("No syllabus structure available")
    
    with tab4:
        st.header("📈 Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("LLM Calls Used", result["llm_calls_used"])
        with col2:
            st.metric("Estimated Cost", f"${result['estimated_cost']:.4f}")
        with col3:
            st.metric("Mode", "�� Online" if mode == "🟢 Online (AI Analysis)" else "🔴 Offline")
        
        # Agent status
        st.subheader("🤖 Agent Status")
        for agent, status in result["agents"].items():
            if "0 LLM" in status:
                st.success(f"✅ {agent}: {status}")
            elif "1 LLM" in status:
                st.info(f"🤖 {agent}: {status}")
            elif "SKIPPED" in status:
                st.warning(f"⏭️ {agent}: {status}")
            else:
                st.error(f"❌ {agent}: {status}")
    
    with tab5:
        st.header("�� Raw Data")
        st.json(result)

if __name__ == "__main__":
    main()
