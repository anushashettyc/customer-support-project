"""
OmniSupport AI - Groq Client
============================
LLM client implementation for Groq API (fast inference).
"""

import os
from typing import Optional, Dict, List

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.llm.base_client import BaseLLMClient, LLMResponse
from config.settings import AGENT_TEMPERATURE


class GroqClient(BaseLLMClient):
    """
    Groq LLM client.

    Uses the Groq API for fast LLM inference.
    Free tier available with generous limits.

    Supported models:
    - openai/gpt-oss-120b (best quality)
    - qwen/qwen3.8-27b (good alternative)
    - allam-2-7b (fastest, smaller)
    """

    # Default model (best available on Groq)
    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(
        self,
        model_name: str = None,
        temperature: float = None,
        api_key: str = None
    ):
        """
        Initialize Groq client.

        Args:
            model_name: Groq model (default: llama-3.1-8b-instant)
            temperature: Creativity level (default: 0.3)
            api_key: API key (default: from environment)
        """
        model_name = model_name or self.DEFAULT_MODEL
        temperature = temperature if temperature is not None else AGENT_TEMPERATURE

        super().__init__(model_name, temperature)

        self.provider_name = "groq"
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self._client = None

        if self.is_available():
            self._initialize()

    def _initialize(self):
        """Initialize the Groq client."""
        if not GROQ_AVAILABLE:
            raise ImportError(
                "groq package not installed. "
                "Install with: pip install groq"
            )

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not set. "
                "Get your API key from: https://console.groq.com/keys"
            )

        self._client = Groq(api_key=self.api_key)
        print(f"✅ Groq client initialized: {self.model_name}")

    def generate(self, prompt: str) -> LLMResponse:
        """
        Generate a response from a prompt.

        Args:
            prompt: The input prompt

        Returns:
            LLMResponse with generated content
        """
        return self.generate_with_system(prompt, "You are a helpful assistant.")

    def generate_with_system(
        self,
        prompt: str,
        system_prompt: str
    ) -> LLMResponse:
        """
        Generate with a system prompt.

        Args:
            prompt: The user prompt
            system_prompt: System instructions

        Returns:
            LLMResponse with generated content
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        return self._chat_completion(messages)

    def generate_with_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate using chat history.

        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            system_prompt: Optional system instructions

        Returns:
            LLMResponse with generated content
        """
        all_messages = []

        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})

        all_messages.extend(messages)

        return self._chat_completion(all_messages)

    def _chat_completion(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """
        Make a chat completion request.

        Args:
            messages: List of message dicts

        Returns:
            LLMResponse
        """
        if not self._client:
            self._initialize()

        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2048
            )

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                provider=self.provider_name,
                usage=usage,
                raw_response=response
            )

        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if Groq is available.

        Returns:
            True if package installed and API key set
        """
        return GROQ_AVAILABLE and bool(self.api_key)

    def get_info(self) -> Dict[str, str]:
        """Get provider information."""
        info = super().get_info()
        info["api_key_set"] = bool(self.api_key)
        info["package_installed"] = GROQ_AVAILABLE
        return info
