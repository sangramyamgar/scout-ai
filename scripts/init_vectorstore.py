#!/usr/bin/env python3
"""
Initialize the vector store with department documents.
Run this before starting the server.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Initialize vector store with all department documents."""
    print("=" * 60)
    print("Scout - Vector Store Initialization")
    print("=" * 60)

    # Check for required environment variables
    from app.core.config import get_settings

    settings = get_settings()

    if not settings.groq_api_key:
        print("\n⚠️  WARNING: GROQ_API_KEY not set!")
        print("   The chatbot won't work without it.")
        print("   Get a free key at: https://console.groq.com/keys")
        print("   Then add it to your .env file")
        print()

    # Initialize vector store
    print("\n📚 Loading documents and creating embeddings...")
    print("   (This may take a minute on first run)\n")

    from app.core.vectorstore import initialize_vector_store

    data_dir = project_root / "data"

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        print("   Make sure the 'data' folder exists with department subfolders")
        sys.exit(1)

    store = initialize_vector_store(str(data_dir))

    # Print stats
    print("\n" + "=" * 60)
    print("📊 Collection Statistics:")
    print("=" * 60)

    stats = store.get_collection_stats()
    total_docs = 0
    for name, info in stats.items():
        count = info["count"]
        total_docs += count
        print(f"   {name}: {count} chunks")

    print(f"\n   Total: {total_docs} chunks indexed")
    print("=" * 60)

    # Build BM25 indices for hybrid search
    print("\n🔧 Building BM25 indices for hybrid search...")

    from app.core.ingestion import load_all_departments
    from app.core.retrieval import get_hybrid_retriever

    all_docs = load_all_departments(str(data_dir))
    retriever = get_hybrid_retriever()

    for dept, docs in all_docs.items():
        retriever.index_documents_for_bm25(dept, docs)
        print(f"   ✓ {dept}: {len(docs)} documents indexed")

    print("\n✅ Initialization complete!")
    print("\n🚀 You can now start the server with:")
    print("   uvicorn app.main:app --reload")
    print("\n📖 API docs will be available at:")
    print("   http://localhost:8000/docs")


if __name__ == "__main__":
    main()
