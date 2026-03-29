#!/bin/bash
# FinSolve AI Assistant - Quick Start Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 FinSolve AI Assistant - Quick Start${NC}"
echo "========================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env and add your GROQ_API_KEY${NC}"
        echo "   Get a free key at: https://console.groq.com/keys"
    else
        echo -e "${RED}Error: No .env or .env.example found${NC}"
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q uvicorn fastapi python-dotenv streamlit \
    langchain langchain-core langchain-groq langchain-chroma \
    langchain-huggingface langchain-community langgraph \
    chromadb sentence-transformers rank-bm25 pydantic-settings httpx

# Initialize vector store if needed
if [ ! -d "data/chroma_db" ]; then
    echo -e "${YELLOW}Initializing vector store...${NC}"
    python scripts/init_vectorstore.py
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}Starting FastAPI backend on http://localhost:8000${NC}"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Streamlit frontend
echo -e "${GREEN}Starting Streamlit UI on http://localhost:8501${NC}"
streamlit run app/streamlit_app.py --server.port 8501 &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}========================================"
echo "✅ FinSolve AI Assistant is running!"
echo "========================================"
echo ""
echo "🔗 API Backend:  http://localhost:8000"
echo "🔗 API Docs:     http://localhost:8000/docs"
echo "🔗 Streamlit UI: http://localhost:8501"
echo ""
echo "📋 Demo Users:"
echo "   Finance:     Sam / financepass"
echo "   Marketing:   Bruce / securepass"
echo "   HR:          Natasha / hrpass123"
echo "   Engineering: Tony / password123"
echo "   C-Level:     Nick / director123"
echo "   Employee:    Happy / employee123"
echo ""
echo -e "Press Ctrl+C to stop all servers${NC}"

# Wait for background processes
wait
