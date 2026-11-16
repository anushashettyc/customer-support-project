"""
Test Unsupported File Format Error Handling
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.document_loader import DocumentLoader

def test_unsupported_formats():
    """Test error handling for unsupported file formats."""

    print("=" * 70)
    print("Testing Unsupported File Format Error Handling")
    print("=" * 70)

    loader = DocumentLoader()

    # Test cases: (filename, category)
    test_cases = [
        ("photo.jpg", "Image"),
        ("document.zip", "Archive"),
        ("report.docx", "Word Document"),
        ("presentation.pptx", "PowerPoint"),
        ("data.json", "JSON Data"),
        ("video.mp4", "Media File"),
        ("program.exe", "Executable"),
        ("unknown.xyz", "Unknown Format"),
    ]

    for filename, category in test_cases:
        print(f"\n📄 Testing: {filename} ({category})")
        print("-" * 70)

        try:
            # This should raise an error
            loader.load_file("dummy_path", filename=filename)
            print(f"❌ FAILED: Should have raised ValueError")
        except ValueError as e:
            print(f"✅ PASSED: Proper error caught")
            print(f"\n{str(e)}\n")
        except Exception as e:
            print(f"❌ FAILED: Wrong error type: {type(e).__name__}")

    print("=" * 70)
    print("✅ All unsupported format tests completed")
    print("=" * 70)

if __name__ == "__main__":
    test_unsupported_formats()
