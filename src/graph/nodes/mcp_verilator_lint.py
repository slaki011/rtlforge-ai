import json

from mcp import Client

from src.graph.state import RTLState
from src.mcp.mcp_server import mcp


async def mcp_verilator_lint_node(state: RTLState) -> dict:
    """
    Call the Verilator lint MCP tool and return a state update.

    Uses an in-process MCP client.
    A lint pass is not proof of functional correctness.
    """
    rtl_file = state.get("rtl_file", "").strip()

    if not rtl_file:
        raise ValueError(
            "Cannot run MCP lint because rtl_file is empty."
        )

    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.call_tool(
            "lint_systemverilog",
            {"rtl_file": rtl_file},
        )

        response_text = "\n".join(
            block.text
            for block in result.content
            if hasattr(block, "text")
        )

        if result.is_error:
            raise RuntimeError(
                "MCP lint tool execution failed:\n"
                f"{response_text}"
            )

        try:
            lint_result = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "MCP lint tool returned invalid JSON."
            ) from exc

    if not isinstance(lint_result, dict):
        raise RuntimeError(
            "MCP lint result must be a dictionary."
        )

    passed = lint_result.get("passed")
    return_code = lint_result.get("return_code")

    if not isinstance(passed, bool):
        raise RuntimeError(
            "MCP lint result must contain a boolean 'passed'."
        )

    if type(return_code) is not int:
        raise RuntimeError(
            "MCP lint result must contain an integer 'return_code'."
        )

    if passed != (return_code == 0):
        raise RuntimeError(
            "MCP lint result has inconsistent passed/return_code values."
        )

    return {
        "lint_result": lint_result,
        "status": "lint_passed" if passed else "lint_failed",
    }