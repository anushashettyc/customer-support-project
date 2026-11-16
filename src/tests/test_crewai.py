"""
OmniSupport AI - CrewAI Test Script
====================================
Test the CrewAI implementation with sample complaints.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def main():
    """Run CrewAI test."""
    print("\n" + "="*60)
    print("  OmniSupport AI - CrewAI Framework Test")
    print("="*60 + "\n")

    # Ensure data is loaded
    print("Initializing system...")
    from src.ingestion.pipeline import get_pipeline
    pipeline = get_pipeline()

    stats = pipeline.get_stats()
    if stats['vector_store'].get('document_count', 0) == 0:
        print("Loading sample data...")
        pipeline.load_sample_data()

    print("✅ System initialized\n")

    # Import CrewAI implementation
    from src.agents.crewai_implementation import OmniSupportCrew

    # Create crew
    crew = OmniSupportCrew()

    # Test complaint
    complaint = input("Enter complaint (or press Enter for default): ").strip()
    if not complaint:
        complaint = "My order ORD-003 Smart Watch screen is flickering. I need this fixed ASAP!"
        print(f"\nUsing default complaint: {complaint}\n")

    # Process complaint
    print("="*60)
    print("Processing with CrewAI...")
    print("="*60 + "\n")

    result = crew.process_complaint(complaint, verbose=True)

    # Display result
    print("\n" + "="*60)
    print("  FINAL RESULT")
    print("="*60)
    print(result)
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
