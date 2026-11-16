"""
OmniSupport AI - Base LLM Client
================================
Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None  # tokens used
    raw_response: Optional[Any] = None  # original response object


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.

    All LLM providers (Gemini, OpenAI, Groq, etc.) must implement this interface.
    This ensures the RAG pipeline works with any provider.
    """

    def __init__(self, model_name: str, temperature: float = 0.3):
        """
        Initialize the LLM client.

        Args:
            model_name: Name of the model to use
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.provider_name = "base"

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """
        Generate a response from a prompt.

        Args:
            prompt: The input prompt

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    def generate_with_system(
        self,
        prompt: str,
        system_prompt: str
    ) -> LLMResponse:
        """
        Generate with a system prompt for context/instructions.

        Args:
            prompt: The user prompt
            system_prompt: System instructions (role, behavior)

        Returns:
            LLMResponse with generated content
        """
        pass

    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate a response using retrieved context (for RAG).

        Args:
            query: User's question
            context: Retrieved document context
            system_prompt: Optional system instructions

        Returns:
            LLMResponse with generated content
        """
        # Default RAG prompt template
        if system_prompt is None:
            system_prompt = """You are a helpful customer support assistant.
Answer questions based ONLY on the provided context.
If the context doesn't contain enough information to answer, say so.
Be concise and professional."""

        prompt = f"""Context:
{context}

Question: {query}

Answer based on the context above:"""

        return self.generate_with_system(prompt, system_prompt)

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        output_format: str = "json"
    ) -> LLMResponse:
        """
        Generate structured output (JSON, etc.).

        Args:
            prompt: The input prompt
            system_prompt: System instructions
            output_format: Expected format (json, list, etc.)

        Returns:
            LLMResponse with structured content
        """
        format_instruction = f"\n\nRespond in {output_format.upper()} format only."
        return self.generate_with_system(prompt + format_instruction, system_prompt)

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this LLM provider is available (API key set, etc.).

        Returns:
            True if the provider can be used
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """
        Get information about this LLM client.

        Returns:
            Dictionary with provider info
        """
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "temperature": self.temperature,
            "available": self.is_available()
        }
