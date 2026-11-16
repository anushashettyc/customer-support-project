"""
OmniSupport AI - Embedding Service
==================================
Generate vector embeddings for text using sentence-transformers.
"""

from typing import List, Union, Optional
import numpy as np

from sentence_transformers import SentenceTransformer

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import EMBEDDING_MODEL, EMBEDDING_DIMENSION


class EmbeddingService:
    """
    Generate embeddings using HuggingFace sentence-transformers.

    Uses the all-MiniLM-L6-v2 model by default, which produces
    384-dimensional vectors and runs locally (no API costs).
    """

    _instance = None
    _model = None

    def __new__(cls, model_name: str = EMBEDDING_MODEL):
        """
        Singleton pattern to avoid loading model multiple times.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformer model
        """
        if self._initialized:
            return

        self.model_name = model_name
        self.dimension = EMBEDDING_DIMENSION
        self._load_model()
        self._initialized = True

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            print(f"Loading embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            print(f"✅ Model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {str(e)}")

    @property
    def model(self) -> SentenceTransformer:
        """Get the loaded model."""
        if self._model is None:
            self._load_model()
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimension

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts but keep track of indices
        valid_texts = []
        valid_indices = []

        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        # Generate embeddings for valid texts
        if valid_texts:
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        else:
            embeddings = np.array([])

        # Build result with zero vectors for empty texts
        result = []
        valid_idx = 0

        for i in range(len(texts)):
            if i in valid_indices:
                result.append(embeddings[valid_idx].tolist())
                valid_idx += 1
            else:
                result.append([0.0] * self.dimension)

        return result

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        This is an alias for embed_text, but semantically indicates
        the text is a query rather than a document.

        Args:
            query: Query text to embed

        Returns:
            Embedding vector
        """
        return self.embed_text(query)

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_most_similar(
        self,
        query_embedding: List[float],
        document_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find the most similar documents to a query.

        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of document embedding vectors
            top_k: Number of top results to return

        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        similarities = []

        for i, doc_embedding in enumerate(document_embeddings):
            sim = self.compute_similarity(query_embedding, doc_embedding)
            similarities.append((i, sim))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_sequence_length": self.model.max_seq_length if self._model else None
        }


# Convenience functions
def get_embedding(text: str) -> List[float]:
    """
    Quick function to get embedding for a single text.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    service = EmbeddingService()
    return service.embed_text(text)


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Quick function to get embeddings for multiple texts.

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    service = EmbeddingService()
    return service.embed_documents(texts)
