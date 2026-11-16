"""
OmniSupport AI - NeMo Guardrails Integration
=============================================
Wraps the agent orchestrator with input/output guardrails.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from nemoguardrails import RailsConfig, LLMRails
    NEMO_AVAILABLE = True
except ImportError:
    NEMO_AVAILABLE = False
    RailsConfig = None
    LLMRails = None

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import AgentOrchestrator, OrchestratorResult, ConversationContext


class GuardrailsWrapper:
    """
    Wraps the AgentOrchestrator with NeMo Guardrails.

    Flow:
    1. User input → Input rails → Orchestrator
    2. Orchestrator output → Output rails → Customer
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize guardrails wrapper.

        Args:
            config_path: Path to guardrails config directory
                        (default: project_root/config/guardrails)
        """
        self.orchestrator = AgentOrchestrator()
        self.rails = None
        self.enabled = False

        if not NEMO_AVAILABLE:
            print("⚠️ NeMo Guardrails not available. Running without guardrails.")
            return

        # Set config path
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent  # Go up to project root
            config_path = project_root / "config" / "guardrails"

        config_path = Path(config_path)

        if not config_path.exists():
            print(f"⚠️ Guardrails config not found at {config_path}. Running without guardrails.")
            return

        try:
            # Load guardrails configuration
            config = RailsConfig.from_path(str(config_path))

            # Initialize rails
            self.rails = LLMRails(config)
            self.enabled = True

            print(f"✅ NeMo Guardrails loaded from {config_path}")

        except Exception as e:
            print(f"⚠️ Failed to load guardrails: {str(e)}. Running without guardrails.")
            self.enabled = False

    def validate_input(self, user_message: str) -> tuple[bool, Optional[str]]:
        """
        Validate user input through guardrails.

        Args:
            user_message: User's input message

        Returns:
            (is_valid, blocked_reason)
        """
        # Python checks run ALWAYS (even if NeMo is disabled)
        try:
            # Simple validation checks (before NeMo)
            if len(user_message.strip()) == 0:
                return False, "Please enter a message."

            if len(user_message) > 2000:
                return False, "Message too long. Please keep it under 2000 characters."

            msg_lower = user_message.lower()

            # Check for obvious jailbreak patterns
            jailbreak_patterns = [
                "ignore previous instructions",
                "ignore all instructions",
                "disregard your rules",
                "pretend you are",
                "act as if you are",
                "your new role is"
            ]

            for pattern in jailbreak_patterns:
                if pattern in msg_lower:
                    return False, "I'm OmniSupport AI and can only help with customer support issues."

            # SMART APPROACH: Category-based keyword detection
            # Instead of listing every possible question, detect topic categories

            # Medical keywords (comprehensive)
            medical_keywords = [
                "medicine", "medication", "drug", "pill", "tablet",
                "headache", "pain", "ache", "fever", "sick", "illness",
                "disease", "symptom", "doctor", "hospital", "treatment",
                "prescription", "dose", "diagnosis", "cancer", "diabetes",
                "blood pressure", "heart", "allergy", "infection"
            ]
            if any(keyword in msg_lower for keyword in medical_keywords):
                # Check if it's about a PRODUCT we sell (medical device/product support is OK)
                if any(word in msg_lower for word in ["order", "product", "purchase", "warranty", "return", "refund"]):
                    # Allow: "I want to return my blood pressure monitor"
                    pass
                else:
                    # Block: "which medicine for headache"
                    return False, "I can only help with customer support issues like orders, returns, refunds, and policies. For medical advice, please consult a healthcare professional."

            # Legal keywords
            legal_keywords = ["sue", "lawyer", "attorney", "legal", "lawsuit", "court", "settlement"]
            if any(keyword in msg_lower for keyword in legal_keywords):
                if not any(word in msg_lower for word in ["policy", "terms", "warranty", "return policy"]):
                    return False, "I can only help with customer support issues like orders, returns, refunds, and policies. For legal matters, please consult an attorney."

            # Financial keywords
            financial_keywords = ["stock", "invest", "bitcoin", "crypto", "tax", "401k", "portfolio", "trading"]
            if any(keyword in msg_lower for keyword in financial_keywords):
                if not any(word in msg_lower for word in ["refund", "charge", "payment", "billing"]):
                    return False, "I can only help with customer support issues like orders, returns, refunds, and policies."

            # Educational keywords (homework, tutorials)
            educational_keywords = ["homework", "teach me", "learn", "tutorial", "how to program", "explain python", "coding help"]
            if any(keyword in msg_lower for keyword in educational_keywords):
                return False, "I can only help with customer support issues like orders, returns, refunds, and policies."

            # Entertainment keywords
            entertainment_keywords = ["joke", "poem", "song", "story", "riddle", "game", "movie", "music"]
            if any(keyword in msg_lower for keyword in entertainment_keywords):
                return False, "I'm OmniSupport AI, specialized in helping with orders, returns, refunds, warranties, and company policies. How can I assist with your customer support issue?"

            # Personal advice keywords
            personal_keywords = ["should i break", "relationship", "girlfriend", "boyfriend", "marriage", "dating"]
            if any(keyword in msg_lower for keyword in personal_keywords):
                return False, "I can only help with customer support issues like orders, returns, refunds, and policies."

            # Competitor keywords
            competitor_keywords = ["amazon", "walmart", "best buy", "target", "ebay", "compare to", "better than"]
            if any(keyword in msg_lower for keyword in competitor_keywords):
                return False, "I can only help with customer support issues. I focus on helping you with your orders and concerns."

            # Weather/News keywords
            general_keywords = ["weather", "forecast", "news", "politics", "election", "president"]
            if any(keyword in msg_lower for keyword in general_keywords):
                return False, "I'm OmniSupport AI, specialized in helping with orders, returns, refunds, warranties, and company policies. How can I assist with your customer support issue?"

            return True, None

        except Exception as e:
            print(f"⚠️ Input validation error: {str(e)}")
            return True, None  # Fail open to avoid blocking legitimate requests

    def validate_output(
        self,
        response: str,
        context: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate LLM output through guardrails.

        Args:
            response: LLM's response
            context: Conversation context

        Returns:
            (is_valid, replacement_response)
        """
        # Python checks run ALWAYS (even if NeMo is disabled)
        try:
            # Business rule: Check refund amounts
            if "refund" in response.lower():
                # Extract potential amounts
                import re
                amounts = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', response)

                for amount_str in amounts:
                    amount = float(amount_str.replace(',', ''))
                    if amount > 1000:
                        return False, "I need manager approval for refunds over $1,000. Let me escalate this for you."

            # Check for PII patterns
            import re

            # SSN pattern
            if re.search(r'\b\d{3}-\d{2}-\d{4}\b', response):
                return False, "I apologize, I cannot share sensitive personal information."

            # Credit card pattern
            if re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', response):
                return False, "I apologize, I cannot share sensitive payment information."

            # Check response length (UX)
            if len(response) > 1500:
                return False, "Let me provide a more concise answer. " + response[:500] + "..."

            return True, None

        except Exception as e:
            print(f"⚠️ Output validation error: {str(e)}")
            return True, None  # Fail open

    def process_complaint(
        self,
        complaint: str,
        order_id: str = None,
        customer_id: str = None,
        context: ConversationContext = None,
        verbose: bool = False
    ) -> OrchestratorResult:
        """
        Process complaint with guardrails protection.

        Args:
            complaint: Customer complaint
            order_id: Optional order ID
            customer_id: Optional customer ID
            context: Conversation context for follow-ups
            verbose: Print execution details

        Returns:
            OrchestratorResult (potentially modified by guardrails)
        """
        # Input validation
        is_valid, block_reason = self.validate_input(complaint)

        if not is_valid:
            # Return blocked response
            return OrchestratorResult(
                success=True,
                final_response=block_reason,
                resolution_type="Input Blocked by Guardrails",
                metadata={
                    "blocked": True,
                    "reason": "input_validation_failed"
                }
            )

        # Process through orchestrator
        result = self.orchestrator.process_complaint(
            complaint=complaint,
            order_id=order_id,
            customer_id=customer_id,
            context=context,
            verbose=verbose
        )

        if not result.success:
            return result

        # Output validation
        validation_context = {
            "order_id": order_id,
            "resolution_type": result.resolution_type,
            "is_followup": result.is_followup
        }

        is_valid, replacement_response = self.validate_output(
            result.final_response,
            validation_context
        )

        if not is_valid and replacement_response:
            # Replace response with guardrail-approved version
            result.final_response = replacement_response
            result.metadata["guardrail_modified"] = True

        return result


def get_guarded_orchestrator(config_path: Optional[str] = None) -> GuardrailsWrapper:
    """
    Get a guardrails-wrapped orchestrator instance.

    Args:
        config_path: Optional path to guardrails config

    Returns:
        GuardrailsWrapper instance
    """
    return GuardrailsWrapper(config_path)
