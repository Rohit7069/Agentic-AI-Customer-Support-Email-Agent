"""Vector knowledge base service using FAISS + OpenAI embeddings."""
import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI
from src.config import settings
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class VectorKBService(BaseService):
    """Vector-based knowledge base using FAISS + OpenAI embeddings."""

    EMBEDDING_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(self):
        super().__init__()
        self.embedding_model = settings.EMBEDDING_MODEL
        self.index_path = settings.KB_INDEX_PATH
        self.documents_path = settings.KB_DOCUMENTS_PATH
        self.faiss_index = None
        self.documents: Dict[int, Dict[str, Any]] = {}
        self.doc_counter = 0
        self.client = None

    async def initialize(self) -> None:
        """Initialize with OpenAI client and FAISS index."""
        import faiss

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        embedding_dim = self.EMBEDDING_DIMENSIONS.get(
            self.embedding_model, 1536
        )

        # Create data directory if needed
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

        # Load existing index or create new one
        if os.path.exists(self.index_path):
            self.faiss_index = faiss.read_index(self.index_path)
            # Load documents metadata
            if os.path.exists(self.documents_path):
                with open(self.documents_path, "r") as f:
                    data = json.load(f)
                    self.documents = {int(k): v for k, v in data.get("documents", {}).items()}
                    self.doc_counter = data.get("doc_counter", 0)
        else:
            self.faiss_index = faiss.IndexFlatL2(embedding_dim)

    async def add_document(
        self, title: str, content: str,
        category: str, source_url: str = ""
    ) -> int:
        """Add a document to the knowledge base."""
        import faiss

        self.doc_counter += 1
        doc_id = self.doc_counter

        # Get embedding
        embedding = await self._get_embedding(f"{title} {content}")

        # Add to FAISS index
        self.faiss_index.add(embedding)

        # Store metadata
        self.documents[doc_id] = {
            "title": title,
            "content": content,
            "category": category,
            "source_url": source_url,
        }

        return doc_id

    async def save(self) -> None:
        """Save the FAISS index and documents to disk."""
        import faiss

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.faiss_index, self.index_path)

        with open(self.documents_path, "w") as f:
            json.dump({
                "documents": self.documents,
                "doc_counter": self.doc_counter,
            }, f, indent=2)

        logger.info(f"Saved {self.doc_counter} documents to knowledge base")

    async def search(
        self, query: str, category: Optional[str] = None,
        limit: int = 5, threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Semantic similarity search."""
        if not self.faiss_index or self.doc_counter == 0:
            return []

        query_embedding = await self._get_embedding(query)

        k = min(limit * 2, self.doc_counter)
        if k == 0:
            return []

        distances, indices = self.faiss_index.search(query_embedding, k=k)

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            doc = self.documents.get(idx + 1)
            if not doc:
                continue

            # Convert L2 distance to similarity score
            similarity = 1 / (1 + float(distance))

            if similarity < threshold:
                continue

            if category and doc.get("category") != category:
                continue

            results.append({
                "title": doc["title"],
                "content": doc["content"],
                "category": doc.get("category", ""),
                "similarity_score": float(similarity),
                "source_url": doc.get("source_url", ""),
            })

        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]

    async def format_context(self, kb_results: List[Dict[str, Any]]) -> str:
        """Format knowledge base results for LLM consumption."""
        if not kb_results:
            return "No additional context available."

        context_parts = []
        for i, result in enumerate(kb_results, 1):
            context_parts.append(
                f"Article {i}: {result['title']}\n"
                f"Content: {result['content']}\n"
                f"Relevance: {result['similarity_score']:.2f}"
            )

        return "\n\n".join(context_parts)

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get OpenAI embedding for text."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        embedding = response.data[0].embedding
        return np.array([embedding], dtype=np.float32)
