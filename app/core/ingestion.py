"""
Document ingestion and chunking pipeline using LangChain.
Loads department documents, chunks them, and prepares for vector store.
"""

from pathlib import Path
from typing import List, Dict

from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.config import get_settings

settings = get_settings()

# Department to folder mapping
DEPARTMENT_FOLDERS = {
    "engineering": "engineering",
    "finance": "finance",
    "hr": "hr",
    "marketing": "marketing",
    "general": "general",
}


class DocumentIngestionPipeline:
    """
    LangChain-based document ingestion pipeline.
    Handles loading, parsing, and chunking documents from various sources.
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            chunk_size: Size of text chunks (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            is_separator_regex=False,
        )

    def load_markdown_file(self, file_path: Path, department: str) -> List[Document]:
        """Load a markdown file using LangChain loader."""
        try:
            # Use simple text loader for markdown files
            loader = TextLoader(str(file_path), encoding="utf-8")
            docs = loader.load()
        except Exception as e:
            print(f"  ⚠ Error loading {file_path}: {e}")
            return []

        # Add department metadata
        for doc in docs:
            doc.metadata.update({
                "department": department,
                "filename": file_path.name,
                "file_type": ".md",
            })

        return docs

    def load_csv_file(self, file_path: Path, department: str) -> List[Document]:
        """
        Load CSV file using LangChain CSVLoader.
        Each row becomes a separate document for better retrieval.
        """
        try:
            loader = CSVLoader(
                file_path=str(file_path),
                encoding="utf-8",
            )
            docs = loader.load()

            # Add department metadata to each row document
            for doc in docs:
                doc.metadata.update({
                    "department": department,
                    "filename": file_path.name,
                    "file_type": ".csv",
                })

            return docs
        except Exception as e:
            print(f"  ⚠ Error loading CSV {file_path}: {e}")
            return []

    def load_department(self, department: str, data_dir: str = "data") -> List[Document]:
        """
        Load all documents for a specific department.

        Args:
            department: Department name
            data_dir: Base data directory

        Returns:
            List of LangChain Document objects
        """
        folder_name = DEPARTMENT_FOLDERS.get(department)
        if not folder_name:
            raise ValueError(f"Unknown department: {department}")

        dept_path = Path(data_dir) / folder_name
        if not dept_path.exists():
            raise FileNotFoundError(f"Department folder not found: {dept_path}")

        documents = []

        for file_path in dept_path.iterdir():
            if not file_path.is_file():
                continue

            if file_path.suffix == ".md":
                docs = self.load_markdown_file(file_path, department)
                documents.extend(docs)
            elif file_path.suffix == ".csv":
                docs = self.load_csv_file(file_path, department)
                documents.extend(docs)
            # Skip other file types

        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks using LangChain text splitter.

        Args:
            documents: List of documents to chunk

        Returns:
            List of chunked documents with preserved metadata
        """
        chunked_docs = self.text_splitter.split_documents(documents)

        # Add chunk index to metadata
        for i, doc in enumerate(chunked_docs):
            doc.metadata["chunk_index"] = i

        return chunked_docs

    def process_department(self, department: str, data_dir: str = "data") -> List[Document]:
        """
        Load and chunk all documents for a department.

        Args:
            department: Department name
            data_dir: Base data directory

        Returns:
            List of chunked documents ready for embedding
        """
        docs = self.load_department(department, data_dir)
        return self.chunk_documents(docs)

    def process_all_departments(self, data_dir: str = "data") -> Dict[str, List[Document]]:
        """
        Process all departments and return chunked documents.

        Returns:
            Dictionary mapping department names to lists of chunked documents
        """
        all_docs = {}

        for department in DEPARTMENT_FOLDERS.keys():
            try:
                chunked = self.process_department(department, data_dir)
                all_docs[department] = chunked
                print(f"  ✓ {department}: {len(chunked)} chunks")
            except FileNotFoundError as e:
                print(f"  ⚠ Skipping {department}: {e}")

        return all_docs


# Convenience functions for backwards compatibility
def load_department_documents(department: str, data_dir: str = "data") -> List[Document]:
    """Load documents for a department (convenience function)."""
    pipeline = DocumentIngestionPipeline()
    return pipeline.load_department(department, data_dir)


def chunk_documents(
    documents: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Document]:
    """Chunk documents (convenience function)."""
    pipeline = DocumentIngestionPipeline(chunk_size, chunk_overlap)
    return pipeline.chunk_documents(documents)


def load_all_departments(data_dir: str = "data") -> Dict[str, List[Document]]:
    """Load and chunk all departments (convenience function)."""
    pipeline = DocumentIngestionPipeline()
    return pipeline.process_all_departments(data_dir)


if __name__ == "__main__":
    print("📚 Testing Document Ingestion Pipeline")
    print("=" * 50)

    pipeline = DocumentIngestionPipeline()
    docs = pipeline.process_all_departments()

    print("\n📊 Summary:")
    total = 0
    for dept, chunks in docs.items():
        total += len(chunks)
        print(f"  {dept}: {len(chunks)} chunks")
    print(f"\n  Total: {total} chunks")
