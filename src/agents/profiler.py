"""
OmniSupport AI - Customer 360 Profiler Agent
=============================================
Agent #1: Fetches customer order history and profile data.
"""

from typing import Dict, Any

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.agents.base_agent import BaseAgent, AgentResult
from src.ingestion.pipeline import get_pipeline
from src.utils.helpers import extract_order_id, extract_customer_id, get_loyalty_tier_info


class CustomerProfilerAgent(BaseAgent):
    """
    Agent responsible for fetching customer profile and order history.

    This agent:
    1. Extracts order_id or customer_id from the complaint
    2. Fetches order details from the database
    3. Retrieves customer loyalty tier information
    4. Calculates relevant metrics (days since order, etc.)
    """

    def __init__(self):
        """Initialize the profiler agent."""
        super().__init__("profiler")
        self.pipeline = get_pipeline()

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute customer profiling.

        Args:
            context: Must contain 'complaint' text

        Returns:
            AgentResult with customer profile data
        """
        try:
            complaint = context.get("complaint", "")

            if not complaint:
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    error="No complaint text provided"
                )

            self.log("Profiling customer...")

            # Extract identifiers
            order_id = context.get("order_id") or extract_order_id(complaint)
            customer_id = context.get("customer_id") or extract_customer_id(complaint)

            profile_data = {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_found": False,
                "customer_tier": None,
                "order_details": None
            }

            # Fetch order if ID found
            if order_id:
                self.log(f"Looking up order: {order_id}")
                order = self.pipeline.get_order(order_id)

                if order:
                    profile_data["order_found"] = True
                    profile_data["order_details"] = order
                    profile_data["customer_tier"] = order.get("loyalty_tier")
                    profile_data["customer_name"] = order.get("customer_name")
                    profile_data["customer_email"] = order.get("email")
                    profile_data["product_name"] = order.get("product_name")
                    profile_data["order_status"] = order.get("status")
                    profile_data["order_price"] = order.get("price")
                    profile_data["order_date"] = order.get("order_date")
                    profile_data["delivery_date"] = order.get("delivery_date")

                    # Get tier benefits
                    tier_info = get_loyalty_tier_info(order.get("loyalty_tier", "Bronze"))
                    profile_data["tier_benefits"] = tier_info

                    self.log(f"✅ Order found: {order_id}")
                    self.log(f"   Customer: {order.get('customer_name')} ({order.get('loyalty_tier')})")
                else:
                    self.log(f"⚠️ Order not found: {order_id}", "WARNING")
            else:
                self.log("No order ID found in complaint", "INFO")

            return AgentResult(
                agent_name=self.name,
                success=True,
                data=profile_data,
                metadata={
                    "identifiers_extracted": {
                        "order_id": order_id,
                        "customer_id": customer_id
                    }
                }
            )

        except Exception as e:
            self.log(f"Error during profiling: {str(e)}", "ERROR")
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
