"""
OmniSupport AI - Ingestion Pipeline
===================================
Orchestrates the complete document ingestion workflow:
Upload → Load → Chunk → Embed → Store
"""

from typing import Union, Optional, List, BinaryIO
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import (
    SAMPLE_POLICIES_DIR,
    SAMPLE_ORDERS_DIR,
    UPLOAD_POLICIES_DIR,
    UPLOAD_ORDERS_DIR,
    LOAD_SAMPLES_ON_STARTUP
)
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.chunker import TextChunker, DocumentChunker
from src.embeddings.embedding_service import EmbeddingService
from src.vectorstore.chroma_store import ChromaStore
from src.utils.helpers import (
    get_file_extension,
    is_policy_file,
    is_order_file,
    generate_doc_id,
    format_timestamp,
    create_metadata
)


@dataclass
class ProcessingResult:
    """Result of processing a file."""
    status: str  # "success" or "error"
    file_type: str  # "policy" or "orders"
    filename: str
    message: str
    details: dict = field(default_factory=dict)


class IngestionPipeline:
    """
    Orchestrates the complete document ingestion workflow.

    Handles:
    - Loading files from disk or uploads
    - Processing policies (chunk → embed → store in ChromaDB)
    - Processing orders (load as DataFrame for direct lookup)
    - Loading sample data on startup
    """

    def __init__(self):
        """Initialize the ingestion pipeline with all required services."""
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker()
        self.text_chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = ChromaStore()

        # Upload directories
        self.uploads_dir = Path("data/uploads")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for order data
        self.orders_df: Optional[pd.DataFrame] = None

        # Track loaded sources
        self._loaded_sources: List[str] = []

        print("✅ Ingestion Pipeline initialized")

    def process_upload(
        self,
        uploaded_file: BinaryIO,
        filename: str
    ) -> ProcessingResult:
        """
        Process an uploaded file automatically.

        Routes to appropriate processor based on file type.

        Args:
            uploaded_file: File-like object from upload
            filename: Original filename

        Returns:
            ProcessingResult with status and details
        """
        try:
            extension = get_file_extension(filename)

            if is_policy_file(filename):
                return self._process_policy_upload(uploaded_file, filename)
            elif is_order_file(filename):
                return self._process_orders_upload(uploaded_file, filename)
            else:
                return ProcessingResult(
                    status="error",
                    file_type="unknown",
                    filename=filename,
                    message=f"❌ Unsupported file format: {extension}",
                    details={"supported": [".pdf", ".txt", ".csv", ".xlsx", ".xls"]}
                )

        except Exception as e:
            return ProcessingResult(
                status="error",
                file_type="unknown",
                filename=filename,
                message=f"❌ Error processing file: {str(e)}",
                details={"error": str(e)}
            )

    def _process_policy_upload(
        self,
        uploaded_file: BinaryIO,
        filename: str
    ) -> ProcessingResult:
        """
        Process an uploaded policy document.

        Pipeline: Load → Chunk → Embed → Store in ChromaDB

        Args:
            uploaded_file: File-like object
            filename: Original filename

        Returns:
            ProcessingResult
        """
        try:
            # Check if already loaded
            if self.vector_store.document_exists(filename):
                # Delete existing and re-process
                self.vector_store.delete_by_metadata({"source": filename})

            # 1. Load text from file
            text = self.loader.load_file(uploaded_file, filename=filename)

            # 2. Chunk the text
            chunks = self.text_chunker.chunk_text_simple(text)

            if not chunks:
                return ProcessingResult(
                    status="error",
                    file_type="policy",
                    filename=filename,
                    message="❌ No text content extracted from file",
                    details={"text_length": len(text) if text else 0}
                )

            # 3. Generate embeddings
            embeddings = self.embedding_service.embed_documents(chunks)

            # 4. Create metadata for each chunk
            metadatas = [
                create_metadata(
                    source=filename,
                    doc_type="policy",
                    chunk_index=i,
                    total_chunks=len(chunks)
                )
                for i in range(len(chunks))
            ]

            # 5. Generate IDs
            ids = [generate_doc_id(filename, i) for i in range(len(chunks))]

            # 6. Store in vector database
            self.vector_store.add_documents(
                texts=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            self._loaded_sources.append(filename)

            return ProcessingResult(
                status="success",
                file_type="policy",
                filename=filename,
                message=f"✅ Policy added: {len(chunks)} chunks indexed",
                details={
                    "chunks_created": len(chunks),
                    "text_length": len(text),
                    "avg_chunk_size": len(text) // len(chunks) if chunks else 0
                }
            )

        except Exception as e:
            return ProcessingResult(
                status="error",
                file_type="policy",
                filename=filename,
                message=f"❌ Error processing policy: {str(e)}",
                details={"error": str(e)}
            )

    def _process_orders_upload(
        self,
        uploaded_file: BinaryIO,
        filename: str
    ) -> ProcessingResult:
        """
        Process an uploaded orders file.

        Loads as DataFrame and stores in memory for direct lookup.

        Args:
            uploaded_file: File-like object
            filename: Original filename

        Returns:
            ProcessingResult
        """
        try:
            # Load as DataFrame
            df = self.loader.load_file(uploaded_file, filename=filename)

            if not isinstance(df, pd.DataFrame):
                return ProcessingResult(
                    status="error",
                    file_type="orders",
                    filename=filename,
                    message="❌ Failed to load as DataFrame",
                    details={}
                )

            # Validate required columns
            required_columns = ['order_id']
            missing = [col for col in required_columns if col not in df.columns]

            if missing:
                return ProcessingResult(
                    status="error",
                    file_type="orders",
                    filename=filename,
                    message=f"❌ Missing required columns: {missing}",
                    details={"columns_found": list(df.columns)}
                )

            # Append to existing DataFrame or create new
            if self.orders_df is None:
                self.orders_df = df
            else:
                # Avoid duplicates by order_id
                existing_ids = set(self.orders_df['order_id'].tolist())
                new_df = df[~df['order_id'].isin(existing_ids)]
                self.orders_df = pd.concat([self.orders_df, new_df], ignore_index=True)

            self._loaded_sources.append(filename)

            return ProcessingResult(
                status="success",
                file_type="orders",
                filename=filename,
                message=f"✅ Orders loaded: {len(df)} records",
                details={
                    "records_loaded": len(df),
                    "total_records": len(self.orders_df),
                    "columns": list(df.columns)
                }
            )

        except Exception as e:
            return ProcessingResult(
                status="error",
                file_type="orders",
                filename=filename,
                message=f"❌ Error processing orders: {str(e)}",
                details={"error": str(e)}
            )

    def process_file_path(self, file_path: Union[str, Path]) -> ProcessingResult:
        """
        Process a file from a file path.

        Args:
            file_path: Path to the file

        Returns:
            ProcessingResult
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return ProcessingResult(
                status="error",
                file_type="unknown",
                filename=file_path.name,
                message=f"❌ File not found: {file_path}",
                details={}
            )

        filename = file_path.name

        if is_policy_file(filename):
            return self._process_policy_path(file_path)
        elif is_order_file(filename):
            return self._process_orders_path(file_path)
        else:
            return ProcessingResult(
                status="error",
                file_type="unknown",
                filename=filename,
                message=f"❌ Unsupported file format",
                details={}
            )

    def _process_policy_path(self, file_path: Path) -> ProcessingResult:
        """Process a policy file from path."""
        try:
            filename = file_path.name

            # Check if already loaded
            if self.vector_store.document_exists(filename):
                return ProcessingResult(
                    status="success",
                    file_type="policy",
                    filename=filename,
                    message=f"ℹ️ Policy already loaded: {filename}",
                    details={"skipped": True}
                )

            # Load text
            text = self.loader.load_file(file_path)

            # Chunk
            chunks = self.text_chunker.chunk_text_simple(text)

            if not chunks:
                return ProcessingResult(
                    status="error",
                    file_type="policy",
                    filename=filename,
                    message="❌ No content extracted",
                    details={}
                )

            # Embed
            embeddings = self.embedding_service.embed_documents(chunks)

            # Metadata
            metadatas = [
                create_metadata(
                    source=filename,
                    doc_type="policy",
                    chunk_index=i,
                    total_chunks=len(chunks)
                )
                for i in range(len(chunks))
            ]

            # IDs
            ids = [generate_doc_id(filename, i) for i in range(len(chunks))]

            # Store
            self.vector_store.add_documents(
                texts=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            self._loaded_sources.append(filename)

            return ProcessingResult(
                status="success",
                file_type="policy",
                filename=filename,
                message=f"✅ Policy added: {len(chunks)} chunks",
                details={"chunks_created": len(chunks)}
            )

        except Exception as e:
            return ProcessingResult(
                status="error",
                file_type="policy",
                filename=file_path.name,
                message=f"❌ Error: {str(e)}",
                details={"error": str(e)}
            )

    def _process_orders_path(self, file_path: Path) -> ProcessingResult:
        """Process an orders file from path."""
        try:
            filename = file_path.name

            # Load DataFrame
            df = self.loader.load_file(file_path)

            if self.orders_df is None:
                self.orders_df = df
            else:
                existing_ids = set(self.orders_df['order_id'].tolist())
                new_df = df[~df['order_id'].isin(existing_ids)]
                if len(new_df) > 0:
                    self.orders_df = pd.concat([self.orders_df, new_df], ignore_index=True)

            self._loaded_sources.append(filename)

            return ProcessingResult(
                status="success",
                file_type="orders",
                filename=filename,
                message=f"✅ Orders loaded: {len(df)} records",
                details={"records_loaded": len(df)}
            )

        except Exception as e:
            return ProcessingResult(
                status="error",
                file_type="orders",
                filename=file_path.name,
                message=f"❌ Error: {str(e)}",
                details={"error": str(e)}
            )

    def load_sample_data(self) -> dict:
        """
        Load all sample data from data/samples/ directory.

        Called on application startup if LOAD_SAMPLES_ON_STARTUP is True.

        Returns:
            Dictionary with loading results
        """
        results = {
            "policies": [],
            "orders": [],
            "total_chunks": 0,
            "total_orders": 0,
            "errors": []
        }

        print("\n" + "="*50)
        print("Loading Sample Data...")
        print("="*50)

        # Load sample policies
        policy_dir = Path(SAMPLE_POLICIES_DIR)
        if policy_dir.exists():
            for policy_file in sorted(policy_dir.glob("*.txt")):
                result = self._process_policy_path(policy_file)
                results["policies"].append({
                    "filename": result.filename,
                    "status": result.status,
                    "message": result.message
                })
                if result.status == "success" and not result.details.get("skipped"):
                    results["total_chunks"] += result.details.get("chunks_created", 0)
                elif result.status == "error":
                    results["errors"].append(result.message)
                print(f"  {result.message}")

            # Also load PDFs if any
            for policy_file in sorted(policy_dir.glob("*.pdf")):
                result = self._process_policy_path(policy_file)
                results["policies"].append({
                    "filename": result.filename,
                    "status": result.status,
                    "message": result.message
                })
                if result.status == "success":
                    results["total_chunks"] += result.details.get("chunks_created", 0)
                print(f"  {result.message}")

        # Load sample orders
        orders_dir = Path(SAMPLE_ORDERS_DIR)
        if orders_dir.exists():
            for orders_file in sorted(orders_dir.glob("*.csv")):
                result = self._process_orders_path(orders_file)
                results["orders"].append({
                    "filename": result.filename,
                    "status": result.status,
                    "message": result.message
                })
                if result.status == "success":
                    results["total_orders"] += result.details.get("records_loaded", 0)
                elif result.status == "error":
                    results["errors"].append(result.message)
                print(f"  {result.message}")

            # Also load Excel files
            for orders_file in sorted(orders_dir.glob("*.xlsx")):
                result = self._process_orders_path(orders_file)
                results["orders"].append({
                    "filename": result.filename,
                    "status": result.status,
                    "message": result.message
                })
                if result.status == "success":
                    results["total_orders"] += result.details.get("records_loaded", 0)
                print(f"  {result.message}")

        print("="*50)
        print(f"✅ Sample data loaded:")
        print(f"   - Policies: {len(results['policies'])} files, {results['total_chunks']} chunks")
        print(f"   - Orders: {len(results['orders'])} files, {results['total_orders']} records")
        print("="*50 + "\n")

        return results

    def get_order(self, order_id: str) -> Optional[dict]:
        """
        Get order details by order ID.

        Args:
            order_id: The order ID to look up

        Returns:
            Dictionary with order details or None if not found
        """
        if self.orders_df is None or self.orders_df.empty:
            return None

        # Normalize order_id
        order_id = order_id.upper().strip()

        # Find order
        order = self.orders_df[self.orders_df['order_id'].str.upper() == order_id]

        if order.empty:
            return None

        # Convert to dictionary
        order_dict = order.iloc[0].to_dict()

        # Convert NaT/NaN to None for JSON serialization
        for key, value in order_dict.items():
            if pd.isna(value):
                order_dict[key] = None
            elif hasattr(value, 'isoformat'):
                order_dict[key] = value.isoformat()

        return order_dict

    def get_customer_orders(self, customer_id: str) -> List[dict]:
        """
        Get all orders for a customer.

        Args:
            customer_id: The customer ID

        Returns:
            List of order dictionaries
        """
        if self.orders_df is None or self.orders_df.empty:
            return []

        customer_id = customer_id.upper().strip()
        orders = self.orders_df[self.orders_df['customer_id'].str.upper() == customer_id]

        result = []
        for _, row in orders.iterrows():
            order_dict = row.to_dict()
            for key, value in order_dict.items():
                if pd.isna(value):
                    order_dict[key] = None
                elif hasattr(value, 'isoformat'):
                    order_dict[key] = value.isoformat()
            result.append(order_dict)

        return result

    def search_policies(
        self,
        query: str,
        top_k: int = 5
    ) -> List[dict]:
        """
        Search policies using semantic search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant policy chunks
        """
        results = self.vector_store.search(query, top_k=top_k)

        return [
            {
                "text": r.text,
                "source": r.metadata.get("source", "unknown"),
                "score": r.score,
                "chunk_index": r.metadata.get("chunk_index", 0)
            }
            for r in results
        ]

    def get_stats(self) -> dict:
        """
        Get pipeline statistics.

        Returns:
            Dictionary with statistics
        """
        vector_stats = self.vector_store.get_collection_stats()

        return {
            "vector_store": vector_stats,
            "orders": {
                "total_records": len(self.orders_df) if self.orders_df is not None else 0,
                "columns": list(self.orders_df.columns) if self.orders_df is not None else []
            },
            "loaded_sources": self._loaded_sources
        }

    def clear_all(self) -> bool:
        """
        Clear all data from the pipeline.

        Returns:
            True if successful
        """
        try:
            self.vector_store.clear_collection()
            self.orders_df = None
            self._loaded_sources = []
            print("✅ All data cleared")
            return True
        except Exception as e:
            print(f"❌ Error clearing data: {str(e)}")
            return False


# Global pipeline instance
_pipeline_instance: Optional[IngestionPipeline] = None


def get_pipeline() -> IngestionPipeline:
    """
    Get the global pipeline instance (singleton).

    Returns:
        IngestionPipeline instance
    """
    global _pipeline_instance

    if _pipeline_instance is None:
        _pipeline_instance = IngestionPipeline()

        if LOAD_SAMPLES_ON_STARTUP:
            _pipeline_instance.load_sample_data()

    return _pipeline_instance
