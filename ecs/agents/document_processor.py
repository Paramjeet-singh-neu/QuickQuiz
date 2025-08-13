# ecs/agents/document_processor.py
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from ecs.utils.text import clean_text, chunk_text

class DocumentProcessor:
    """
    0-LLM agent: extracts text, chunks, embeds, and builds a vector store.
    """
    def __init__(self, persist_dir: str = ".chroma_store", collection_name: str = "lecture"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")  # fast, high-quality
        self.client = chromadb.PersistentClient(path=self.persist_dir, settings=Settings(allow_reset=True))
        # Create or get collection
        self.collection = self.client.get_or_create_collection(self.collection_name)

    def _read_pdf(self, pdf_path: str) -> str:
        reader = PdfReader(pdf_path)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    def build_store(self, pdf_path: str, chunk_size=800, overlap=120) -> int:
        raw = self._read_pdf(pdf_path)
        text = clean_text(raw)
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        # Reset collection
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(self.collection_name)

        # Embed and add to Chroma
        embeddings = self.embedder.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
        ids = [f"doc_{i}" for i in range(len(chunks))]
        self.collection.add(ids=ids, documents=chunks, embeddings=embeddings.tolist(), metadatas=[{"source": pdf_path}] * len(chunks))
        return len(chunks)

    def retrieve(self, query: str, k: int = 6) -> List[Dict[str, Any]]:
        q_emb = self.embedder.encode([query], convert_to_numpy=True)
        res = self.collection.query(query_embeddings=q_emb.tolist(), n_results=k)
        # Pack results
        out = []
        for i in range(len(res["ids"][0])):
            out.append({
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "distance": res["distances"][0][i]
            })
        return out
