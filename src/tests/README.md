# Test Suite

All test files have been organized in `src/tests/` directory.

## Running Tests

From the project root directory:

```bash
# Run all tests
python -m pytest src/tests/

# Run specific test file
python src/tests/test_guardrails.py
python src/tests/test_off_topic.py
python src/tests/test_ingestion_pipeline.py
python src/tests/test_rag_llm.py
python src/tests/test_agent_orchestration.py

# Run with verbose output
python -m pytest src/tests/ -v
```

## Test Files

### Guardrails Tests

1. **test_guardrails.py** - Basic guardrail functionality
   - Normal customer complaints
   - Jailbreak attempts
   - Off-topic requests
   - Policy questions

2. **test_off_topic.py** - Category-based off-topic blocking
   - Medical questions (blocks advice, allows product returns)
   - Legal/Financial questions
   - Educational requests
   - Entertainment requests
   - Competitor comparisons
   - Valid support requests (order/return/policy)

### Core System Tests

3. **test_ingestion_pipeline.py** - Data ingestion system
   - Document loading (TXT, PDF, CSV, XLSX)
   - Text chunking
   - Embedding generation
   - Vector store operations
   - Complete pipeline integration

4. **test_rag_llm.py** - RAG and LLM integration
   - LLM factory and provider detection
   - LLM client initialization
   - RAG chain operations
   - Policy retrieval and generation
   - Multi-provider support (Groq, OpenAI, Anthropic)

5. **test_agent_orchestration.py** - Multi-agent system
   - Individual agent testing (5 agents)
   - Agent orchestration flow
   - Customer profiling
   - Complaint analysis
   - Policy research
   - Resolution arbitration
   - Response validation

### Integration Tests

6. **test_crewai.py** - CrewAI integration tests
   - CrewAI framework integration

## Test Categories

### Guardrails Tests
Test that the system properly blocks:
- ✅ Jailbreak attempts ("ignore previous instructions")
- ✅ Medical advice requests ("which medicine for headache")
- ✅ Legal advice requests ("can I sue you")
- ✅ Financial advice requests ("should I buy stocks")
- ✅ Educational/homework help ("teach me Python")
- ✅ Entertainment requests ("tell me a joke")
- ✅ Competitor comparisons ("is Amazon better")
- ✅ Off-topic general questions ("what's the weather")

And allows:
- ✅ Order inquiries ("where is my order")
- ✅ Return/refund requests ("I want to return my product")
- ✅ Policy questions ("what is your refund policy")
- ✅ Product support ("my blood pressure monitor warranty")

### Ingestion Pipeline Tests
- Document loading from multiple formats
- Text chunking with overlap
- Embedding generation
- Vector store persistence
- End-to-end pipeline

### RAG & LLM Tests
- Provider auto-detection
- LLM client initialization
- RAG retrieval accuracy
- Response generation quality
- Multi-provider compatibility

### Agent Orchestration Tests
- 5-agent pipeline execution
- Inter-agent communication
- Context preservation
- Resolution quality
- Follow-up support

## Quick Test Commands

```bash
cd /Users/I531807/Documents/Edureka/customer-support-project

# Test guardrails (category-based blocking)
python src/tests/test_off_topic.py

# Test ingestion pipeline
python src/tests/test_ingestion_pipeline.py

# Test RAG and LLM
python src/tests/test_rag_llm.py

# Test agent orchestration
python src/tests/test_agent_orchestration.py
```

## Expected Results

### test_off_topic.py
- **Expected**: 14/14 tests pass
- **Tests**: Medical, legal, financial, educational, entertainment blocking + valid support requests

### test_ingestion_pipeline.py
- **Expected**: All modules import successfully, pipeline processes documents

### test_rag_llm.py
- **Expected**: Provider detected, RAG chain generates responses

### test_agent_orchestration.py
- **Expected**: 5 agents execute successfully, orchestrator produces resolution
