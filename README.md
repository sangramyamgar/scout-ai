# Scout AI 🔍

**Enterprise Knowledge Assistant** with Role-Based Access Control

A production-grade RAG (Retrieval-Augmented Generation) chatbot that provides secure, role-based access to enterprise knowledge using LangChain, LangGraph, and modern AI infrastructure.

![Scout AI](https://img.shields.io/badge/AI-LangChain-blue) ![Python](https://img.shields.io/badge/Python-3.11-green) ![React](https://img.shields.io/badge/Frontend-React-61dafb) ![AWS](https://img.shields.io/badge/Cloud-AWS-orange) ![License](https://img.shields.io/badge/License-MIT-yellow)

**Live Demo:** [scout.yamgar.com](https://scout.yamgar.com)

---

## Features

- **Role-Based Access Control (RBAC)** - Secure access based on user roles (Finance, HR, Engineering, Marketing, Executive)
- **Agentic RAG Pipeline** - LangGraph-powered intelligent retrieval with 6-node workflow
- **Multi-Department Support** - Isolated document collections per department
- **PII Detection** - Built-in guardrails for sensitive information
- **Modern UI** - React + Tailwind with dark mode support
- **Inline Citations** - Expandable sources with document references
- **Serverless Architecture** - AWS Lambda + API Gateway + Bedrock
- **Cost-Optimized** - ~$1-3/month for demo usage

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              SCOUT AI ARCHITECTURE                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────────┐
│  Cloudflare     │     │  AWS API        │     │  AWS Lambda (Container)     │
│  Pages          │────▶│  Gateway        │────▶│                             │
│  (React UI)     │     │  (HTTP API)     │     │  ┌─────────────────────┐    │
└─────────────────┘     └─────────────────┘     │  │  FastAPI + Mangum   │    │
                                                │  └──────────┬──────────┘    │
                                                │             │               │
                                                │  ┌──────────▼──────────┐    │
                                                │  │  LangGraph Pipeline │    │
                                                │  │  (6-Node RAG)       │    │
                                                │  └──────────┬──────────┘    │
                                                │             │               │
                                                │  ┌─────┬────┴────┬─────┐   │
                                                │  │     │         │     │   │
                                                └──┼─────┼─────────┼─────┼───┘
                                                   ▼     ▼         ▼     ▼
                                             ┌─────────┐ ┌───────┐ ┌─────────┐
                                             │ChromaDB │ │Bedrock│ │  Groq   │
                                             │(Vectors)│ │(Embed)│ │ (LLM)   │
                                             └─────────┘ └───────┘ └─────────┘
```

### LangGraph RAG Pipeline

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│   Input    │───▶│   Route    │───▶│  Retrieve  │───▶│  Rerank    │───▶│  Generate  │───▶│   Output   │
│ Guardrails │    │   Query    │    │   (RBAC)   │    │  Results   │    │  Response  │    │ Guardrails │
└────────────┘    └────────────┘    └────────────┘    └────────────┘    └────────────┘    └────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Local Development

```bash
# Clone repository
git clone https://github.com/sangramyamgar/scout-ai.git
cd scout-ai

# Backend setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# Create .env file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Initialize vector store
python scripts/init_vectorstore.py

# Start backend
uvicorn app.main:app --reload --port 8000
```

```bash
# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173

---

## Demo Accounts

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Finance | sarah.mitchell@scout.ai | finance2024 | Finance + General |
| Marketing | james.chen@scout.ai | marketing2024 | Marketing + General |
| HR | priya.sharma@scout.ai | hr2024 | HR + General |
| Engineering | alex.torres@scout.ai | eng2024 | Engineering + General |
| Executive | michael.ross@scout.ai | exec2024 | **All Departments** |
| Employee | emma.wilson@scout.ai | employee2024 | General Only |

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async API framework |
| **LangChain** | LLM application framework |
| **LangGraph** | Agentic workflow orchestration |
| **ChromaDB** | Vector database for embeddings |
| **AWS Bedrock** | Titan embeddings (production) |
| **Mangum** | AWS Lambda adapter for ASGI |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI component library |
| **Tailwind CSS** | Utility-first styling |
| **Vite** | Fast build tool |
| **Lucide React** | Icon library |

### AI/ML
| Model | Provider | Purpose |
|-------|----------|---------|
| **Llama 3.3 70B** | Groq | LLM inference |
| **Titan Embed Text v1** | AWS Bedrock | Document embeddings |
| **Keyword Reranker** | Custom | Result reranking |

### Infrastructure
| Service | Purpose |
|---------|---------|
| **AWS Lambda** | Serverless compute (container) |
| **AWS API Gateway** | HTTP API endpoint |
| **AWS ECR** | Docker image registry |
| **AWS Bedrock** | Managed embeddings |
| **Cloudflare Pages** | Frontend hosting |

---

## Project Structure

```
scout-ai/
├── app/
│   ├── agents/
│   │   └── rag_pipeline.py    # LangGraph 6-node RAG pipeline
│   ├── core/
│   │   ├── config.py          # Settings & role definitions
│   │   ├── llm.py             # Groq LLM service
│   │   ├── vectorstore.py     # ChromaDB + Bedrock embeddings
│   │   └── reranker_llm.py    # Lightweight keyword reranker
│   ├── guardrails/
│   │   └── safety.py          # PII detection & input validation
│   ├── lambda_handler.py      # AWS Lambda entry point
│   └── main.py                # FastAPI application
├── data/
│   ├── engineering/           # Technical documentation
│   ├── finance/               # Financial reports
│   ├── general/               # Employee handbook
│   ├── hr/                    # HR policies & data
│   └── marketing/             # Marketing reports
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   └── App.jsx            # Main app with routing
│   └── .env.production        # Production API URL
├── scripts/
│   └── init_vectorstore.py    # Initialize vector database
├── tests/                     # Test suite
├── Dockerfile                 # Lambda container image
├── requirements-lambda.txt    # Production dependencies
└── pyproject.toml             # Project configuration
```

---

## Deployment

### AWS Lambda (Backend)

```bash
# Build container
docker build --platform linux/amd64 -t scout-ai .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag scout-ai:latest <account>.dkr.ecr.us-east-1.amazonaws.com/scout-ai:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/scout-ai:latest

# Update Lambda
aws lambda update-function-code --function-name scout-ai-backend --image-uri <ecr-uri>:latest
```

### Cloudflare Pages (Frontend)

```bash
cd frontend
npm run build
npx wrangler pages deploy dist --project-name=scout-ai
```

---

## Cost Estimate (Monthly)

| Service | Cost |
|---------|------|
| AWS Lambda | ~$0-2 (1M free requests/month) |
| API Gateway | ~$0-1 (1M free requests/month) |
| Bedrock Embeddings | ~$0.50 |
| ECR Storage | ~$0.10 (363MB image) |
| Cloudflare Pages | **Free** |
| **Total** | **~$1-3/month** |

---

## Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_...              # Groq API key

# Optional
ENVIRONMENT=production            # development | production
LANGCHAIN_TRACING_V2=false       # Enable LangSmith tracing
LANGCHAIN_API_KEY=               # LangSmith API key
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/login` | Basic | Validate credentials |
| POST | `/chat` | Basic | Chat with RAG pipeline |
| GET | `/usage` | Basic | User's API usage stats |
| GET | `/roles` | No | List available roles |
| GET | `/collections` | Basic | Vector store stats |

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [LangChain](https://langchain.com) for the LLM framework
- [Groq](https://groq.com) for fast LLM inference
- [AWS](https://aws.amazon.com) for serverless infrastructure
- [Cloudflare](https://cloudflare.com) for frontend hosting
