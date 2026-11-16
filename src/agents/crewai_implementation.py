"""
OmniSupport AI - CrewAI Framework Implementation
================================================
Multi-agent customer support using CrewAI framework.

This demonstrates the same 5-agent workflow using an industry-standard
agentic AI framework instead of custom implementation.
"""

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import Field
from typing import Dict, Any, Type
import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.ingestion.pipeline import get_pipeline
from src.rag.rag_chain import RAGChain


# ============================================================
# TOOLS (for agents to use)
# ============================================================

class OrderLookupTool(BaseTool):
    """Tool for looking up customer orders."""

    name: str = "Order Lookup Tool"
    description: str = "Look up customer order details from the database. Provide an order_id (e.g., ORD-003) to get customer and order information."

    def _run(self, order_id: str) -> Dict[str, Any]:
        """Execute the tool."""
        pipeline = get_pipeline()
        order = pipeline.get_order(order_id)

        if order:
            return {
                "found": True,
                "order_id": order.get("order_id"),
                "customer_name": order.get("customer_name"),
                "customer_tier": order.get("loyalty_tier"),
                "product": order.get("product_name"),
                "price": order.get("price"),
                "status": order.get("status"),
                "order_date": order.get("order_date"),
                "delivery_date": order.get("delivery_date")
            }
        else:
            return {"found": False, "message": "Order not found"}


class PolicySearchTool(BaseTool):
    """Tool for searching company policies."""

    name: str = "Policy Search Tool"
    description: str = "Search company policies using semantic search (RAG). Provide a natural language question about policies (return policy, warranty, refunds, VIP benefits, etc.)"

    def _run(self, query: str) -> str:
        """Execute the tool."""
        rag = RAGChain()
        response = rag.query(query)
        return response.answer


# ============================================================
# CREWAI AGENTS
# ============================================================

class OmniSupportCrew:
    """CrewAI implementation of OmniSupport multi-agent system."""

    def __init__(self):
        """Initialize the crew with 5 specialized agents."""
        # Configure CrewAI LLM to use Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        # Use Gemini Flash (free and fast)
        self.llm = LLM(
            model="gemini/gemini-flash",
            api_key=api_key,
            temperature=0.3
        )

        # Initialize tools
        self.order_lookup_tool = OrderLookupTool()
        self.policy_search_tool = PolicySearchTool()

        # Agent 1: Customer Profiler
        self.profiler_agent = Agent(
            role="Customer 360 Profiler",
            goal="Extract customer and order information from complaints",
            backstory="""You are a data retrieval specialist. Your job is to identify
            order IDs and customer IDs in complaints and retrieve complete customer profiles
            including loyalty tier, purchase history, and account status.""",
            tools=[self.order_lookup_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        # Agent 2: Complaint Analyzer
        self.analyzer_agent = Agent(
            role="Complaint Analyzer",
            goal="Understand the sentiment, urgency, and intent of customer complaints",
            backstory="""You are an expert in sentiment analysis and customer psychology.
            You analyze complaints to determine emotional tone, urgency level, and what
            the customer actually wants (refund, replacement, information, etc.).""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        # Agent 3: Policy Researcher
        self.researcher_agent = Agent(
            role="Policy Researcher",
            goal="Find relevant company policies that apply to customer situations",
            backstory="""You are a policy expert with access to all company documentation.
            You search for and interpret return policies, warranty terms, refund rules,
            and VIP benefits that apply to each customer case.""",
            tools=[self.policy_search_tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        # Agent 4: Resolution Arbitrator
        self.arbitrator_agent = Agent(
            role="Resolution Arbitrator",
            goal="Make fair resolution decisions balancing customer satisfaction and company policy",
            backstory="""You are a senior customer service manager with authority to
            make resolution decisions. You weigh customer value, policy compliance,
            and fairness to determine appropriate resolutions (refund, replacement, etc.).""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        # Agent 5: Response Validator
        self.validator_agent = Agent(
            role="Response Validator",
            goal="Ensure response quality, professionalism, and safety",
            backstory="""You are a quality assurance specialist who reviews all customer
            communications. You check for tone, completeness, policy compliance, and
            ensure no promises the company can't keep.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def create_tasks(self, complaint: str) -> list:
        """
        Create tasks for each agent based on the complaint.

        Args:
            complaint: Customer complaint text

        Returns:
            List of Task objects for the crew
        """
        # Task 1: Profile the customer
        profile_task = Task(
            description=f"""Analyze this complaint and extract customer information:

            Complaint: "{complaint}"

            Your tasks:
            1. Identify any order ID or customer ID mentioned
            2. Use the Order Lookup Tool to get customer details
            3. Report customer tier, order status, and relevant context

            Provide a structured summary of customer information.""",
            agent=self.profiler_agent,
            expected_output="Structured customer profile with order details and loyalty tier"
        )

        # Task 2: Analyze the complaint
        analyze_task = Task(
            description=f"""Analyze this customer complaint in detail:

            Complaint: "{complaint}"

            Your tasks:
            1. Determine sentiment (positive/neutral/negative)
            2. Assess urgency level (low/medium/high/critical)
            3. Identify customer intent (refund/replacement/repair/information)
            4. List key issues mentioned

            Provide structured analysis of the complaint.""",
            agent=self.analyzer_agent,
            expected_output="Structured analysis with sentiment, urgency, intent, and key issues",
            context=[profile_task]  # Can see profile results
        )

        # Task 3: Research policies
        research_task = Task(
            description=f"""Research company policies relevant to this situation:

            Complaint: "{complaint}"

            Your tasks:
            1. Use the Policy Search Tool to find relevant policies
            2. Focus on return policy, warranty terms, refund rules
            3. Check for VIP/loyalty tier special benefits
            4. Summarize applicable policy sections

            Provide relevant policy information.""",
            agent=self.researcher_agent,
            expected_output="Relevant policy sections with return/warranty/refund terms",
            context=[profile_task, analyze_task]  # Can see both previous results
        )

        # Task 4: Make resolution decision
        arbitrate_task = Task(
            description=f"""Based on all gathered information, make a fair resolution decision:

            Original Complaint: "{complaint}"

            Your tasks:
            1. Review customer profile (tier, history)
            2. Review complaint analysis (urgency, intent)
            3. Review applicable policies
            4. Decide appropriate resolution type
            5. Draft a professional, empathetic response to the customer

            Provide resolution decision and customer response.""",
            agent=self.arbitrator_agent,
            expected_output="Resolution decision with detailed customer response",
            context=[profile_task, analyze_task, research_task]  # Uses all previous results
        )

        # Task 5: Validate response
        validate_task = Task(
            description="""Review the proposed response for quality and safety:

            Your tasks:
            1. Check tone (professional, empathetic)
            2. Check completeness (all questions answered, next steps clear)
            3. Check safety (no unrealistic promises, policy compliant)
            4. Suggest improvements if needed
            5. Approve or provide improved version

            Provide final approved response.""",
            agent=self.validator_agent,
            expected_output="Quality-checked final response ready to send to customer",
            context=[arbitrate_task]  # Reviews arbitrator's response
        )

        return [profile_task, analyze_task, research_task, arbitrate_task, validate_task]

    def process_complaint(self, complaint: str, verbose: bool = True) -> str:
        """
        Process a customer complaint through the full agent crew.

        Args:
            complaint: Customer complaint text
            verbose: Whether to print detailed agent logs

        Returns:
            Final validated response for the customer
        """
        if verbose:
            print("\n" + "="*60)
            print("  🚢 CrewAI Multi-Agent Processing")
            print("="*60 + "\n")

        # Create tasks
        tasks = self.create_tasks(complaint)

        # Create crew with sequential process
        crew = Crew(
            agents=[
                self.profiler_agent,
                self.analyzer_agent,
                self.researcher_agent,
                self.arbitrator_agent,
                self.validator_agent
            ],
            tasks=tasks,
            process=Process.sequential,  # Execute agents one by one
            verbose=verbose
        )

        # Execute crew
        result = crew.kickoff()

        if verbose:
            print("\n" + "="*60)
            print("  ✅ Processing Complete")
            print("="*60 + "\n")

        return result


    def get_agent_info(self) -> list:
        """
        Get information about all agents for display.

        Returns:
            List of agent info dictionaries
        """
        return [
            {
                "name": "Customer 360 Profiler",
                "icon": "👤",
                "description": "Extracts order and customer data"
            },
            {
                "name": "Complaint Analyzer",
                "icon": "🔍",
                "description": "Analyzes sentiment, urgency, and intent"
            },
            {
                "name": "Policy Researcher",
                "icon": "📚",
                "description": "Searches policies using RAG"
            },
            {
                "name": "Resolution Arbitrator",
                "icon": "⚖️",
                "description": "Makes resolution decisions"
            },
            {
                "name": "Response Validator",
                "icon": "✅",
                "description": "Validates response quality"
            }
        ]


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def process_with_crewai(complaint: str, verbose: bool = True) -> str:
    """
    Process a complaint using CrewAI framework.

    Args:
        complaint: Customer complaint text
        verbose: Whether to show detailed logs

    Returns:
        Final customer response
    """
    crew = OmniSupportCrew()
    return crew.process_complaint(complaint, verbose=verbose)


# ============================================================
# MAIN (for testing)
# ============================================================

if __name__ == "__main__":
    # Test complaint
    test_complaint = "My order ORD-003 Smart Watch screen is flickering. I need this fixed ASAP!"

    print("Testing CrewAI Implementation")
    print("="*60)

    result = process_with_crewai(test_complaint)

    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    print(result)
