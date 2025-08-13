# ecs/utils/text.py
import re
from typing import List

def clean_text(text: str) -> str:
    # Remove excessive whitespace, newlines, hyphenated line breaks, etc.
    text = text.replace("\r", " ")
    text = re.sub(r"-\s*\n\s*", "", text)       # join hyphenated breaks
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

def chunk_text(text: str, chunk_size=800, overlap=120) -> List[str]:
    # Simple word-based sliding window chunking
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks
