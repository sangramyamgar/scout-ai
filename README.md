# Scout AI 🧭

**Enterprise Knowledge Assistant** — A production-grade RAG chatbot with Role-Based Access Control (RBAC), Agentic AI workflows, and cloud deployment.

![Scout AI](https://img.shields.io/badge/Scout-AI-0ea5e9?style=for-the-badge)
![AWS](https://img.shields.io/badge/AWS-Ready-FF9900?style=for-the-badge)
![LangChain](https://img.shields.io/badge/LangChain-Powered-1a1a1a?style=for-the-badge)

## 🎯 Features

- **🔐 Role-Based Access Control**: Secure, department-specific data access
- **🤖 Agentic AI Pipeline**: LangGraph-powered workflow with query routing and citation validation
- **🔍 Hybrid Retrieval**: Combines semantic search (ChromaDB) with keyword search (BM25)
- **📊 Cross-Encoder Re-ranking**: Improves retrieval precision using Sentence Transformers
- **🛡️ Guardrails**: PII protection, prompt injection defense, and out-of-scope detection
- **📝 Citation Enforcement**: Responses include source references; declines to answer without context
- **💸 Free LLM Inference**: Uses Groq Cloud (Llama 3.3 70B) - no API costs
- **📈 Evaluation Pipeline**: Ragas-based quality metrics with CI/CD integration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              REACT FRONTEND (Cloudflare Pages)              │
│                    Modern, Professional UI                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                FASTAPI BACKEND (AWS / Local)                │
│       Authentication → RBAC Middleware → Rate Limiter       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH AGENTIC RAG PIPELINE                 │
│    Guardrails → Retrieval → Rerank → Citation → Generate    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ChromaDB            Groq Cloud           Sentence
 (Vector Store)      (Llama 3.3 70B)     Transformers
```

## 🚀 Quick Start

### Option 1: One-Click Start

```bash
./run.sh
```

### Option 2: Manual Setup

```bash
# Clone and setup
git clone <your-repo-url>
cd ds-rpc-01

# Backend setup
python -m venv venv
source venv/bin/activate
pip install -e .

# Configure API keys
cp .env.example .env
# Edit .env and add GROQ_API_KEY from https://console.groq.com/keys

# Initialize vector store
python scripts/init_vectorstore.py

# Start backend
uvicorn app.main:app --port 8000
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev  # Development server at http://localhost:3000
```

### Access Points

- **React UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Legacy Streamlit UI**: http://localhost:8501 (run `streamlit run app/streamlit_app.py`)

## 👥 Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| **Executive** | michael.ross@finsolve.com | exec2024 |
| **Finance** | sarah.mitchell@finsolve.com | finance2024 |
| **Marketing** | james.chen@finsolve.com | marketing2024 |
| **HR** | priya.sharma@finsolve.com | hr2024 |
| **Engineering** | alex.torres@finsolve.com | eng2024 |
| **Employee** | emma.wilson@finsolve.com | employee2024 |

## 📁 Project Structure

```
ds-rpc-01/
├── app/
│   ├── main.py              # FastAPI application
│   ├── streamlit_app.py     # Legacy Streamlit UI
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
├── frontend/                # React + Tailwind UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginPage.jsx
│   │   │   └── ChatPage.jsx
│   │   └── App.jsx
│   └── package.json
├── data/                    # Department documents
├── scripts/
├── tests/
├── aws_guide.md             # AWS deployment guide
└── README.md
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

## ☁️ Deployment

### Frontend → Cloudflare Pages (Free)

1. Push to GitHub
2. Connect repo to Cloudflare Pages
3. Build command: `cd frontend && npm run build`
4. Output directory: `frontend/dist`
5. Set `VITE_API_URL` environment variable to your backend URL

### Backend → AWS (Free Tier)

See **[aws_guide.md](aws_guide.md)** for detailed step-by-step instructions:
- Lambda + API Gateway (serverless)
- ECS Fargate (containers)
- Budget alerts and cost protection

## 💰 Budget: Under $10

| Service | Cost |
|---------|------|
| Groq Cloud (LLM) | **Free** (100K tokens/day) |
| ChromaDB | **Free** (local storage) |
| HuggingFace Models | **Free** (local inference) |
| Cloudflare Pages | **Free** (unlimited requests) |
| AWS Free Tier | **Free** (12 months) |

## 📊 Evaluation

```bash
python -m app.evaluation.eval_pipeline
```

Metrics: Faithfulness, Answer Relevancy, Context Recall

## 📚 Resources

- [Groq Console](https://console.groq.com/) - Get free API key
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Ragas Docs](https://docs.ragas.io/)

---

Built for the [Codebasics Resume Project Challenge](https://codebasics.io/challenge/codebasics-gen-ai-data-science-resume-project-challenge)
