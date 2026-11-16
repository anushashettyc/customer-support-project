"""
OmniSupport AI - Day 4 Test Script
==================================
Test the 5-agent orchestration system.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def test_individual_agents():
    """Test each agent individually."""
    print("\n" + "=" * 60)
    print("  TEST 1: Individual Agent Testing")
    print("=" * 60 + "\n")

    from src.agents.profiler import CustomerProfilerAgent
    from src.agents.complaint_analyzer import ComplaintAnalyzerAgent
    from src.agents.policy_researcher import PolicyResearcherAgent

    complaint = "My order ORD-003 arrived but the Smart Watch screen is flickering. I need this fixed ASAP!"

    # Test Profiler
    print("Testing Profiler Agent...")
    profiler = CustomerProfilerAgent()
    result = profiler.execute({"complaint": complaint})
    print(f"Result: {'✅ Success' if result.success else '❌ Failed'}")
    if result.success:
        print(f"  Order Found: {result.data.get('order_found')}")
        if result.data.get('order_found'):
            print(f"  Customer: {result.data.get('customer_name')}")
            print(f"  Tier: {result.data.get('customer_tier')}")

    # Test Complaint Analyzer
    print("\nTesting Complaint Analyzer Agent...")
    analyzer = ComplaintAnalyzerAgent()
    result = analyzer.execute({"complaint": complaint})
    print(f"Result: {'✅ Success' if result.success else '❌ Failed'}")
    if result.success:
        print(f"  Sentiment: {result.data.get('sentiment')}")
        print(f"  Urgency: {result.data.get('urgency')}")
        print(f"  Intent: {result.data.get('intent')}")

    # Test Policy Researcher
    print("\nTesting Policy Researcher Agent...")
    researcher = PolicyResearcherAgent()
    result = researcher.execute({
        "complaint": complaint,
        "previous_results": {}
    })
    print(f"Result: {'✅ Success' if result.success else '❌ Failed'}")
    if result.success:
        print(f"  Sources: {result.data.get('source_count')}")
        print(f"  Key Points: {len(result.data.get('key_points', []))}")

    print("\n✅ Individual agent tests complete\n")
    return True


def test_orchestrator_basic():
    """Test the orchestrator with a simple complaint."""
    print("\n" + "=" * 60)
    print("  TEST 2: Basic Orchestration")
    print("=" * 60 + "\n")

    from src.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()

    complaint = "My order ORD-001 hasn't arrived yet. It's been 3 days past the delivery date!"

    result = orchestrator.process_complaint(complaint, verbose=True)

    print("\n" + "=" * 60)
    print(f"Final Result: {'✅ Success' if result.success else '❌ Failed'}")
    print(f"Resolution: {result.resolution_type}")
    print(f"Duration: {result.metadata.get('duration_seconds', 0):.2f}s")
    print("=" * 60 + "\n")

    return result.success


def test_orchestrator_with_order_id():
    """Test with a known order ID."""
    print("\n" + "=" * 60)
    print("  TEST 3: Orchestration with Order Context")
    print("=" * 60 + "\n")

    from src.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()

    complaint = "I received my Smart Watch but the screen has a dead pixel. This is unacceptable for a $300 product!"
    order_id = "ORD-003"

    result = orchestrator.process_complaint(
        complaint=complaint,
        order_id=order_id,
        verbose=True
    )

    return result.success


def test_orchestrator_vip_customer():
    """Test with a VIP customer complaint."""
    print("\n" + "=" * 60)
    print("  TEST 4: VIP Customer Scenario")
    print("=" * 60 + "\n")

    from src.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()

    # ORD-005 is a Platinum customer
    complaint = "Order ORD-005 - The Designer Handbag I received has a small scratch. I expected perfect quality at this price point."

    result = orchestrator.process_complaint(
        complaint=complaint,
        verbose=True
    )

    return result.success


def test_orchestrator_refund_request():
    """Test a refund request scenario."""
    print("\n" + "=" * 60)
    print("  TEST 5: Refund Request")
    print("=" * 60 + "\n")

    from src.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()

    complaint = "I want to return my order ORD-010. The product doesn't match the description. I'd like a full refund."

    result = orchestrator.process_complaint(
        complaint=complaint,
        verbose=True
    )

    return result.success


def test_agent_info():
    """Test agent information retrieval."""
    print("\n" + "=" * 60)
    print("  TEST 6: Agent Information")
    print("=" * 60 + "\n")

    from src.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()

    agents = orchestrator.get_agent_info()

    print("Available Agents:")
    for agent in agents:
        print(f"  {agent['icon']} {agent['name']}")
        print(f"     {agent['description']}")

    print(f"\n✅ {len(agents)} agents available\n")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  OmniSupport AI - Day 4 Test Suite")
    print("  Multi-Agent Orchestration System")
    print("=" * 60)

    # Ensure data is loaded
    print("\n[Initializing system...]")
    from src.ingestion.pipeline import get_pipeline
    pipeline = get_pipeline()

    stats = pipeline.get_stats()
    if stats['vector_store'].get('document_count', 0) == 0:
        print("Loading sample data...")
        pipeline.load_sample_data()

    results = []

    # Test 1: Individual agents
    results.append(("Individual Agents", test_individual_agents()))

    # Test 2: Basic orchestration
    results.append(("Basic Orchestration", test_orchestrator_basic()))

    # Test 3: With order context
    results.append(("Order Context", test_orchestrator_with_order_id()))

    # Test 4: VIP customer
    results.append(("VIP Customer", test_orchestrator_vip_customer()))

    # Test 5: Refund request
    results.append(("Refund Request", test_orchestrator_refund_request()))

    # Test 6: Agent info
    results.append(("Agent Info", test_agent_info()))

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:25} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("  🎉 ALL TESTS PASSED!")
    else:
        print("  ⚠️  Some tests failed")

    print("=" * 60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
