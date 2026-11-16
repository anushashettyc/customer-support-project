"""
OmniSupport AI - Policy Researcher Agent
=========================================
Agent #3: Performs RAG search on policy documents.
"""

from typing import Dict, Any, List

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.agents.base_agent import BaseAgent, AgentResult
from src.rag.rag_chain import RAGChain


class PolicyResearcherAgent(BaseAgent):
    """
    Agent responsible for researching relevant policies.

    This agent:
    1. Searches the vector store for relevant policy documents
    2. Extracts applicable terms and conditions
    3. Identifies special cases (VIP benefits, time-based rules, etc.)
    4. Returns structured policy information
    """

    def __init__(self):
        """Initialize the policy researcher agent."""
        super().__init__("policy")
        self.rag_chain = RAGChain()

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute policy research.

        Args:
            context: Must contain 'complaint' text, optionally 'profile_data'

        Returns:
            AgentResult with policy research data
        """
        try:
            complaint = context.get("complaint", "")

            # Get previous results - they are AgentResult objects
            previous_results = context.get("previous_results", {})

            analysis = {}
            if "complaint_analyzer" in previous_results:
                analysis = previous_results["complaint_analyzer"].data

            profile = {}
            if "profiler" in previous_results:
                profile = previous_results["profiler"].data

            if not complaint:
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    error="No complaint text provided"
                )

            self.log("Researching policies...")

            # Build search query based on intent and complaint
            intent = analysis.get("intent", "complaint")
            search_query = self._build_search_query(complaint, intent, profile)

            self.log(f"Search query: {search_query}")

            # Perform RAG search
            order_info = profile.get("order_details") if profile.get("order_found") else None

            if order_info:
                rag_response = self.rag_chain.query_with_order_context(
                    question=search_query,
                    order_info=order_info
                )
            else:
                rag_response = self.rag_chain.query(search_query)

            # Extract policy information
            policy_data = {
                "relevant_policies": rag_response.answer,
                "sources": rag_response.sources,
                "source_count": len(rag_response.sources),
                "search_query": search_query
            }

            # Extract key policy points
            policy_data["key_points"] = self._extract_key_points(rag_response.answer)

            self.log(f"✅ Research complete")
            self.log(f"   Sources found: {len(rag_response.sources)}")
            self.log(f"   Key points: {len(policy_data['key_points'])}")

            return AgentResult(
                agent_name=self.name,
                success=True,
                data=policy_data,
                metadata={
                    "rag_metadata": rag_response.metadata
                }
            )

        except Exception as e:
            self.log(f"Error during research: {str(e)}", "ERROR")
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(e)
            )

    def _build_search_query(
        self,
        complaint: str,
        intent: str,
        profile: Dict[str, Any]
    ) -> str:
        """
        Build an optimized search query based on context.

        Args:
            complaint: Original complaint text
            intent: Detected intent (refund, replacement, etc.)
            profile: Customer profile data

        Returns:
            Optimized search query
        """
        # Map intents to policy keywords
        intent_keywords = {
            "refund": "refund policy eligibility conditions",
            "replacement": "replacement warranty exchange policy",
            "repair": "repair warranty service policy",
            "return": "return policy conditions timeframe",
            "information": complaint,
            "complaint": "resolution policy customer support"
        }

        base_query = intent_keywords.get(intent, complaint)

        # Add tier-specific information if available
        tier = profile.get("customer_tier")
        if tier and tier in ["Gold", "Platinum"]:
            base_query += f" {tier} VIP benefits"

        return base_query

    def _extract_key_points(self, policy_text: str) -> List[str]:
        """
        Extract key bullet points from policy text.

        Args:
            policy_text: The policy text from RAG

        Returns:
            List of key points
        """
        key_points = []

        # Split by common bullet point markers
        lines = policy_text.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith(("*", "-", "•", "·")):
                # Remove bullet marker
                point = line.lstrip("*-•· ").strip()
                if point and len(point) > 10:  # Ignore very short lines
                    key_points.append(point)

        # If no bullets found, try to extract sentences
        if not key_points and len(policy_text) > 0:
            sentences = policy_text.split(".")
            key_points = [s.strip() + "." for s in sentences[:3] if len(s.strip()) > 20]

        return key_points[:5]  # Return top 5 points
