"""
OmniSupport AI - ChromaDB Vector Store
======================================
Store and retrieve document embeddings using ChromaDB.
"""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import VECTORSTORE_DIR, CHROMA_COLLECTION_NAME, TOP_K_RESULTS
from src.embeddings.embedding_service import EmbeddingService


@dataclass
class SearchResult:
    """Represents a search result from the vector store."""
    text: str
    metadata: dict
    score: float
    doc_id: str


class ChromaStore:
    """
    Vector store using ChromaDB for semantic search.

    Provides methods to:
    - Add documents with embeddings
    - Search for similar documents
    - Delete documents
    - Manage collections
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern to maintain single database connection.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = CHROMA_COLLECTION_NAME
    ):
        """
        Initialize the ChromaDB store.

        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        if self._initialized:
            return

        self.persist_directory = persist_directory or str(VECTORSTORE_DIR)
        self.collection_name = collection_name
        self.embedding_service = EmbeddingService()

        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self._init_client()
        self._initialized = True

    def _init_client(self):
        """Initialize the ChromaDB client and collection."""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "OmniSupport AI Knowledge Base"}
            )

            print(f"✅ ChromaDB initialized. Collection: {self.collection_name}")
            print(f"   Documents in collection: {self.collection.count()}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB: {str(e)}")

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dicts for each document
            ids: Optional list of unique IDs (auto-generated if not provided)
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs
        """
        if not texts:
            return []

        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i:06d}" for i in range(len(texts))]

        # Generate embeddings if not provided
        if embeddings is None:
            embeddings = self.embedding_service.embed_documents(texts)

        # Ensure metadatas exist
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in texts]

        # Add to collection
        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Added {len(texts)} documents to vector store")
            return ids

        except Exception as e:
            raise RuntimeError(f"Failed to add documents: {str(e)}")

    def search(
        self,
        query_text: str,
        top_k: int = TOP_K_RESULTS,
        filter_metadata: Optional[dict] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents.

        Args:
            query_text: Text to search for
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult objects
        """
        if not query_text or not query_text.strip():
            return []

        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query_text)

        # Build query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }

        if filter_metadata:
            query_params["where"] = filter_metadata

        # Execute search
        try:
            results = self.collection.query(**query_params)

            # Convert to SearchResult objects
            search_results = []

            if results and results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
                distances = results['distances'][0] if results['distances'] else [0.0] * len(documents)
                ids = results['ids'][0] if results['ids'] else [''] * len(documents)

                for doc, meta, dist, doc_id in zip(documents, metadatas, distances, ids):
                    # Convert distance to similarity score (ChromaDB returns L2 distance)
                    # Lower distance = more similar, so we convert
                    similarity = 1 / (1 + dist)

                    search_results.append(SearchResult(
                        text=doc,
                        metadata=meta,
                        score=similarity,
                        doc_id=doc_id
                    ))

            return search_results

        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

    def search_with_scores(
        self,
        query_text: str,
        top_k: int = TOP_K_RESULTS
    ) -> List[tuple]:
        """
        Search and return results as (text, score) tuples.

        Args:
            query_text: Text to search for
            top_k: Number of results

        Returns:
            List of (text, score) tuples
        """
        results = self.search(query_text, top_k)
        return [(r.text, r.score) for r in results]

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[doc_id])
            print(f"✅ Deleted document: {doc_id}")
            return True
        except Exception as e:
            print(f"Delete error: {str(e)}")
            return False

    def delete_by_metadata(self, metadata_filter: dict) -> int:
        """
        Delete documents matching metadata filter.

        Args:
            metadata_filter: Metadata filter (e.g., {"source": "file.txt"})

        Returns:
            Number of documents deleted
        """
        try:
            # First, find documents matching the filter
            results = self.collection.get(
                where=metadata_filter,
                include=["metadatas"]
            )

            if results and results['ids']:
                ids_to_delete = results['ids']
                self.collection.delete(ids=ids_to_delete)
                print(f"✅ Deleted {len(ids_to_delete)} documents matching filter")
                return len(ids_to_delete)

            return 0

        except Exception as e:
            print(f"Delete by metadata error: {str(e)}")
            return 0

    def get_document(self, doc_id: str) -> Optional[dict]:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Dictionary with document data or None
        """
        try:
            result = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas", "embeddings"]
            )

            if result and result['documents']:
                return {
                    "id": doc_id,
                    "text": result['documents'][0],
                    "metadata": result['metadatas'][0] if result['metadatas'] else {}
                }

            return None

        except Exception as e:
            print(f"Get document error: {str(e)}")
            return None

    def get_all_documents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """
        Get all documents from the collection.

        Args:
            limit: Maximum documents to return
            offset: Starting offset

        Returns:
            List of document dictionaries
        """
        try:
            result = self.collection.get(
                limit=limit,
                offset=offset,
                include=["documents", "metadatas"]
            )

            documents = []
            if result and result['ids']:
                for i, doc_id in enumerate(result['ids']):
                    documents.append({
                        "id": doc_id,
                        "text": result['documents'][i] if result['documents'] else "",
                        "metadata": result['metadatas'][i] if result['metadatas'] else {}
                    })

            return documents

        except Exception as e:
            print(f"Get all documents error: {str(e)}")
            return []

    def clear_collection(self) -> bool:
        """
        Delete all documents from the collection.

        Returns:
            True if successful
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "OmniSupport AI Knowledge Base"}
            )
            print(f"✅ Collection cleared: {self.collection_name}")
            return True

        except Exception as e:
            print(f"Clear collection error: {str(e)}")
            return False

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()

            # Get unique sources
            all_docs = self.get_all_documents(limit=1000)
            sources = set()
            for doc in all_docs:
                if doc.get('metadata', {}).get('source'):
                    sources.add(doc['metadata']['source'])

            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "unique_sources": len(sources),
                "sources": list(sources),
                "persist_directory": self.persist_directory
            }

        except Exception as e:
            return {"error": str(e)}

    def document_exists(self, source: str) -> bool:
        """
        Check if documents from a source already exist.

        Args:
            source: Source filename

        Returns:
            True if documents from this source exist
        """
        try:
            result = self.collection.get(
                where={"source": source},
                limit=1
            )
            return bool(result and result['ids'])

        except Exception as e:
            return False


# Convenience function
def get_vector_store() -> ChromaStore:
    """
    Get the singleton vector store instance.

    Returns:
        ChromaStore instance
    """
    return ChromaStore()
