"""
OmniSupport AI - Day 3 Test Script
==================================
Test the RAG pipeline and LLM integration.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def test_llm_factory():
    """Test LLM factory and provider detection."""
    print("\n" + "=" * 60)
    print("  TEST 1: LLM Factory & Provider Detection")
    print("=" * 60 + "\n")

    from src.llm.llm_factory import (
        get_available_providers,
        auto_detect_provider,
        print_provider_status
    )

    # Show provider status
    print_provider_status()

    # Check available providers
    providers = get_available_providers()
    print(f"Registered providers: {[p['name'] for p in providers]}")

    # Auto-detect
    detected = auto_detect_provider()
    if detected:
        print(f"✅ Auto-detected provider: {detected}")
        return True
    else:
        print("❌ No provider available. Set an API key in .env file.")
        return False


def test_llm_client():
    """Test LLM client initialization and generation."""
    print("\n" + "=" * 60)
    print("  TEST 2: LLM Client")
    print("=" * 60 + "\n")

    try:
        from src.llm.llm_factory import get_llm_client

        # Get auto-detected client
        client = get_llm_client()
        print(f"✅ Client created: {client.provider_name} ({client.model_name})")

        # Test simple generation
        print("\nTesting generation...")
        response = client.generate("Say 'Hello, I am working!' in exactly those words.")
        print(f"✅ Response received: {response.content[:100]}...")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")

        if response.usage:
            print(f"   Tokens: {response.usage}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_rag_chain():
    """Test the RAG pipeline."""
    print("\n" + "=" * 60)
    print("  TEST 3: RAG Chain")
    print("=" * 60 + "\n")

    try:
        from src.rag.rag_chain import RAGChain

        # Ensure vector store has data
        from src.ingestion.pipeline import get_pipeline
        pipeline = get_pipeline()

        stats = pipeline.get_stats()
        doc_count = stats['vector_store'].get('document_count', 0)
        print(f"Vector store has {doc_count} documents")

        if doc_count == 0:
            print("Loading sample data...")
            pipeline.load_sample_data()

        # Create RAG chain
        print("\nInitializing RAG chain...")
        rag = RAGChain()

        # Test query 1: Return policy
        print("\n" + "-" * 40)
        print("Query 1: Return Policy")
        print("-" * 40)
        question1 = "How many days do I have to return an item?"

        response1 = rag.query(question1)
        print(f"\nQ: {question1}")
        print(f"\nA: {response1.answer}")
        print(f"\nSources ({len(response1.sources)}):")
        for src in response1.sources[:2]:
            print(f"  - {src['source']} (score: {src['score']})")

        # Test query 2: VIP benefits
        print("\n" + "-" * 40)
        print("Query 2: VIP Benefits")
        print("-" * 40)
        question2 = "What extra benefits do Platinum members get?"

        response2 = rag.query(question2)
        print(f"\nQ: {question2}")
        print(f"\nA: {response2.answer}")

        # Test query 3: Warranty
        print("\n" + "-" * 40)
        print("Query 3: Warranty")
        print("-" * 40)
        question3 = "What is the warranty period for electronics?"

        response3 = rag.query(question3)
        print(f"\nQ: {question3}")
        print(f"\nA: {response3.answer}")

        print("\n✅ RAG Chain working!")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_with_order():
    """Test RAG with order context."""
    print("\n" + "=" * 60)
    print("  TEST 4: RAG with Order Context")
    print("=" * 60 + "\n")

    try:
        from src.rag.rag_chain import RAGChain
        from src.ingestion.pipeline import get_pipeline

        pipeline = get_pipeline()
        rag = RAGChain()

        # Get a sample order
        order = pipeline.get_order("ORD-003")
        if not order:
            print("❌ Could not find order ORD-003")
            return False

        print(f"Order: {order['order_id']}")
        print(f"Customer: {order['customer_name']} ({order['loyalty_tier']})")
        print(f"Product: {order['product_name']}")
        print(f"Status: {order['status']}")

        # Query with order context
        question = "My Smart Watch has a screen issue. What are my options?"

        print(f"\n" + "-" * 40)
        print(f"Query: {question}")
        print("-" * 40)

        response = rag.query_with_order_context(
            question=question,
            order_info=order
        )

        print(f"\nA: {response.answer}")
        print(f"\nMetadata:")
        print(f"  - Order ID: {response.metadata.get('order_id')}")
        print(f"  - Customer Tier: {response.metadata.get('customer_tier')}")
        print(f"  - Sources used: {response.metadata.get('retrieval_count')}")

        print("\n✅ RAG with order context working!")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_quick_ask():
    """Test the quick ask function."""
    print("\n" + "=" * 60)
    print("  TEST 5: Quick Ask Function")
    print("=" * 60 + "\n")

    try:
        from src.rag import ask

        question = "Can I return an opened perfume?"
        print(f"Q: {question}")

        answer = ask(question)
        print(f"\nA: {answer}")

        print("\n✅ Quick ask working!")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  OmniSupport AI - Day 3 Test Suite")
    print("  RAG Pipeline & LLM Integration")
    print("=" * 60)

    results = []

    # Test 1: LLM Factory
    results.append(("LLM Factory", test_llm_factory()))

    # Only continue if we have an LLM provider
    if not results[0][1]:
        print("\n" + "=" * 60)
        print("  ⚠️  Cannot continue without LLM provider")
        print("  Please set an API key in .env file")
        print("=" * 60 + "\n")
        return False

    # Test 2: LLM Client
    results.append(("LLM Client", test_llm_client()))

    # Test 3: RAG Chain
    results.append(("RAG Chain", test_rag_chain()))

    # Test 4: RAG with Order
    results.append(("RAG + Order", test_rag_with_order()))

    # Test 5: Quick Ask
    results.append(("Quick Ask", test_quick_ask()))

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:20} {status}")
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
