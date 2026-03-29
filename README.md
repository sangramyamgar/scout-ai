# FinSolve AI Assistant 🤖

A **production-grade RAG chatbot** with Role-Based Access Control (RBAC), Agentic AI workflows, and AWS deployment capabilities.

## 🎯 Features

- **RAG with RBAC**: Role-based access control ensures users only see authorized data
- **Agentic AI Pipeline**: LangGraph-powered workflow with query routing and citation validation
- **Hybrid Retrieval**: Combines semantic search (ChromaDB) with keyword search (BM25)
- **Cross-Encoder Re-ranking**: Improves retrieval precision using Sentence Transformers
- **Guardrails**: PII protection, prompt injection defense, and out-of-scope detection
- **Citation Enforcement**: Responses include source references; declines to answer without context
- **Free LLM Inference**: Uses Groq Cloud (Llama 3.3 70B) - no API costs
- **Evaluation Pipeline**: Ragas-based quality metrics with CI/CD integration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      STREAMLIT UI                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                          │
│   Authentication → RBAC Middleware → Rate Limiter           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH AGENTIC RAG PIPELINE                 │
│  Guardrails → Retrieval → Rerank → Citation → Generation   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ChromaDB            Groq Cloud           Sentence
 (Vector Store)      (Llama 3.3 70B)     Transformers
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd ds-rpc-01

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Groq API key
# Get a FREE key at: https://console.groq.com/keys
```

### 3. Initialize Vector Store

```bash
python scripts/init_vectorstore.py
```

### 4. Run the Server

```bash
# Start FastAPI backend
uvicorn app.main:app --reload

# In another terminal, start Streamlit frontend
streamlit run app/streamlit_app.py
```

### 5. Access the Application

- **API Docs**: http://localhost:8000/docs
- **Chat UI**: http://localhost:8501

## 👥 User Roles

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Engineering | Tony | password123 | Engineering docs + General |
| Finance | Sam | financepass | Financial reports + General |
| HR | Natasha | hrpass123 | HR data + General |
| Marketing | Bruce | securepass | Marketing reports + General |
| C-Level | Nick | director123 | **Full Access** |
| Employee | Happy | employee123 | General info only |

## 📁 Project Structure

```
ds-rpc-01/
├── app/
│   ├── main.py              # FastAPI application
│   ├── streamlit_app.py     # Streamlit UI
│   ├── core/
│   │   ├── config.py        # Settings & RBAC roles
│   │   ├── ingestion.py     # Document loading
│   │   ├── vectorstore.py   # ChromaDB integration
│   │   ├── retrieval.py     # Hybrid search (Vector + BM25)
│   │   ├── reranker.py      # Cross-encoder re-ranking
│   │   └── llm.py           # Groq LLM integration
│   ├── agents/
│   │   └── rag_pipeline.py  # LangGraph workflow
│   ├── guardrails/
│   │   └── safety.py        # PII & injection protection
│   └── evaluation/
│       └── eval_pipeline.py # Ragas evaluation
├── data/                    # Department documents
│   ├── engineering/
│   ├── finance/
│   ├── hr/
│   ├── marketing/
│   └── general/
├── scripts/
│   └── init_vectorstore.py  # Initialization script
├── tests/
├── pyproject.toml
├── .env.example
└── aws_guide.md             # AWS deployment guide
```

## 🔧 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/login` | GET | Yes | Validate credentials |
| `/chat` | POST | Yes | Send chat message |
| `/usage` | GET | Yes | Get usage stats |
| `/roles` | GET | No | List available roles |
| `/collections` | GET | Yes | Vector store stats |

## 📊 Evaluation

Run the evaluation pipeline to measure RAG quality:

```bash
python -m app.evaluation.eval_pipeline
```

Metrics:
- **Faithfulness**: Are responses grounded in context?
- **Answer Relevancy**: Do responses answer the question?
- **Context Recall**: Does retrieval find relevant info?

## 💰 Budget: $0

All components use free tiers:
- **Groq Cloud**: Free LLM inference (Llama 3.3 70B)
- **ChromaDB**: Local vector storage
- **HuggingFace**: Local embeddings & reranker
- **AWS Free Tier**: See [aws_guide.md](aws_guide.md)

## 📚 Resources

- [Groq Console](https://console.groq.com/) - Get free API key
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Ragas Docs](https://docs.ragas.io/)

## 🚧 AWS Deployment

See **[aws_guide.md](aws_guide.md)** for detailed step-by-step AWS deployment instructions.

---

Built for the [Codebasics Resume Project Challenge](https://codebasics.io/challenge/codebasics-gen-ai-data-science-resume-project-challenge)
