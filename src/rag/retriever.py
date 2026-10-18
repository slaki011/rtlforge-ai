from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_DIR = PROJECT_ROOT / ".chroma_db"

COLLECTION_NAME = "rtl_guidelines"
EMBEDDING_MODEL = "text-embedding-3-small"


load_dotenv(PROJECT_ROOT / ".env")


def get_vector_store() -> Chroma:
    """
    Connect to the existing local Chroma vector store.

    This does not ingest or reset any documents.
    It only opens the collection created by ingest.py.
    """

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    return vector_store


def retrieve_guidelines(
    query: str,
    k: int = 3,
) -> list[Document]:
    """
    Retrieve the most relevant RTL guidelines for the given query.

    Args:
        query:
            Natural-language description of the RTL topic or design problem.

        k:
            Maximum number of documents to retrieve.

    Returns:
        List of LangChain Document objects ordered by similarity.
    """

    if not query.strip():
        raise ValueError("Retrieval query must not be empty.")

    vector_store = get_vector_store()

    documents = vector_store.similarity_search(
        query=query,
        k=k,
    )

    return documents