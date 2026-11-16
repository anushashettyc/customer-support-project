"""
OmniSupport AI - Complaint Analyzer Agent
==========================================
Agent #2: Analyzes complaint sentiment, intent, and urgency.
"""

from typing import Dict, Any
import json

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.agents.base_agent import BaseAgent, AgentResult
from src.llm.llm_factory import get_llm_client


class ComplaintAnalyzerAgent(BaseAgent):
    """
    Agent responsible for analyzing customer complaints.

    This agent uses LLM to extract:
    1. Sentiment (positive, neutral, negative)
    2. Intent (refund, replacement, information, etc.)
    3. Urgency level (low, medium, high, critical)
    4. Key issues mentioned
    5. Emotional tone
    """

    def __init__(self):
        """Initialize the complaint analyzer agent."""
        super().__init__("complaint")
        self.llm_client = get_llm_client()

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute complaint analysis.

        Args:
            context: Must contain 'complaint' text

        Returns:
            AgentResult with analysis data
        """
        try:
            complaint = context.get("complaint", "")

            if not complaint:
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    error="No complaint text provided"
                )

            self.log("Analyzing complaint...")

            # Build analysis prompt
            system_prompt = """You are an expert customer service analyst. Analyze customer complaints and extract structured information.

Your response MUST be valid JSON with this exact structure:
{
  "sentiment": "positive|neutral|negative",
  "urgency": "low|medium|high|critical",
  "intent": "refund|replacement|repair|information|complaint|other",
  "emotional_tone": "calm|frustrated|angry|disappointed|confused",
  "key_issues": ["issue1", "issue2"],
  "requires_immediate_attention": true|false,
  "summary": "One sentence summary"
}"""

            user_prompt = f"""Analyze this customer complaint:

"{complaint}"

Provide your analysis as JSON only, no additional text."""

            # Get LLM analysis
            response = self.llm_client.generate_with_system(
                user_prompt,
                system_prompt
            )

            # Parse JSON response
            analysis_text = response.content.strip()

            # Extract JSON if wrapped in markdown
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

            analysis = json.loads(analysis_text)

            self.log(f"✅ Analysis complete")
            self.log(f"   Sentiment: {analysis.get('sentiment')}")
            self.log(f"   Urgency: {analysis.get('urgency')}")
            self.log(f"   Intent: {analysis.get('intent')}")

            return AgentResult(
                agent_name=self.name,
                success=True,
                data=analysis,
                metadata={
                    "model_used": response.model,
                    "tokens": response.usage
                }
            )

        except json.JSONDecodeError as e:
            self.log(f"Failed to parse LLM JSON response: {str(e)}", "ERROR")
            # Return fallback analysis
            return AgentResult(
                agent_name=self.name,
                success=True,
                data={
                    "sentiment": "neutral",
                    "urgency": "medium",
                    "intent": "complaint",
                    "emotional_tone": "unknown",
                    "key_issues": ["Unable to analyze"],
                    "requires_immediate_attention": False,
                    "summary": complaint[:100]
                },
                metadata={"fallback": True, "parse_error": str(e)}
            )

        except Exception as e:
            self.log(f"Error during analysis: {str(e)}", "ERROR")
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
