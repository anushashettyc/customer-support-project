"""
OmniSupport AI - Agent Orchestrator
====================================
Orchestrates the execution of all 5 agents in sequence.
Supports follow-up conversations with context memory.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.agents.profiler import CustomerProfilerAgent
from src.agents.complaint_analyzer import ComplaintAnalyzerAgent
from src.agents.policy_researcher import PolicyResearcherAgent
from src.agents.arbitrator import ResolutionArbitratorAgent
from src.agents.validator import ResponseValidatorAgent
from src.agents.base_agent import AgentResult
from src.llm.llm_factory import get_llm_client


@dataclass
class ConversationContext:
    """Stores context for follow-up conversations."""
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_tier: Optional[str] = None
    product_name: Optional[str] = None
    issue_summary: Optional[str] = None
    last_resolution: Optional[str] = None
    chat_history: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_tier": self.customer_tier,
            "product_name": self.product_name,
            "issue_summary": self.issue_summary,
            "last_resolution": self.last_resolution,
            "chat_history": self.chat_history
        }


@dataclass
class OrchestratorResult:
    """
    Final result from the agent orchestration.
    """
    success: bool
    final_response: str = ""
    resolution_type: str = ""
    error: str = ""
    is_followup: bool = False
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_logs: List[Dict[str, Any]] = field(default_factory=list)
    context: Optional[ConversationContext] = None


class AgentOrchestrator:
    """
    Orchestrates the 5-agent pipeline for customer support.
    Supports follow-up conversations with context memory.
    """

    def __init__(self):
        """Initialize the orchestrator with all agents."""
        self.agents = {
            "profiler": CustomerProfilerAgent(),
            "complaint_analyzer": ComplaintAnalyzerAgent(),
            "policy_researcher": PolicyResearcherAgent(),
            "arbitrator": ResolutionArbitratorAgent(),
            "validator": ResponseValidatorAgent()
        }

        self.execution_order = [
            "profiler",
            "complaint_analyzer",
            "policy_researcher",
            "arbitrator",
            "validator"
        ]

        self.llm_client = None

    def _get_llm(self):
        """Lazy load LLM client."""
        if self.llm_client is None:
            self.llm_client = get_llm_client()
        return self.llm_client

    def is_followup_question(self, message: str, context: ConversationContext) -> bool:
        """
        Detect if a message is a follow-up question or a new complaint.

        Uses simple heuristics first, then LLM if uncertain.
        """
        # No history = definitely not a follow-up
        if not context.chat_history:
            return False

        message_lower = message.lower()

        # Strong indicators of follow-up
        followup_indicators = [
            "instead", "rather", "what about", "how about",
            "can i", "can you", "could i", "could you",
            "what if", "is it possible", "alternatively",
            "also", "another", "more", "else",
            "when", "where", "how long", "how much",
            "tracking", "status", "update",
            "yes", "no", "ok", "okay", "sure", "thanks",
            "that", "this", "it", "the", "my"
        ]

        # Strong indicators of new complaint
        new_complaint_indicators = [
            "new order", "different order", "another order",
            "i have a problem", "i have an issue",
            "i want to complain", "i need help with"
        ]

        # Check for new complaint first
        for indicator in new_complaint_indicators:
            if indicator in message_lower:
                return False

        # Check for follow-up indicators
        for indicator in followup_indicators:
            if indicator in message_lower:
                return True

        # Short messages are likely follow-ups
        if len(message.split()) < 10:
            return True

        # If message contains order ID different from context, it's new
        import re
        order_match = re.search(r'ORD[-_]?\d{3,}', message.upper())
        if order_match and context.order_id:
            if order_match.group() != context.order_id:
                return False

        # Default: if we have context and message is ambiguous, treat as follow-up
        return True

    def process_followup(
        self,
        message: str,
        context: ConversationContext,
        verbose: bool = True
    ) -> OrchestratorResult:
        """
        Process a follow-up message using existing context.
        Uses only the Arbitrator agent for efficiency.
        """
        start_time = datetime.now()

        if verbose:
            print("\n" + "=" * 60)
            print("  💬 OmniSupport AI - Follow-up Processing")
            print("=" * 60 + "\n")

        # Build conversation history for LLM
        history_text = "\n".join([
            f"{'Customer' if msg['role'] == 'user' else 'Support'}: {msg['content']}"
            for msg in context.chat_history[-6:]  # Last 6 messages
        ])

        system_prompt = f"""You are OmniSupport AI, handling a follow-up in an ongoing customer support conversation.

CONVERSATION CONTEXT:
- Order ID: {context.order_id or 'Not provided'}
- Customer: {context.customer_name or 'Unknown'} ({context.customer_tier or 'Standard'} tier)
- Product: {context.product_name or 'Unknown'}
- Original Issue: {context.issue_summary or 'General inquiry'}
- Last Resolution Offered: {context.last_resolution or 'None yet'}

CONVERSATION HISTORY:
{history_text}

INSTRUCTIONS:
1. This is a FOLLOW-UP message, not a new complaint
2. Use the existing context - don't ask for information you already have
3. Be helpful, concise, and action-oriented
4. If they're asking for a different resolution, evaluate if it's possible
5. If they're asking for status/details, provide specific information
6. Keep responses professional but friendly

Respond directly to the customer's follow-up question."""

        user_prompt = f"Customer's follow-up: {message}"

        try:
            llm = self._get_llm()
            response = llm.generate_with_system(user_prompt, system_prompt)
            final_response = response.content.strip()

            # Update context with this exchange
            context.chat_history.append({"role": "user", "content": message})
            context.chat_history.append({"role": "assistant", "content": final_response})

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if verbose:
                print(f"✅ Follow-up processed in {duration:.2f}s\n")
                print(f"Response:\n{final_response}\n")

            return OrchestratorResult(
                success=True,
                final_response=final_response,
                resolution_type="Follow-up Response",
                is_followup=True,
                context=context,
                metadata={
                    "duration_seconds": duration,
                    "type": "followup",
                    "timestamp": end_time.isoformat()
                }
            )

        except Exception as e:
            return OrchestratorResult(
                success=False,
                error=str(e),
                is_followup=True,
                context=context
            )

    def process_complaint(
        self,
        complaint: str,
        order_id: str = None,
        customer_id: str = None,
        context: ConversationContext = None,
        verbose: bool = True
    ) -> OrchestratorResult:
        """
        Process a customer complaint through the full agent pipeline.
        Supports follow-up detection with conversation context.
        """
        # Check if this is a follow-up
        if context and self.is_followup_question(complaint, context):
            return self.process_followup(complaint, context, verbose)

        start_time = datetime.now()

        if verbose:
            print("\n" + "=" * 60)
            print("  🎯 OmniSupport AI - Multi-Agent Processing")
            print("=" * 60 + "\n")

        # Initialize context dict for agents
        agent_context = {
            "complaint": complaint,
            "order_id": order_id,
            "customer_id": customer_id,
            "previous_results": {}
        }

        agent_results = {}
        execution_log = []

        # Execute agents in sequence
        for agent_key in self.execution_order:
            agent = self.agents[agent_key]

            log_entry = {
                "agent": agent.name,
                "icon": agent.icon,
                "start_time": datetime.now().isoformat()
            }

            if verbose:
                print(f"{agent.icon} {agent.name}")
                print("-" * 60)

            # Execute agent
            result = agent.execute(agent_context)

            log_entry["end_time"] = datetime.now().isoformat()
            log_entry["success"] = result.success

            if result.success:
                agent_results[agent_key] = result
                agent_context["previous_results"][agent_key] = result

                if verbose:
                    print(f"✅ Success\n")

                log_entry["status"] = "success"
            else:
                if verbose:
                    print(f"❌ Failed: {result.error}\n")

                log_entry["status"] = "failed"
                log_entry["error"] = result.error

                # Stop pipeline on critical failure
                if agent_key in ["profiler", "arbitrator"]:
                    execution_log.append(log_entry)
                    return OrchestratorResult(
                        success=False,
                        error=result.error or "Agent execution failed",
                        agent_results=agent_results,
                        execution_log=execution_log,
                        agent_logs=self._build_agent_logs(execution_log, agent_results),
                        metadata={"failed_at": agent_key, "error": result.error}
                    )

            execution_log.append(log_entry)

        # Extract final results
        validator_result = agent_results.get("validator")
        arbitrator_result = agent_results.get("arbitrator")
        profiler_result = agent_results.get("profiler")

        if validator_result and validator_result.success:
            final_response = validator_result.data.get("final_response", "")
            resolution_type = validator_result.data.get("resolution_type", "")
        elif arbitrator_result and arbitrator_result.success:
            final_response = arbitrator_result.data.get("customer_response", "")
            resolution_type = arbitrator_result.data.get("resolution_type", "")
        else:
            final_response = "Unable to generate response"
            resolution_type = "Escalate to Human Agent"

        # Build conversation context for follow-ups
        new_context = ConversationContext(
            order_id=order_id or (profiler_result.data.get("order_id") if profiler_result else None),
            customer_id=customer_id,
            customer_name=profiler_result.data.get("customer_name") if profiler_result else None,
            customer_tier=profiler_result.data.get("customer_tier") if profiler_result else None,
            product_name=profiler_result.data.get("product_name") if profiler_result else None,
            issue_summary=complaint[:200],
            last_resolution=resolution_type,
            chat_history=[
                {"role": "user", "content": complaint},
                {"role": "assistant", "content": final_response}
            ]
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if verbose:
            print("=" * 60)
            print(f"  ✅ Processing Complete ({duration:.2f}s)")
            print("=" * 60 + "\n")
            print(f"Resolution: {resolution_type}")
            print(f"\nFinal Response:\n{final_response}\n")

        return OrchestratorResult(
            success=True,
            final_response=final_response,
            resolution_type=resolution_type,
            is_followup=False,
            agent_results=agent_results,
            execution_log=execution_log,
            agent_logs=self._build_agent_logs(execution_log, agent_results),
            context=new_context,
            metadata={
                "duration_seconds": duration,
                "agents_executed": len(execution_log),
                "timestamp": end_time.isoformat()
            }
        )

    def _build_agent_logs(self, execution_log: List[Dict], agent_results: Dict) -> List[Dict[str, Any]]:
        """Build simplified agent logs for UI display."""
        logs = []
        for log in execution_log:
            result = None
            for key, res in agent_results.items():
                if res.agent_name == log.get("agent"):
                    result = res
                    break

            try:
                start = datetime.fromisoformat(log.get("start_time", ""))
                end = datetime.fromisoformat(log.get("end_time", ""))
                duration = (end - start).total_seconds()
            except:
                duration = 0

            logs.append({
                "agent_name": log.get("agent", "Unknown"),
                "icon": log.get("icon", "🤖"),
                "status": log.get("status", "unknown"),
                "duration": duration,
                "error": log.get("error"),
                "input": None,
                "output": result.data if result else None
            })
        return logs

    def get_agent_info(self) -> List[Dict[str, str]]:
        """Get information about all agents."""
        return [
            agent.get_info()
            for agent in self.agents.values()
        ]
