"""
OmniSupport AI - Configuration Settings
========================================
Central configuration for all application settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# PATH CONFIGURATIONS
# ============================================================
# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
UPLOADS_DIR = DATA_DIR / "uploads"

# Sample data paths
SAMPLE_ORDERS_DIR = SAMPLES_DIR / "orders"
SAMPLE_POLICIES_DIR = SAMPLES_DIR / "policies"
SAMPLE_COMPLAINTS_DIR = SAMPLES_DIR / "sample_complaints"

# Upload paths
UPLOAD_ORDERS_DIR = UPLOADS_DIR / "orders"
UPLOAD_POLICIES_DIR = UPLOADS_DIR / "policies"

# Vector store path
VECTORSTORE_DIR = BASE_DIR / "vectorstore_db"

# ============================================================
# API CONFIGURATIONS
# ============================================================
# Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-pro"  # Free tier model (use gemini-pro for v1beta API)

# ============================================================
# EMBEDDING CONFIGURATIONS
# ============================================================
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # HuggingFace sentence-transformer
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

# ============================================================
# CHUNKING CONFIGURATIONS
# ============================================================
CHUNK_SIZE = 500          # Characters per chunk
CHUNK_OVERLAP = 50        # Overlap between chunks

# ============================================================
# VECTOR STORE CONFIGURATIONS
# ============================================================
CHROMA_COLLECTION_NAME = "omnisupport_knowledge_base"
TOP_K_RESULTS = 5         # Number of similar documents to retrieve

# ============================================================
# DOCUMENT PROCESSING
# ============================================================
SUPPORTED_POLICY_FORMATS = [".pdf", ".txt"]
SUPPORTED_ORDER_FORMATS = [".csv", ".xlsx", ".xls"]
ALL_SUPPORTED_FORMATS = SUPPORTED_POLICY_FORMATS + SUPPORTED_ORDER_FORMATS

# ============================================================
# AGENT CONFIGURATIONS
# ============================================================
AGENT_TEMPERATURE = 0.3   # Lower = more deterministic responses
AGENT_MAX_TOKENS = 1024   # Max response length

# Agent-specific settings
AGENT_CONFIG = {
    "profiler": {
        "name": "Customer 360 Profiler",
        "description": "Fetches customer order history and profile data",
        "icon": "👤"
    },
    "complaint": {
        "name": "Complaint Analyzer",
        "description": "Analyzes sentiment, intent, and urgency",
        "icon": "🔍"
    },
    "policy": {
        "name": "Policy Researcher",
        "description": "Performs RAG search on policy documents",
        "icon": "📚"
    },
    "arbitrator": {
        "name": "Resolution Arbitrator",
        "description": "Makes fair decisions based on policy and customer value",
        "icon": "⚖️"
    },
    "validator": {
        "name": "Response Validator",
        "description": "Validates response quality and safety",
        "icon": "✅"
    }
}

# ============================================================
# APPLICATION SETTINGS
# ============================================================
APP_TITLE = "OmniSupport AI"
APP_SUBTITLE = "360° Autonomous Customer Support & Dispute Resolution"
APP_ICON = "🎯"
LOAD_SAMPLES_ON_STARTUP = False  # Admin must manually upload data

# Streamlit page config
PAGE_CONFIG = {
    "page_title": APP_TITLE,
    "page_icon": APP_ICON,
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL = "INFO"
LOG_AGENT_STEPS = True    # Show agent reasoning in UI

# ============================================================
# RESOLUTION TYPES
# ============================================================
RESOLUTION_TYPES = [
    "Full Refund",
    "Partial Refund",
    "Store Credit",
    "Replacement",
    "Repair/Service",
    "Denial with Explanation",
    "Escalate to Human Agent"
]

# ============================================================
# CUSTOMER TIERS
# ============================================================
LOYALTY_TIERS = {
    "Bronze": {"discount": 0, "extended_return_days": 0, "priority": "Standard"},
    "Silver": {"discount": 5, "extended_return_days": 7, "priority": "Medium"},
    "Gold": {"discount": 10, "extended_return_days": 14, "priority": "High"},
    "Platinum": {"discount": 15, "extended_return_days": 30, "priority": "VIP"}
}
