import asyncio

from mcp import Client

from src.mcp.mcp_server import mcp


def extract_text(result) -> str:
    return "\n".join(
        block.text
        for block in result.content
        if hasattr(block, "text")
    )


async def main() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        print("MCP CONNECTION OK")

        invalid_result = await client.call_tool(
            "search_rtl_guidelines",
            {
                "query": "",
                "k": 3,
            },
        )

        if not invalid_result.is_error:
            raise AssertionError(
                "Expected an error for an empty guideline query."
            )

        error_text = extract_text(invalid_result)

        expected_message = (
            "Guideline search query must not be empty."
        )

        if expected_message not in error_text:
            raise AssertionError(
                "The tool returned an unexpected error:\n"
                f"{error_text}"
            )

        print("EMPTY QUERY VALIDATION OK")

        retrieval_result = await client.call_tool(
            "search_rtl_guidelines",
            {
                "query": (
                    "SystemVerilog sequential logic coding guidelines "
                    "for clocked registers and reset handling"
                ),
                "k": 2,
            },
        )

        retrieval_text = extract_text(retrieval_result)

        if retrieval_result.is_error:
            raise AssertionError(
                "RAG tool call failed:\n"
                f"{retrieval_text}"
            )

        if not retrieval_result.content:
            raise AssertionError(
                "RAG tool returned no content blocks."
            )

        print("RAG TOOL CALL OK")
        print("\n--- RETRIEVAL RESPONSE ---")
        print(retrieval_text)
        print("--- END RESPONSE ---")
        print("\nMCP SMOKE TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())