"""
OmniSupport AI - Document Loader
================================
Load documents in multiple formats: PDF, TXT, CSV, Excel.
"""

import os
from pathlib import Path
from typing import Union, BinaryIO, Optional
import pandas as pd

# PDF processing
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from src.utils.helpers import get_file_extension, clean_text


class DocumentLoader:
    """
    Universal document loader supporting multiple file formats.

    Supported formats:
        - PDF (.pdf) → Returns extracted text
        - TXT (.txt) → Returns raw text
        - CSV (.csv) → Returns pandas DataFrame
        - Excel (.xlsx, .xls) → Returns pandas DataFrame
    """

    def __init__(self):
        """Initialize the document loader."""
        self._validate_dependencies()

    def _validate_dependencies(self):
        """Check that required libraries are available."""
        if PdfReader is None:
            print("Warning: pypdf not installed. PDF loading will not work.")

    def load_file(
        self,
        file_source: Union[str, Path, BinaryIO],
        filename: Optional[str] = None
    ) -> Union[str, pd.DataFrame]:
        """
        Load a file and return its contents.

        Automatically detects file type and routes to appropriate loader.

        Args:
            file_source: File path (str/Path) or file-like object (uploaded file)
            filename: Original filename (required if file_source is file-like object)

        Returns:
            str for text documents (PDF, TXT)
            pd.DataFrame for data files (CSV, Excel)

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file path doesn't exist
        """
        # Determine filename
        if isinstance(file_source, (str, Path)):
            filepath = Path(file_source)
            filename = filepath.name
        elif filename is None:
            raise ValueError("filename required when loading from file-like object")

        # Get extension FIRST (before checking if file exists)
        extension = get_file_extension(filename).lower()

        # Check format validity BEFORE checking if file exists
        # This gives better error messages for unsupported formats

        # Supported formats
        if extension in ['.pdf', '.txt', '.csv', '.xlsx', '.xls']:
            # Valid format - will process below
            pass
        # Unsupported formats with helpful error messages
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
            raise ValueError(
                f"❌ Image files ({extension}) are not supported.\n"
                f"💡 Supported formats: PDF, TXT (policies) | CSV, XLSX (orders)"
            )
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            raise ValueError(
                f"❌ Archive files ({extension}) are not supported.\n"
                f"💡 Please extract the archive and upload individual files.\n"
                f"   Supported formats: PDF, TXT (policies) | CSV, XLSX (orders)"
            )
        elif extension in ['.doc', '.docx']:
            raise ValueError(
                f"❌ Word documents ({extension}) are not supported.\n"
                f"💡 Please convert to PDF or TXT format.\n"
                f"   Supported formats: PDF, TXT (policies) | CSV, XLSX (orders)"
            )
        elif extension in ['.ppt', '.pptx']:
            raise ValueError(
                f"❌ PowerPoint files ({extension}) are not supported.\n"
                f"💡 Please convert to PDF format.\n"
                f"   Supported formats: PDF, TXT (policies) | CSV, XLSX (orders)"
            )
        elif extension in ['.json', '.xml', '.yaml', '.yml']:
            raise ValueError(
                f"❌ Data format ({extension}) is not supported.\n"
                f"💡 Please convert to CSV or XLSX format for orders.\n"
                f"   Supported formats: PDF, TXT (policies) | CSV, XLSX (orders)"
            )
        elif extension in ['.mp4', '.avi', '.mov', '.mp3', '.wav']:
            raise ValueError(
                f"❌ Media files ({extension}) are not supported.\n"
                f"💡 This is a document-based system.\n"
                f"   Supported formats: PDF, TXT (policies) | CSV, XLSX (orders)"
            )
        elif extension in ['.exe', '.dll', '.so', '.bin']:
            raise ValueError(
                f"❌ Executable files ({extension}) are not supported for security reasons.\n"
                f"   Supported formats: PDF, TXT (policies) | CSV, XLSX (orders)"
            )
        else:
            raise ValueError(
                f"❌ Unsupported file format: {extension}\n"
                f"💡 Supported formats:\n"
                f"   • Policies: PDF, TXT\n"
                f"   • Orders: CSV, XLSX"
            )

        # NOW check if file exists (only for file paths, not uploaded files)
        if isinstance(file_source, (str, Path)):
            if not filepath.exists():
                raise FileNotFoundError(f"File not found: {filepath}")

        # Route to appropriate loader
        if extension == '.pdf':
            return self.load_pdf(file_source)
        elif extension == '.txt':
            return self.load_txt(file_source)
        elif extension == '.csv':
            return self.load_csv(file_source)
        elif extension in ['.xlsx', '.xls']:
            return self.load_excel(file_source)

    def load_pdf(self, file_source: Union[str, Path, BinaryIO]) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_source: Path to PDF or file-like object

        Returns:
            Extracted text as string
        """
        if PdfReader is None:
            raise ImportError("pypdf is required for PDF loading. Install with: pip install pypdf")

        try:
            reader = PdfReader(file_source)

            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)
            return clean_text(full_text)

        except Exception as e:
            raise RuntimeError(f"Error reading PDF: {str(e)}")

    def load_txt(self, file_source: Union[str, Path, BinaryIO]) -> str:
        """
        Load text from a TXT file.

        Args:
            file_source: Path to TXT file or file-like object

        Returns:
            File contents as string
        """
        try:
            if isinstance(file_source, (str, Path)):
                with open(file_source, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                # File-like object (e.g., Streamlit upload)
                text = file_source.read()
                if isinstance(text, bytes):
                    text = text.decode('utf-8')

            return clean_text(text)

        except UnicodeDecodeError:
            # Try with different encoding
            if isinstance(file_source, (str, Path)):
                with open(file_source, 'r', encoding='latin-1') as f:
                    text = f.read()
                return clean_text(text)
            raise
        except Exception as e:
            raise RuntimeError(f"Error reading TXT file: {str(e)}")

    def load_csv(self, file_source: Union[str, Path, BinaryIO]) -> pd.DataFrame:
        """
        Load data from a CSV file.

        Args:
            file_source: Path to CSV file or file-like object

        Returns:
            pandas DataFrame with CSV data
        """
        try:
            df = pd.read_csv(file_source)

            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()

            # Convert date columns if present
            date_columns = ['order_date', 'delivery_date', 'date', 'created_at']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            return df

        except Exception as e:
            raise RuntimeError(f"Error reading CSV file: {str(e)}")

    def load_excel(self, file_source: Union[str, Path, BinaryIO]) -> pd.DataFrame:
        """
        Load data from an Excel file.

        Args:
            file_source: Path to Excel file or file-like object

        Returns:
            pandas DataFrame with Excel data (first sheet)
        """
        try:
            df = pd.read_excel(file_source, engine='openpyxl')

            # Clean column names
            df.columns = df.columns.str.strip()

            # Convert date columns if present
            date_columns = ['order_date', 'delivery_date', 'date', 'created_at']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            return df

        except Exception as e:
            raise RuntimeError(f"Error reading Excel file: {str(e)}")

    def get_file_info(self, file_source: Union[str, Path]) -> dict:
        """
        Get information about a file.

        Args:
            file_source: Path to file

        Returns:
            Dictionary with file information
        """
        filepath = Path(file_source)

        if not filepath.exists():
            return {"error": "File not found"}

        stats = filepath.stat()

        return {
            "filename": filepath.name,
            "extension": get_file_extension(filepath.name),
            "size_bytes": stats.st_size,
            "modified": stats.st_mtime,
            "path": str(filepath.absolute())
        }


# Convenience function for quick loading
def load_document(file_path: Union[str, Path]) -> Union[str, pd.DataFrame]:
    """
    Quick function to load a document.

    Args:
        file_path: Path to the document

    Returns:
        Document contents (str or DataFrame)
    """
    loader = DocumentLoader()
    return loader.load_file(file_path)
