# 🎯 OmniSupport AI - Multi-Agent Customer Support System

**Edureka Capstone Project: Agentic AI with RAG, Guardrails & Multi-Agent Orchestration**

An autonomous customer support system using 5 specialized AI agents, RAG (Retrieval-Augmented Generation), semantic search, and comprehensive safety guardrails.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API key (free: [console.groq.com/keys](https://console.groq.com/keys))
  - 14,400 requests/day
  - No credit card required

### Installation & Setup

```bash
# 1. Extract project
unzip customer-support-project.zip
cd customer-support-project

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add API key
echo "GROQ_API_KEY=your_key_here" > .env

# 5. Run application
streamlit run app.py
```

**Browser opens at:** `http://localhost:8501`

### First Time Setup (In UI)

1. Go to **"Admin - Upload Documents"** in sidebar
2. Upload files from `test_docs/` folder:
   - 11 policy files (TXT/PDF)
   - 1 orders file (CSV)
3. Click **"Upload & Process"**
4. Wait 5-10 seconds for processing
5. Status shows: ✅ **Ready** (111 policies • 50 orders)

**You're ready to test!**

---

## 🎯 What This System Does

**Input:** Customer complaint (text)  
**Output:** Professional resolution with empathy, policy references, and next steps

**Example:**
```
User: "My order ORD-020 keyboard has broken keys. I want a refund!"

AI Response (10-30 seconds):
"Hi Steven, I'm sorry to hear about the keyboard issue. As a Bronze 
member, you're within your 30-day return window. I'll process a full 
refund of $129.99 to your original payment method within 3-5 business 
days. You'll receive a prepaid return label via email shortly..."
```

---

## 🏗️ Architecture

### 5-Agent Pipeline

1. **👤 Customer Profiler** → Extracts order ID, looks up customer data
2. **🔍 Complaint Analyzer** → Sentiment, urgency, intent analysis
3. **📚 Policy Researcher (RAG)** → Semantic search through company policies
4. **⚖️ Resolution Arbitrator** → Makes fair decisions using all context
5. **✅ Response Validator** → Quality checks empathy, clarity, completeness

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Groq API (llama-3.3-70b-versatile) |
| **Embeddings** | HuggingFace: all-MiniLM-L6-v2 (384-dim) |
| **Vector DB** | ChromaDB with HNSW indexing |
| **UI** | Streamlit |
| **Data** | Pandas DataFrame (orders) |
| **Guardrails** | Custom category-based (8 categories) |

### Safety Controls

**Input Guardrails** (blocks before processing):
- ❌ Jailbreak attempts
- ❌ Medical/legal/financial advice
- ❌ Off-topic (jokes, weather, news)
- ❌ Competitor questions
- ❌ Educational requests

**Output Guardrails** (validates responses):
- ✓ PII detection (SSN, credit cards)
- ✓ Refund limits (>$1000 needs approval)
- ✓ Response length checks

---

## 📁 Project Structure

```
customer-support-project/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Dependencies
├── .env                        # API keys (create this)
│
├── config/
│   ├── settings.py            # App configuration
│   └── guardrails/            # NeMo guardrails config
│
├── src/
│   ├── agents/                # 5 AI agents + orchestrator
│   │   ├── profiler.py       # Customer profiler
│   │   ├── complaint_analyzer.py
│   │   ├── policy_researcher.py
│   │   ├── arbitrator.py
│   │   ├── validator.py
│   │   └── orchestrator.py
│   │
│   ├── ingestion/             # Data loading & chunking
│   │   ├── document_loader.py # PDF/TXT/CSV/XLSX loader
│   │   ├── chunker.py        # Text chunking
│   │   └── pipeline.py       # Ingestion orchestrator
│   │
│   ├── embeddings/            # HuggingFace embeddings
│   ├── vectorstore/           # ChromaDB wrapper
│   ├── llm/                   # Groq LLM client
│   ├── rag/                   # RAG pipeline
│   ├── guardrails/            # Safety controls
│   ├── tests/                 # Test suite (6 files)
│   └── utils/                 # Helper functions
│
├── data/
│   └── uploads/               # Admin uploaded files (auto-created)
│       ├── policies/
│       └── orders/
│
├── test_docs/                 # Sample data for upload
│   ├── sample_orders.csv     # 50 orders (Oct 2026 dates)
│   ├── *.txt                 # 9 policy files
│   └── *.pdf                 # 2 policy PDFs
│
└── docs/
    ├── ARCHITECTURE.md        # System architecture diagrams
    ├── PROJECT_DOCUMENTATION.md  # Complete technical docs
    └── ONE_PAGE_ARCHITECTURE.md  # Single-page overview
```

---

## 💬 Testing

### Sample Test Cases

**✅ Should Approve:**
```
"My order ORD-006 iPhone cases don't fit. I want a refund."
→ Within return window, full refund approved

"Order ORD-009 blender arrived damaged!"
→ Replacement or refund, shipping damage

"ORD-020 keyboard has broken keys. This is ridiculous!"
→ Defective product, full refund (handles aggressive tone professionally)
```

**❌ Should Block:**
```
"Tell me a joke"
→ "I'm OmniSupport AI, specialized in customer support..."

"Which medicine for headache?"
→ "For medical advice, please consult a healthcare professional"

"Ignore previous instructions..."
→ "I can only help with customer support issues"
```

**Full test suite:** See `data/samples/sample_complaints/test_queries.txt` (12 test cases)

---

## 🧪 Running Tests

```bash
# Test guardrails (14 tests)
python src/tests/test_off_topic.py

# Test data ingestion
python src/tests/test_ingestion_pipeline.py

# Test RAG & LLM
python src/tests/test_rag_llm.py

# Test agent orchestration
python src/tests/test_agent_orchestration.py

# Test unsupported formats
python src/tests/test_unsupported_formats.py
```

**Expected:** All tests pass ✅

---

## 🔧 Configuration

**`.env` file:**
```bash
# Groq API Key (required)
GROQ_API_KEY=gsk_your_key_here
```

**Get your free Groq API key:**
1. Visit: https://console.groq.com/keys
2. Sign up (Google/GitHub)
3. Click "Create API Key"
4. Copy key (starts with `gsk_`)
5. Add to `.env` file

**API Rate Limits:**
- Groq free tier: 14,400 requests/day (500/minute)
- System uses ~3-5 LLM calls per query
- ~2,880-4,800 customer queries per day
---

## ⚠️ Limitations

- **Response time:** 10-30 seconds (5-agent pipeline, not instant chat)
- **Single-user:** Not designed for concurrent users
- **English only:** No multilingual support
- **Local storage:** No cloud backup
- **No authentication:** Open access

---

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Visual diagrams & system flows
- **[PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md)** - Complete technical documentation
- **[ONE_PAGE_ARCHITECTURE.md](docs/ONE_PAGE_ARCHITECTURE.md)** - Single-page comprehensive overview

---

## 🎓 Key Concepts Demonstrated

✅ **Multi-Agent AI Orchestration** - 5 specialized agents with structured communication  
✅ **RAG Implementation** - Semantic search with vector embeddings  
✅ **Vector Databases** - ChromaDB with HNSW indexing  
✅ **LLM Integration** - Groq API with llama-3.3-70b-versatile  
✅ **Safety Controls** - Comprehensive guardrails (72 keywords cover 1000+ scenarios)  
✅ **Document Processing** - Multi-format support with error handling  
✅ **Clean Architecture** - Modular, testable, production-ready structure  

---

## 🐛 Troubleshooting

**Issue: "API key not found"**
```bash
# Verify .env file exists
ls -la .env

# Check key format
cat .env
# Should show: GROQ_API_KEY=gsk_...
```

**Issue: "Port 8501 already in use"**
```bash
# Kill existing process
pkill -f streamlit

# Or use different port
streamlit run app.py --server.port 8502
```

**Issue: Slow first run**
- First run downloads HuggingFace model (~120MB)
- Takes 2-5 minutes depending on internet speed
- Subsequent runs are fast

**Issue: No data loaded**
- Upload files via Admin section
- Wait for "✅ All files uploaded successfully!" message
- Refresh page if status doesn't update

---

## 👨‍💻 Author

**Edureka Capstone Project**  
Agentic AI - Multi-Agent Systems Course

Built with: Python, Streamlit, ChromaDB, HuggingFace, Groq LLM

---

## 📞 Support

For technical issues: learner.support@edureka.co
