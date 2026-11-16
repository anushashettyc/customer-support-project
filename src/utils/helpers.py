"""
OmniSupport AI - Helper Utilities
=================================
Common utility functions used across the application.
"""

import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Union, List, Optional


def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.

    Args:
        filename: Name of the file

    Returns:
        Lowercase file extension including the dot (e.g., '.pdf')
    """
    return Path(filename).suffix.lower()


def is_policy_file(filename: str) -> bool:
    """
    Check if file is a policy document (PDF/TXT).

    Args:
        filename: Name of the file

    Returns:
        True if file is a policy format
    """
    policy_formats = ['.pdf', '.txt']
    return get_file_extension(filename) in policy_formats


def is_order_file(filename: str) -> bool:
    """
    Check if file is an order data file (CSV/Excel).

    Args:
        filename: Name of the file

    Returns:
        True if file is an order format
    """
    order_formats = ['.csv', '.xlsx', '.xls']
    return get_file_extension(filename) in order_formats


def is_supported_format(filename: str) -> bool:
    """
    Check if file format is supported.

    Args:
        filename: Name of the file

    Returns:
        True if format is supported
    """
    return is_policy_file(filename) or is_order_file(filename)


def generate_doc_id(source: str, chunk_index: int) -> str:
    """
    Generate a unique document ID for a chunk.

    Args:
        source: Source filename
        chunk_index: Index of the chunk

    Returns:
        Unique document ID string
    """
    # Create hash of source name for uniqueness
    source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
    return f"doc_{source_hash}_{chunk_index:04d}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing special characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace special characters
    sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime as a string.

    Args:
        dt: Datetime object (default: now)

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp_id() -> str:
    """
    Generate a timestamp-based ID.

    Returns:
        Timestamp ID string
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.

    Args:
        text: Raw text

    Returns:
        Cleaned text
    """
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count (rough estimate: 1 token ≈ 4 characters).

    Args:
        text: Text to count

    Returns:
        Approximate token count
    """
    return len(text) // 4


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def extract_order_id(text: str) -> Optional[str]:
    """
    Extract order ID from text using pattern matching.

    Args:
        text: Text that may contain an order ID

    Returns:
        Extracted order ID or None
    """
    # Pattern: ORD-XXX or ORD_XXX or ORDXXX
    patterns = [
        r'ORD[-_]?\d{3,}',  # ORD-001, ORD_001, ORD001
        r'ORDER[-_]?\d{3,}',  # ORDER-001
        r'#\d{3,}',  # #001
    ]

    for pattern in patterns:
        match = re.search(pattern, text.upper())
        if match:
            # Normalize to ORD-XXX format
            order_id = match.group()
            order_id = re.sub(r'[_#]', '-', order_id)
            if not order_id.startswith('ORD'):
                order_id = 'ORD-' + order_id.lstrip('-')
            return order_id

    return None


def extract_customer_id(text: str) -> Optional[str]:
    """
    Extract customer ID from text using pattern matching.

    Args:
        text: Text that may contain a customer ID

    Returns:
        Extracted customer ID or None
    """
    # Pattern: CUST-XXX
    pattern = r'CUST[-_]?\d{3,}'
    match = re.search(pattern, text.upper())

    if match:
        customer_id = match.group()
        customer_id = re.sub(r'_', '-', customer_id)
        return customer_id

    return None


def format_currency(amount: Union[int, float]) -> str:
    """
    Format a number as currency.

    Args:
        amount: Numeric amount

    Returns:
        Formatted currency string
    """
    return f"${amount:,.2f}"


def calculate_days_since(date_str: str, date_format: str = "%Y-%m-%d") -> int:
    """
    Calculate days since a given date.

    Args:
        date_str: Date string
        date_format: Format of the date string

    Returns:
        Number of days since the date
    """
    try:
        past_date = datetime.strptime(date_str, date_format)
        today = datetime.now()
        delta = today - past_date
        return delta.days
    except ValueError:
        return -1


def get_loyalty_tier_info(tier: str) -> dict:
    """
    Get loyalty tier information.

    Args:
        tier: Tier name (Bronze, Silver, Gold, Platinum)

    Returns:
        Dictionary with tier benefits
    """
    tiers = {
        "Bronze": {
            "discount": 0,
            "extended_return_days": 0,
            "priority": "Standard",
            "return_window": 30
        },
        "Silver": {
            "discount": 5,
            "extended_return_days": 7,
            "priority": "Medium",
            "return_window": 37
        },
        "Gold": {
            "discount": 10,
            "extended_return_days": 14,
            "priority": "High",
            "return_window": 44
        },
        "Platinum": {
            "discount": 15,
            "extended_return_days": 30,
            "priority": "VIP",
            "return_window": 60
        }
    }

    return tiers.get(tier, tiers["Bronze"])


def create_metadata(
    source: str,
    doc_type: str,
    chunk_index: int = 0,
    total_chunks: int = 1,
    **extra
) -> dict:
    """
    Create standardized metadata for a document chunk.

    Args:
        source: Source filename
        doc_type: Type of document (policy/order)
        chunk_index: Index of this chunk
        total_chunks: Total number of chunks
        **extra: Additional metadata fields

    Returns:
        Metadata dictionary
    """
    metadata = {
        "source": source,
        "type": doc_type,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "indexed_at": format_timestamp()
    }
    metadata.update(extra)
    return metadata
