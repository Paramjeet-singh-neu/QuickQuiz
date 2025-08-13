# QuickQuiz: Educational Content System

An intelligent system that converts PDF lectures into interactive quizzes with AI-powered analysis and statistical insights.

## 🚀 Features

- **PDF Processing:** Extract and chunk text from lecture PDFs
- **AI Analysis:** Generate key concepts and learning objectives using GPT-4
- **Quiz Generation:** Create MCQ, True/False, and Cloze questions automatically
- **Statistical Analysis:** Text complexity, readability scores, and mathematical content analysis
- **Offline Mode:** Generate quizzes without LLM calls (zero cost)
- **Cost Tracking:** Monitor LLM usage and estimated costs

## 📋 Requirements

- Python 3.9+
- OpenAI API key (for online mode)
- 2GB+ RAM (for sentence transformers)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd FinalProject_QuickQuiz
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=sk-your-key-here" > .env
   echo "MODEL_NAME=gpt-4o-mini" >> .env
   echo "ECONOMY_COST_PER_CALL=0.002" >> .env
   
   # Export to shell
   export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2)
   ```

## 🎯 Usage Examples

### Online Mode (Full AI Analysis)
```bash
python main.py --pdf "data/lecture.pdf" --n 10
```
- Generates concepts, objectives, and structured quiz
- Uses 1 LLM call (~$0.002 cost)
- Best quality results

### Offline Mode (Zero Cost)
```bash
python main.py --pdf "data/lecture.pdf" --n 10 --offline
```
- Generates quiz without LLM calls
- Zero cost, fast processing
- Basic concept extraction

### Custom Question Count
```bash
python main.py --pdf "data/lecture.pdf" --n 20
```
- Generate any number of questions
- Mix of MCQ, True/False, and Cloze

## ��️ Architecture

### Agents
- **DocumentProcessor (0-LLM):** PDF text extraction and vector storage
- **ContentAnalyzer (1-LLM):** AI-powered concept and objective analysis
- **StatisticalAnalyzer (0-LLM):** Text complexity and readability metrics
- **QuizGenerator (0-LLM):** Deterministic quiz generation

### Workflow
1. PDF → Text chunks → Vector store
2. Semantic retrieval → Content analysis
3. Statistical analysis → Quiz generation
4. Comprehensive reporting

## 📊 Performance Metrics

- **LLM Calls:** 0-1 per request (≤2 requirement exceeded)
- **Cost:** $0.0000 (offline) to $0.0020 (online)
- **Processing Time:** <30 seconds for typical PDFs
- **Accuracy:** High-quality AI analysis with fallback handling

## �� Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `MODEL_NAME`: LLM model (default: gpt-4o-mini)
- `ECONOMY_COST_PER_CALL`: Cost per LLM call (default: 0.002)

### Customization
- Chunk size and overlap in DocumentProcessor
- Question types in QuizGenerator
- Analysis depth in ContentAnalyzer

## 🧪 Testing

### Test Scenarios
1. **Basic PDF Processing:**
   ```bash
   python main.py --pdf "data/sample.pdf" --n 5
   ```

2. **Offline Mode:**
   ```bash
   python main.py --pdf "data/sample.pdf" --n 5 --offline
   ```

3. **Large Document:**
   ```bash
   python main.py --pdf "data/large_lecture.pdf" --n 20
   ```

## 🚨 Troubleshooting

### Common Issues
- **Import errors:** Ensure virtual environment is activated
- **PDF reading errors:** Check PDF format and permissions
- **LLM errors:** Verify OpenAI API key and internet connection
- **Memory issues:** Reduce chunk size for large documents

### Error Handling
- Graceful fallbacks for LLM failures
- Validation error handling for malformed responses
- Comprehensive error reporting

## 📈 Future Enhancements

- Support for more document formats (DOCX, TXT)
- Advanced question generation algorithms
- Integration with learning management systems
- Real-time collaboration features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request



## 👥 Authors

Paramjeet Singh
Northeastern University

## �� Acknowledgments

- OpenAI for GPT models
- Hugging Face for sentence transformers
- ChromaDB for vector storage