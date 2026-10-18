import json

from mcp import Client

from src.graph.state import RTLState
from src.mcp.mcp_server import mcp


async def retrieve_guidelines_node(state: RTLState) -> dict:
    """
    Retrieve project RTL guidelines through the MCP server.

    Preserves the original query, k=3, and state output format.
    """
    user_spec = state.get("user_spec", "")

    if not isinstance(user_spec, str) or not user_spec.strip():
        raise ValueError(
            "Cannot retrieve RTL guidelines because user_spec is empty "
            "or invalid."
        )

    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.call_tool(
            "search_rtl_guidelines",
            {
                "query": user_spec.strip(),
                "k": 3,
            },
        )

        if result.is_error:
            error_text = "\n".join(
                block.text
                for block in result.content
                if hasattr(block, "text")
            )

            raise RuntimeError(
                "MCP guideline retrieval failed:\n"
                f"{error_text}"
            )

        retrieved_guidelines = []

        for block in result.content:
            if not hasattr(block, "text"):
                raise RuntimeError(
                    "MCP guideline retrieval returned an unexpected "
                    "non-text content block."
                )

            try:
                payload = json.loads(block.text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "MCP guideline retrieval returned invalid JSON."
                ) from exc

            # Support either one document per block or a JSON list.
            if isinstance(payload, dict):
                documents = [payload]
            elif isinstance(payload, list):
                documents = payload
            else:
                raise RuntimeError(
                    "MCP guideline content must be a document "
                    "dictionary or a list of document dictionaries."
                )

            for document in documents:
                if not isinstance(document, dict):
                    raise RuntimeError(
                        "MCP guideline document must be a dictionary."
                    )

                source = document.get("source")
                content = document.get("content")

                if not isinstance(source, str):
                    raise RuntimeError(
                        "MCP guideline document source must be a string."
                    )

                if not isinstance(content, str):
                    raise RuntimeError(
                        "MCP guideline document content must be a string."
                    )

                retrieved_guidelines.append(
                    {
                        "source": source,
                        "content": content,
                    }
                )

    if len(retrieved_guidelines) > 3:
        raise RuntimeError(
            "MCP guideline retrieval returned more documents "
            "than requested."
        )

    return {
        "retrieved_guidelines": retrieved_guidelines,
    }