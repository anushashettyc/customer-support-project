"""
OmniSupport AI - Text Chunker
=============================
Split documents into chunks suitable for embedding and retrieval.
"""

from typing import List, Optional
from dataclasses import dataclass
import re

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    text: str
    index: int
    start_char: int
    end_char: int
    source: Optional[str] = None


class TextChunker:
    """
    Split text into overlapping chunks for embedding.

    Uses character-based splitting with configurable size and overlap.
    Attempts to split at sentence boundaries when possible.
    """

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Maximum characters per chunk (default: 500)
            chunk_overlap: Overlap between consecutive chunks (default: 50)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Sentence ending patterns
        self.sentence_endings = re.compile(r'[.!?]\s+')

    def chunk_text(
        self,
        text: str,
        source: Optional[str] = None
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: The text to split
            source: Optional source identifier (e.g., filename)

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        # Clean the text
        text = self._preprocess(text)

        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [TextChunk(
                text=text,
                index=0,
                start_char=0,
                end_char=len(text),
                source=source
            )]

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If not at the end, try to break at a sentence boundary
            if end < len(text):
                end = self._find_break_point(text, start, end)

            # Extract chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(TextChunk(
                    text=chunk_text,
                    index=chunk_index,
                    start_char=start,
                    end_char=end,
                    source=source
                ))
                chunk_index += 1

            # Move start position (with overlap)
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start >= len(text) - self.chunk_overlap:
                break

        return chunks

    def chunk_text_simple(self, text: str) -> List[str]:
        """
        Simple chunking that returns just the text strings.

        Args:
            text: The text to split

        Returns:
            List of chunk strings
        """
        chunks = self.chunk_text(text)
        return [chunk.text for chunk in chunks]

    def _preprocess(self, text: str) -> str:
        """
        Preprocess text before chunking.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """
        Find a good break point near the target end position.

        Tries to break at:
        1. Paragraph boundary (double newline)
        2. Sentence boundary (., !, ?)
        3. Clause boundary (;, :, ,)
        4. Word boundary (space)

        Args:
            text: Full text
            start: Start position of current chunk
            end: Target end position

        Returns:
            Adjusted end position
        """
        # Search window: look back up to 100 chars from target end
        search_start = max(start + self.chunk_size // 2, end - 100)
        search_text = text[search_start:end]

        # Try to find paragraph boundary
        para_match = search_text.rfind('\n\n')
        if para_match != -1:
            return search_start + para_match + 2

        # Try to find sentence boundary
        sentence_matches = list(self.sentence_endings.finditer(search_text))
        if sentence_matches:
            last_match = sentence_matches[-1]
            return search_start + last_match.end()

        # Try to find clause boundary
        for delimiter in ['; ', ': ', ', ']:
            pos = search_text.rfind(delimiter)
            if pos != -1:
                return search_start + pos + len(delimiter)

        # Fall back to word boundary
        space_pos = search_text.rfind(' ')
        if space_pos != -1:
            return search_start + space_pos + 1

        # No good break point found, use target end
        return end

    def get_chunk_count(self, text: str) -> int:
        """
        Estimate the number of chunks for a given text.

        Args:
            text: The text to estimate

        Returns:
            Estimated chunk count
        """
        if not text:
            return 0

        text_length = len(text)

        if text_length <= self.chunk_size:
            return 1

        # Calculate with overlap
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        return max(1, (text_length // effective_chunk_size) + 1)


class DocumentChunker:
    """
    Higher-level chunker for processing entire documents with metadata.
    """

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        """
        Initialize the document chunker.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.text_chunker = TextChunker(chunk_size, chunk_overlap)

    def chunk_document(
        self,
        text: str,
        metadata: Optional[dict] = None
    ) -> List[dict]:
        """
        Chunk a document and attach metadata to each chunk.

        Args:
            text: Document text
            metadata: Base metadata to attach to each chunk

        Returns:
            List of dictionaries with 'text' and 'metadata' keys
        """
        if metadata is None:
            metadata = {}

        chunks = self.text_chunker.chunk_text(text, source=metadata.get('source'))

        result = []
        total_chunks = len(chunks)

        for chunk in chunks:
            chunk_metadata = {
                **metadata,
                'chunk_index': chunk.index,
                'total_chunks': total_chunks,
                'start_char': chunk.start_char,
                'end_char': chunk.end_char
            }

            result.append({
                'text': chunk.text,
                'metadata': chunk_metadata
            })

        return result


# Convenience function
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Quick function to chunk text.

    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of chunk strings
    """
    chunker = TextChunker(chunk_size, overlap)
    return chunker.chunk_text_simple(text)
