"""
OmniSupport AI - LLM Factory
============================
Simplified factory - Groq only for fast, reliable inference.
"""

import os
from typing import Optional

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.llm.base_client import BaseLLMClient
from src.llm.groq_client import GroqClient


def get_llm_client(
    model_name: str = None,
    temperature: float = None,
    api_key: str = None
) -> BaseLLMClient:
    """
    Get a Groq LLM client instance.

    Args:
        model_name: Model to use (default: llama-3.3-70b-versatile)
        temperature: Creativity level (0.0-1.0)
        api_key: API key (optional, defaults to GROQ_API_KEY env var)

    Returns:
        Configured Groq client

    Raises:
        ValueError: If GROQ_API_KEY is not set
    """
    # Check for API key
    key = api_key or os.getenv("GROQ_API_KEY")

    if not key or key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY not set!\n\n"
            "Get your FREE API key:\n"
            "  1. Go to: https://console.groq.com/keys\n"
            "  2. Sign up (free)\n"
            "  3. Create API key\n"
            "  4. Add to .env file:\n"
            "     GROQ_API_KEY=gsk_your_key_here\n"
        )

    # Build kwargs
    kwargs = {"api_key": key}
    if model_name:
        kwargs["model_name"] = model_name
    if temperature is not None:
        kwargs["temperature"] = temperature

    return GroqClient(**kwargs)


def get_llm_client_safe(**kwargs) -> Optional[BaseLLMClient]:
    """
    Get an LLM client, returning None if not available.

    Returns:
        LLM client or None if not available
    """
    try:
        return get_llm_client(**kwargs)
    except (ValueError, ImportError, RuntimeError):
        return None


# Alias for backwards compatibility
def get_groq_client(**kwargs) -> BaseLLMClient:
    """Get a Groq client."""
    return get_llm_client(**kwargs)


def print_provider_status():
    """Print Groq provider status."""
    print("\n" + "=" * 50)
    print("LLM Provider: Groq")
    print("=" * 50)

    key = os.getenv("GROQ_API_KEY")
    has_key = key and key != "your_groq_api_key_here"

    if has_key:
        print("  Status: ✅ Ready")
        print(f"  API Key: {key[:10]}...")
    else:
        print("  Status: ❌ No API key")
        print("  Get free key: https://console.groq.com/keys")

    print("=" * 50 + "\n")
