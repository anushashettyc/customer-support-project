"""
OmniSupport AI - RAG Chain
==========================
Retrieval-Augmented Generation pipeline.
Combines vector search with LLM generation for grounded responses.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import TOP_K_RESULTS
from src.llm.base_client import BaseLLMClient, LLMResponse
from src.llm.llm_factory import get_llm_client
from src.vectorstore.chroma_store import ChromaStore, SearchResult


@dataclass
class RAGResponse:
    """Response from the RAG pipeline."""
    answer: str
    sources: List[Dict[str, Any]]
    query: str
    context_used: str
    llm_response: Optional[LLMResponse] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGChain:
    """
    Retrieval-Augmented Generation pipeline.

    Flow:
    1. User query → Embed
    2. Search vector store for relevant chunks
    3. Build prompt with retrieved context
    4. Send to LLM
    5. Return grounded response with sources
    """

    # Default system prompt for customer support
    DEFAULT_SYSTEM_PROMPT = """You are an expert customer support assistant for OmniSupport.

Your role is to help customers with their inquiries about:
- Return policies
- Refund procedures
- Warranty claims
- VIP/loyalty benefits
- Damaged goods procedures

IMPORTANT RULES:
1. Answer ONLY based on the provided context/policy documents
2. If the context doesn't contain enough information, say "I don't have enough information to answer that based on our policies"
3. Be concise, professional, and helpful
4. Quote specific policy details when relevant (e.g., "According to our return policy, you have 30 days...")
5. If the customer mentions an order ID or is a specific tier (Gold, Platinum), consider their benefits
6. Never make up information not in the context

Format your response clearly and professionally."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        vector_store: Optional[ChromaStore] = None,
        top_k: int = TOP_K_RESULTS,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the RAG chain.

        Args:
            llm_client: LLM client (auto-detected if not provided)
            vector_store: Vector store for retrieval
            top_k: Number of documents to retrieve
            system_prompt: Custom system prompt
        """
        self.llm_client = llm_client or get_llm_client()
        self.vector_store = vector_store or ChromaStore()
        self.top_k = top_k
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        print(f"✅ RAG Chain initialized with {self.llm_client.provider_name}")

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None,
        include_sources: bool = True
    ) -> RAGResponse:
        """
        Process a query through the RAG pipeline.

        Args:
            question: User's question
            top_k: Override number of documents to retrieve
            filter_metadata: Optional filter for retrieval
            include_sources: Whether to include source information

        Returns:
            RAGResponse with answer and sources
        """
        k = top_k or self.top_k

        # Step 1: Retrieve relevant documents
        search_results = self.vector_store.search(
            query_text=question,
            top_k=k,
            filter_metadata=filter_metadata
        )

        if not search_results:
            return RAGResponse(
                answer="I couldn't find any relevant information in our knowledge base to answer your question.",
                sources=[],
                query=question,
                context_used="",
                metadata={"retrieval_count": 0}
            )

        # Step 2: Build context from retrieved documents
        context = self._build_context(search_results)

        # Step 3: Generate response using LLM
        llm_response = self.llm_client.generate_with_context(
            query=question,
            context=context,
            system_prompt=self.system_prompt
        )

        # Step 4: Format sources
        sources = []
        if include_sources:
            sources = [
                {
                    "text": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                    "source": r.metadata.get("source", "unknown"),
                    "score": round(r.score, 4),
                    "chunk_index": r.metadata.get("chunk_index", 0)
                }
                for r in search_results
            ]

        return RAGResponse(
            answer=llm_response.content,
            sources=sources,
            query=question,
            context_used=context,
            llm_response=llm_response,
            metadata={
                "retrieval_count": len(search_results),
                "model": llm_response.model,
                "provider": llm_response.provider,
                "tokens": llm_response.usage
            }
        )

    def _build_context(self, search_results: List[SearchResult]) -> str:
        """
        Build context string from search results.

        Args:
            search_results: List of retrieved documents

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, result in enumerate(search_results, 1):
            source = result.metadata.get("source", "unknown")
            context_parts.append(
                f"[Source {i}: {source}]\n{result.text}"
            )

        return "\n\n---\n\n".join(context_parts)

    def query_with_order_context(
        self,
        question: str,
        order_info: Dict[str, Any],
        top_k: Optional[int] = None
    ) -> RAGResponse:
        """
        Query with additional order context (for customer support scenarios).

        Args:
            question: User's question
            order_info: Dictionary with order details
            top_k: Number of documents to retrieve

        Returns:
            RAGResponse with answer considering order context
        """
        # Build order context
        order_context = self._format_order_context(order_info)

        # Retrieve policy documents
        k = top_k or self.top_k
        search_results = self.vector_store.search(
            query_text=question,
            top_k=k
        )

        # Build full context
        policy_context = self._build_context(search_results) if search_results else ""

        full_context = f"""CUSTOMER ORDER INFORMATION:
{order_context}

RELEVANT POLICY DOCUMENTS:
{policy_context}"""

        # Generate response
        llm_response = self.llm_client.generate_with_context(
            query=question,
            context=full_context,
            system_prompt=self.system_prompt
        )

        # Format sources
        sources = [
            {
                "text": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                "source": r.metadata.get("source", "unknown"),
                "score": round(r.score, 4)
            }
            for r in search_results
        ]

        return RAGResponse(
            answer=llm_response.content,
            sources=sources,
            query=question,
            context_used=full_context,
            llm_response=llm_response,
            metadata={
                "retrieval_count": len(search_results),
                "order_id": order_info.get("order_id"),
                "customer_tier": order_info.get("loyalty_tier")
            }
        )

    def _format_order_context(self, order_info: Dict[str, Any]) -> str:
        """Format order information for context."""
        if not order_info:
            return "No order information available."

        lines = [
            f"Order ID: {order_info.get('order_id', 'N/A')}",
            f"Customer: {order_info.get('customer_name', 'N/A')}",
            f"Email: {order_info.get('email', 'N/A')}",
            f"Product: {order_info.get('product_name', 'N/A')}",
            f"Price: ${order_info.get('total_price', 0):.2f}",
            f"Order Date: {order_info.get('order_date', 'N/A')}",
            f"Delivery Date: {order_info.get('delivery_date', 'N/A')}",
            f"Status: {order_info.get('status', 'N/A')}",
            f"Loyalty Tier: {order_info.get('loyalty_tier', 'Bronze')}",
        ]

        if order_info.get('notes'):
            lines.append(f"Notes: {order_info.get('notes')}")

        return "\n".join(lines)

    def simple_query(self, question: str) -> str:
        """
        Simple query that returns just the answer string.

        Args:
            question: User's question

        Returns:
            Answer string
        """
        response = self.query(question)
        return response.answer

    def get_info(self) -> Dict[str, Any]:
        """Get information about the RAG chain configuration."""
        return {
            "llm_provider": self.llm_client.provider_name,
            "llm_model": self.llm_client.model_name,
            "top_k": self.top_k,
            "vector_store": self.vector_store.get_collection_stats()
        }


# Global RAG chain instance
_rag_chain_instance: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """
    Get the global RAG chain instance (singleton).

    Returns:
        RAGChain instance
    """
    global _rag_chain_instance

    if _rag_chain_instance is None:
        _rag_chain_instance = RAGChain()

    return _rag_chain_instance


def ask(question: str) -> str:
    """
    Quick function to ask a question.

    Args:
        question: User's question

    Returns:
        Answer string
    """
    chain = get_rag_chain()
    return chain.simple_query(question)
