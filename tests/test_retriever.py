from src.rag.retriever import retrieve_guidelines


def main() -> None:
    query = """
    I need to design a synchronous RTL block with registers,
    sequential logic, and an active-low reset.
    What coding guidelines should I follow?
    """

    print("=" * 70)
    print("RTLForge AI - RAG Retrieval Test")
    print("=" * 70)

    print("\nQuery:")
    print(query.strip())

    documents = retrieve_guidelines(
        query=query,
        k=3,
    )

    print(f"\nRetrieved {len(documents)} document(s).")

    if not documents:
        print("\nNo guidelines were retrieved.")
        return

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown")

        print("\n" + "-" * 70)
        print(f"RESULT {index}")
        print(f"Source: {source}")
        print("-" * 70)
        print(document.page_content.strip())

    print("\n" + "=" * 70)
    print("Retrieval test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()