"""
OmniSupport AI - Resolution Arbitrator Agent
=============================================
Agent #4: Makes fair resolution decisions based on all gathered data.
"""

from typing import Dict, Any
import json

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.agents.base_agent import BaseAgent, AgentResult
from src.llm.llm_factory import get_llm_client
from config.settings import RESOLUTION_TYPES


class ResolutionArbitratorAgent(BaseAgent):
    """
    Agent responsible for making fair resolution decisions.

    This agent:
    1. Receives inputs from all previous agents
    2. Weighs customer value, policy rules, and complaint severity
    3. Makes an autonomous resolution decision
    4. Generates a personalized response
    """

    def __init__(self):
        """Initialize the arbitrator agent."""
        super().__init__("arbitrator")
        self.llm_client = get_llm_client()

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute resolution arbitration.

        Args:
            context: Must contain all previous agent results

        Returns:
            AgentResult with resolution decision and response
        """
        try:
            complaint = context.get("complaint", "")
            previous_results = context.get("previous_results", {})

            # Extract data from previous agents - they are AgentResult objects
            profile_data = previous_results.get("profiler").data if "profiler" in previous_results else {}
            analysis_data = previous_results.get("complaint_analyzer").data if "complaint_analyzer" in previous_results else {}
            policy_data = previous_results.get("policy_researcher").data if "policy_researcher" in previous_results else {}

            if not complaint:
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    error="No complaint text provided"
                )

            self.log("Making resolution decision...")

            # Build arbitration prompt
            decision_response = self._generate_resolution(
                complaint=complaint,
                profile=profile_data,
                analysis=analysis_data,
                policies=policy_data
            )

            self.log(f"✅ Decision made")
            self.log(f"   Resolution: {decision_response.get('resolution_type')}")
            self.log(f"   Confidence: {decision_response.get('confidence')}")

            return AgentResult(
                agent_name=self.name,
                success=True,
                data=decision_response,
                metadata={
                    "model_used": self.llm_client.model_name
                }
            )

        except Exception as e:
            self.log(f"Error during arbitration: {str(e)}", "ERROR")
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(e)
            )

    def _generate_resolution(
        self,
        complaint: str,
        profile: Dict[str, Any],
        analysis: Dict[str, Any],
        policies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate resolution decision and response.

        Args:
            complaint: Original complaint
            profile: Customer profile data
            analysis: Complaint analysis
            policies: Policy research results

        Returns:
            Dictionary with resolution decision and response
        """
        # Build context summary
        context_summary = self._build_context_summary(profile, analysis, policies)

        system_prompt = f"""You are an expert customer service arbitrator for OmniSupport AI. Your job is to make fair, policy-compliant resolution decisions.

AVAILABLE RESOLUTION TYPES:
{', '.join(RESOLUTION_TYPES)}

DECISION CRITERIA:
1. Policy Compliance: Follow company policies strictly
2. Customer Value: Consider loyalty tier and customer history
3. Fairness: Balance company interests with customer satisfaction
4. Urgency: Respond appropriately to complaint severity

RESPONSE FORMAT (JSON only):
{{
  "resolution_type": "one of the available types",
  "resolution_details": {{
    "refund_amount": 0.00,
    "store_credit_amount": 0.00,
    "actions_required": ["action1", "action2"],
    "timeline": "immediate|3-5 days|7-14 days"
  }},
  "confidence": "low|medium|high",
  "reasoning": "Brief explanation of decision",
  "customer_response": "Professional, empathetic response to customer (2-3 paragraphs)"
}}

TONE GUIDELINES:
- Start with customer's name if available
- Show empathy and understanding
- Clearly explain the resolution
- Provide next steps
- Thank them for their business"""

        user_prompt = f"""CUSTOMER COMPLAINT:
"{complaint}"

CONTEXT:
{context_summary}

POLICY INFORMATION:
{policies.get('relevant_policies', 'No specific policies found')}

Make a fair resolution decision and draft a customer response."""

        # Get LLM decision
        response = self.llm_client.generate_with_system(
            user_prompt,
            system_prompt
        )

        # Parse JSON response
        decision_text = response.content.strip()

        # Extract JSON if wrapped
        if "```json" in decision_text:
            decision_text = decision_text.split("```json")[1].split("```")[0].strip()
        elif "```" in decision_text:
            decision_text = decision_text.split("```")[1].split("```")[0].strip()

        decision = json.loads(decision_text)

        return decision

    def _build_context_summary(
        self,
        profile: Dict[str, Any],
        analysis: Dict[str, Any],
        policies: Dict[str, Any]
    ) -> str:
        """Build a concise context summary for the LLM."""
        summary_parts = []

        # Customer info
        if profile.get("order_found"):
            order = profile.get("order_details", {})
            summary_parts.append(f"Customer: {order.get('customer_name')} ({profile.get('customer_tier')} tier)")
            summary_parts.append(f"Order: {order.get('order_id')} - {order.get('product_name')} (${order.get('price')})")
            summary_parts.append(f"Status: {order.get('status')}")
            summary_parts.append(f"Order Date: {order.get('order_date')}")
        else:
            summary_parts.append("Customer: Unknown (no order found)")

        # Analysis info
        summary_parts.append(f"Sentiment: {analysis.get('sentiment', 'unknown')}")
        summary_parts.append(f"Urgency: {analysis.get('urgency', 'medium')}")
        summary_parts.append(f"Intent: {analysis.get('intent', 'complaint')}")
        summary_parts.append(f"Emotional Tone: {analysis.get('emotional_tone', 'unknown')}")

        # Key issues
        if analysis.get("key_issues"):
            summary_parts.append(f"Key Issues: {', '.join(analysis['key_issues'])}")

        return "\n".join(summary_parts)
