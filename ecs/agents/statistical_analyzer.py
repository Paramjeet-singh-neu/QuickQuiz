# ecs/agents/statistical_analyzer.py
import re
import statistics
from typing import Dict, Any, List, Tuple
from collections import Counter
import math

class StatisticalAnalyzer:
    """
    0-LLM agent: performs statistical analysis on extracted text data.
    Provides insights like readability scores, complexity metrics, and text statistics.
    """
    
    def __init__(self):
        self.analysis_count = 0
    
    def analyze_text_statistics(self, passages: List[str]) -> Dict[str, Any]:
        """
        Analyze text passages and return comprehensive statistics.
        """
        try:
            self.analysis_count += 1
            
            # Combine all passages for analysis
            combined_text = " ".join(passages)
            
            # Basic text statistics
            word_count = len(combined_text.split())
            char_count = len(combined_text)
            sentence_count = len(re.split(r'[.!?]+', combined_text))
            paragraph_count = len([p for p in passages if p.strip()])
            
            # Word length analysis
            words = re.findall(r'\b\w+\b', combined_text.lower())
            word_lengths = [len(word) for word in words if word]
            
            # Readability metrics
            avg_word_length = statistics.mean(word_lengths) if word_lengths else 0
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Flesch Reading Ease approximation (simplified)
            flesch_score = self._calculate_flesch_score(avg_word_length, avg_sentence_length)
            
            # Complexity metrics
            unique_words = set(words)
            vocabulary_diversity = len(unique_words) / word_count if word_count > 0 else 0
            
            # Technical term analysis
            technical_terms = self._extract_technical_terms(combined_text)
            
            # Numerical data extraction
            numbers = self._extract_numbers(combined_text)
            
            # Mathematical expressions
            math_expressions = self._extract_math_expressions(combined_text)
            
            return {
                "basic_stats": {
                    "word_count": word_count,
                    "character_count": char_count,
                    "sentence_count": sentence_count,
                    "paragraph_count": paragraph_count,
                    "avg_word_length": round(avg_word_length, 2),
                    "avg_sentence_length": round(avg_sentence_length, 2)
                },
                "readability": {
                    "flesch_score": round(flesch_score, 2),
                    "readability_level": self._get_readability_level(flesch_score),
                    "vocabulary_diversity": round(vocabulary_diversity, 3)
                },
                "complexity": {
                    "technical_terms_count": len(technical_terms),
                    "technical_terms": technical_terms[:10],  # Top 10
                    "unique_words_ratio": round(vocabulary_diversity, 3)
                },
                "numerical_analysis": {
                    "numbers_found": len(numbers),
                    "number_types": self._categorize_numbers(numbers),
                    "math_expressions": len(math_expressions)
                },
                "text_quality": {
                    "analysis_timestamp": self.analysis_count,
                    "data_quality": "high" if word_count > 100 else "medium"
                }
            }
            
        except Exception as e:
            # Error handling for statistical analysis failures
            return {
                "error": f"Statistical analysis failed: {str(e)}",
                "fallback_stats": {
                    "word_count": len(" ".join(passages).split()),
                    "status": "analysis_failed"
                }
            }
    
    def _calculate_flesch_score(self, avg_word_length: float, avg_sentence_length: float) -> float:
        """
        Calculate simplified Flesch Reading Ease score.
        Higher score = easier to read.
        """
        try:
            # Simplified formula: 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
            score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
            return max(0, min(100, score))  # Clamp between 0-100
        except:
            return 50.0  # Default middle score
    
    def _get_readability_level(self, flesch_score: float) -> str:
        """Convert Flesch score to readability level."""
        if flesch_score >= 90:
            return "Very Easy"
        elif flesch_score >= 80:
            return "Easy"
        elif flesch_score >= 70:
            return "Fairly Easy"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Fairly Difficult"
        elif flesch_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract potential technical terms (capitalized words that appear multiple times)."""
        try:
            # Find capitalized words that might be technical terms
            technical_pattern = r'\b[A-Z][a-zA-Z\s-]{2,}\b'
            matches = re.findall(technical_pattern, text)
            
            # Count occurrences and return most frequent
            term_counts = Counter([term.strip() for term in matches if len(term.strip()) > 2])
            return [term for term, count in term_counts.most_common(15) if count > 1]
        except:
            return []
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numerical values from text."""
        try:
            # Find various number formats
            number_patterns = [
                r'\b\d+\.\d+\b',  # Decimal numbers
                r'\b\d+\b',        # Whole numbers
                r'\b\d+[eE][+-]?\d+\b',  # Scientific notation
            ]
            
            numbers = []
            for pattern in number_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        numbers.append(float(match))
                    except ValueError:
                        continue
            
            return numbers
        except:
            return []
    
    def _categorize_numbers(self, numbers: List[float]) -> Dict[str, int]:
        """Categorize numbers by type."""
        try:
            categories = {
                "integers": len([n for n in numbers if n.is_integer()]),
                "decimals": len([n for n in numbers if not n.is_integer()]),
                "positive": len([n for n in numbers if n > 0]),
                "negative": len([n for n in numbers if n < 0]),
                "zero": len([n for n in numbers if n == 0])
            }
            return categories
        except:
            return {"integers": 0, "decimals": 0, "positive": 0, "negative": 0, "zero": 0}
    
    def _extract_math_expressions(self, text: str) -> List[str]:
        """Extract mathematical expressions and formulas."""
        try:
            # Find patterns that look like math expressions
            math_patterns = [
                r'[a-zA-Z]\s*=\s*[^=]+',  # Variable assignments
                r'[a-zA-Z]\s*\+\s*[a-zA-Z]',  # Addition expressions
                r'[a-zA-Z]\s*\*\s*[a-zA-Z]',  # Multiplication expressions
                r'[a-zA-Z]\s*/\s*[a-zA-Z]',   # Division expressions
                r'[a-zA-Z]\^[0-9]',           # Exponents
                r'∫[^∫]+',                    # Integrals
                r'∑[^∑]+',                    # Summations
            ]
            
            expressions = []
            for pattern in math_patterns:
                matches = re.findall(pattern, text)
                expressions.extend(matches)
            
            return list(set(expressions))  # Remove duplicates
        except:
            return []
    
    def get_analysis_summary(self, passages: List[str]) -> str:
        """Get a human-readable summary of the statistical analysis."""
        try:
            stats = self.analyze_text_statistics(passages)
            
            if "error" in stats:
                return f"Analysis Error: {stats['error']}"
            
            basic = stats["basic_stats"]
            readability = stats["readability"]
            
            summary = f"""
📊 TEXT STATISTICS SUMMARY:
• Words: {basic['word_count']:,} | Characters: {basic['character_count']:,}
• Sentences: {basic['sentence_count']} | Paragraphs: {basic['paragraph_count']}
• Avg Word Length: {basic['avg_word_length']} | Avg Sentence: {basic['avg_sentence_length']:.1f}

📖 READABILITY:
• Flesch Score: {readability['flesch_score']} ({readability['readability_level']})
• Vocabulary Diversity: {readability['vocabulary_diversity']:.1%}

🔬 COMPLEXITY:
• Technical Terms: {stats['complexity']['technical_terms_count']}
• Math Expressions: {stats['numerical_analysis']['math_expressions']}
• Numbers Found: {stats['numerical_analysis']['numbers_found']}
            """.strip()
            
            return summary
            
        except Exception as e:
            return f"Failed to generate summary: {str(e)}"