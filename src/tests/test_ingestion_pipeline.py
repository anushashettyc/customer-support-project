"""
OmniSupport AI - Day 2 Test Script
==================================
Test the complete ingestion pipeline.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_pipeline():
    """Test the complete ingestion pipeline."""

    print("\n" + "="*60)
    print("  OmniSupport AI - Day 2 Pipeline Test")
    print("="*60 + "\n")

    # Test 1: Import all modules
    print("1. Testing imports...")
    try:
        from src.utils.helpers import get_file_extension, extract_order_id
        from src.ingestion.document_loader import DocumentLoader
        from src.ingestion.chunker import TextChunker
        from src.embeddings.embedding_service import EmbeddingService
        from src.vectorstore.chroma_store import ChromaStore
        from src.ingestion.pipeline import IngestionPipeline
        print("   ✅ All imports successful\n")
    except ImportError as e:
        print(f"   ❌ Import error: {e}\n")
        return False

    # Test 2: Document Loader
    print("2. Testing Document Loader...")
    try:
        loader = DocumentLoader()

        # Test TXT loading
        txt_path = project_root / "data/samples/policies/return_policy.txt"
        if txt_path.exists():
            text = loader.load_txt(txt_path)
            print(f"   ✅ Loaded TXT: {len(text)} characters")

        # Test CSV loading
        csv_path = project_root / "data/samples/orders/sample_orders.csv"
        if csv_path.exists():
            df = loader.load_csv(csv_path)
            print(f"   ✅ Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
        print()
    except Exception as e:
        print(f"   ❌ Document Loader error: {e}\n")
        return False

    # Test 3: Text Chunker
    print("3. Testing Text Chunker...")
    try:
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)

        sample_text = "This is a test. " * 100  # ~1600 characters
        chunks = chunker.chunk_text_simple(sample_text)

        print(f"   ✅ Chunked {len(sample_text)} chars into {len(chunks)} chunks")
        print(f"   ✅ Avg chunk size: {sum(len(c) for c in chunks) // len(chunks)} chars")
        print()
    except Exception as e:
        print(f"   ❌ Chunker error: {e}\n")
        return False

    # Test 4: Embedding Service
    print("4. Testing Embedding Service...")
    try:
        embedder = EmbeddingService()

        # Single embedding
        text = "What is the return policy for electronics?"
        embedding = embedder.embed_text(text)
        print(f"   ✅ Single embedding: {len(embedding)} dimensions")

        # Batch embedding
        texts = ["First text", "Second text", "Third text"]
        embeddings = embedder.embed_documents(texts)
        print(f"   ✅ Batch embeddings: {len(embeddings)} vectors")
        print()
    except Exception as e:
        print(f"   ❌ Embedding error: {e}\n")
        return False

    # Test 5: Vector Store
    print("5. Testing Vector Store (ChromaDB)...")
    try:
        store = ChromaStore()

        # Clear for fresh test
        store.clear_collection()

        # Add documents
        texts = [
            "Return policy allows 30 days for refunds.",
            "Warranty covers manufacturing defects for 1 year.",
            "VIP customers get extended 60-day return window."
        ]
        metadatas = [
            {"source": "test_policy.txt", "type": "policy"},
            {"source": "test_warranty.txt", "type": "policy"},
            {"source": "test_vip.txt", "type": "policy"}
        ]

        ids = store.add_documents(texts=texts, metadatas=metadatas)
        print(f"   ✅ Added {len(ids)} documents")

        # Search
        results = store.search("What is the return window?", top_k=2)
        print(f"   ✅ Search returned {len(results)} results")
        if results:
            print(f"   ✅ Top result score: {results[0].score:.4f}")

        # Stats
        stats = store.get_collection_stats()
        print(f"   ✅ Collection has {stats['document_count']} documents")
        print()
    except Exception as e:
        print(f"   ❌ Vector Store error: {e}\n")
        return False

    # Test 6: Full Pipeline
    print("6. Testing Full Pipeline...")
    try:
        # Create fresh pipeline
        pipeline = IngestionPipeline()

        # Clear existing data
        pipeline.clear_all()

        # Load sample data
        results = pipeline.load_sample_data()

        print(f"   ✅ Loaded {len(results['policies'])} policy files")
        print(f"   ✅ Loaded {len(results['orders'])} order files")
        print(f"   ✅ Total chunks: {results['total_chunks']}")
        print(f"   ✅ Total orders: {results['total_orders']}")

        # Test order lookup
        order = pipeline.get_order("ORD-001")
        if order:
            print(f"   ✅ Order lookup works: {order.get('customer_name')}")

        # Test policy search
        policy_results = pipeline.search_policies("return policy", top_k=3)
        print(f"   ✅ Policy search returned {len(policy_results)} results")

        # Get stats
        stats = pipeline.get_stats()
        print(f"   ✅ Pipeline stats retrieved")
        print()
    except Exception as e:
        print(f"   ❌ Pipeline error: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    # Test 7: Helper functions
    print("7. Testing Helper Functions...")
    try:
        from src.utils.helpers import (
            extract_order_id,
            extract_customer_id,
            calculate_days_since,
            get_loyalty_tier_info
        )

        # Test order ID extraction
        order_id = extract_order_id("My order number is ORD-001 and I want a refund")
        print(f"   ✅ Extracted order ID: {order_id}")

        # Test customer ID extraction
        customer_id = extract_customer_id("Customer CUST-101 called")
        print(f"   ✅ Extracted customer ID: {customer_id}")

        # Test loyalty tier
        tier_info = get_loyalty_tier_info("Gold")
        print(f"   ✅ Gold tier return window: {tier_info['return_window']} days")
        print()
    except Exception as e:
        print(f"   ❌ Helper functions error: {e}\n")
        return False

    print("="*60)
    print("  ✅ ALL TESTS PASSED!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
