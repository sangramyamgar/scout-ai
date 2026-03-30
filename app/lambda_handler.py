"""AWS Lambda handler using Mangum to adapt FastAPI."""
import os
import shutil

# Copy ChromaDB to /tmp (Lambda's only writable directory) on cold start
LAMBDA_TASK_ROOT = os.environ.get("LAMBDA_TASK_ROOT", "/var/task")
SRC_CHROMA = os.path.join(LAMBDA_TASK_ROOT, "chroma_db")
DST_CHROMA = "/tmp/chroma_db"

if os.path.exists(SRC_CHROMA) and not os.path.exists(DST_CHROMA):
    print(f"📦 Copying ChromaDB from {SRC_CHROMA} to {DST_CHROMA}...")
    shutil.copytree(SRC_CHROMA, DST_CHROMA)
    print("✅ ChromaDB copied to writable /tmp")

# Set the environment variable BEFORE importing app (which loads config)
os.environ["CHROMA_PERSIST_DIRECTORY"] = DST_CHROMA

from mangum import Mangum
from app.main import app

# Mangum adapts FastAPI/ASGI for Lambda
handler = Mangum(app, lifespan="off")
