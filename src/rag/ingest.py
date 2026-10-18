import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


PROJECT_ROOT = Path(__file__).resolve().parents[2]
print(f"Project root: {PROJECT_ROOT}")
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
CHROMA_DIR = PROJECT_ROOT / ".chroma_db"

COLLECTION_NAME = "rtl_guidelines"
EMBEDDING_MODEL = "text-embedding-3-small"


def load_documents() -> list[Document]:
    if not KNOWLEDGE_DIR.is_dir():
        raise FileNotFoundError(
            f"Knowledge folder not found: {KNOWLEDGE_DIR}"
        )

    documents = []

    for file in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = file.read_text(encoding="utf-8").strip()

        if not content:
            print(f"Skipping empty file: {file.name}")
            continue

        documents.append(
            Document(
                page_content=content,
                metadata={"source": file.name},
            )
        )

    if not documents:
        raise ValueError(
            f"No non-empty Markdown files found in {KNOWLEDGE_DIR}"
        )

    return documents


def build_vector_store() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Check your .env file."
        )

    documents = load_documents()

    print(f"Loaded {len(documents)} documents.")

    for document in documents:
        print(f"  - {document.metadata['source']}")

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    # Rebuild this project's collection from the current files.
    # Other collections in the database are not deleted.
    vector_store.reset_collection()

    vector_store.add_documents(
        documents=documents,
        ids=[doc.metadata["source"] for doc in documents],
    )

    print("\nKnowledge base indexed.")
    print(f"Database location: {CHROMA_DIR}")


if __name__ == "__main__":
    build_vector_store()
