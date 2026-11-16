"""
OmniSupport AI - Response Validator Agent
==========================================
Agent #5: Validates response quality and safety.
"""

from typing import Dict, Any, List
import json

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.agents.base_agent import BaseAgent, AgentResult
from src.llm.llm_factory import get_llm_client


class ResponseValidatorAgent(BaseAgent):
    """
    Agent responsible for validating the final response.

    This agent:
    1. Checks response quality (tone, clarity, completeness)
    2. Validates policy compliance
    3. Checks for safety issues (promises we can't keep, legal risks)
    4. Suggests improvements if needed
    """

    def __init__(self):
        """Initialize the validator agent."""
        super().__init__("validator")
        self.llm_client = get_llm_client()

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute response validation.

        Args:
            context: Must contain arbitrator's decision

        Returns:
            AgentResult with validation results
        """
        try:
            previous_results = context.get("previous_results", {})

            # Get arbitrator result - it's an AgentResult object
            if "arbitrator" not in previous_results:
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    error="No arbitrator decision to validate"
                )

            arbitrator_data = previous_results["arbitrator"].data

            customer_response = arbitrator_data.get("customer_response", "")
            resolution_type = arbitrator_data.get("resolution_type", "")

            if not customer_response:
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    error="No customer response to validate"
                )

            self.log("Validating response...")

            # Perform validation
            validation_result = self._validate_response(
                response=customer_response,
                resolution_type=resolution_type,
                context=context
            )

            validation_result["original_response"] = customer_response
            validation_result["resolution_type"] = resolution_type

            # Determine if response needs revision
            issues = validation_result.get("issues", [])
            validation_result["approved"] = len(issues) == 0

            if validation_result["approved"]:
                self.log(f"✅ Response approved")
                validation_result["final_response"] = customer_response
            else:
                self.log(f"⚠️ Issues found: {len(issues)}", "WARNING")
                for issue in issues:
                    self.log(f"   - {issue}", "WARNING")

                # Use improved response if available
                if validation_result.get("improved_response"):
                    validation_result["final_response"] = validation_result["improved_response"]
                else:
                    validation_result["final_response"] = customer_response

            return AgentResult(
                agent_name=self.name,
                success=True,
                data=validation_result,
                metadata={
                    "validation_score": validation_result.get("score", 0)
                }
            )

        except Exception as e:
            self.log(f"Error during validation: {str(e)}", "ERROR")
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(e)
            )

    def _validate_response(
        self,
        response: str,
        resolution_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate the customer response.

        Args:
            response: The customer response to validate
            resolution_type: Type of resolution offered
            context: Full context for validation

        Returns:
            Validation results
        """
        system_prompt = """You are a quality assurance expert for customer service responses. Validate responses for:

1. TONE: Professional, empathetic, clear
2. COMPLETENESS: All information provided, next steps clear
3. SAFETY: No unrealistic promises, no legal issues
4. POLICY COMPLIANCE: Follows company policies
5. CLARITY: Easy to understand, well-structured

RESPONSE FORMAT (JSON only):
{
  "score": 0-100,
  "approved": true|false,
  "issues": ["issue1", "issue2"],
  "strengths": ["strength1", "strength2"],
  "improved_response": "Only if issues found, provide improved version"
}"""

        user_prompt = f"""VALIDATE THIS CUSTOMER RESPONSE:

Resolution Type: {resolution_type}

Response:
"{response}"

Provide validation results as JSON."""

        # Get LLM validation
        llm_response = self.llm_client.generate_with_system(
            user_prompt,
            system_prompt
        )

        # Parse JSON response
        validation_text = llm_response.content.strip()

        # Extract JSON if wrapped
        if "```json" in validation_text:
            validation_text = validation_text.split("```json")[1].split("```")[0].strip()
        elif "```" in validation_text:
            validation_text = validation_text.split("```")[1].split("```")[0].strip()

        validation = json.loads(validation_text)

        return validation
