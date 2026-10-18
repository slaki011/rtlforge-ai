import json
from pathlib import Path

from mcp import Client

from src.graph.state import RTLState
from src.mcp.mcp_server import mcp


async def yosys_synthesis_node(state: RTLState) -> dict:
    """
    Run Yosys synthesis through the in-process MCP server.

    Requires successful lint and a saved source matching rtl_code.
    Synthesis success is not proof of functional correctness.
    """
    lint_result = state.get("lint_result")

    if (
        state.get("status") != "lint_passed"
        or not isinstance(lint_result, dict)
        or lint_result.get("passed") is not True
        or type(lint_result.get("return_code")) is not int
        or lint_result["return_code"] != 0
    ):
        raise ValueError(
            "Cannot synthesize: a successful lint result is required."
        )

    rtl_file = state.get("rtl_file")

    if not isinstance(rtl_file, str) or not rtl_file.strip():
        raise ValueError(
            "Cannot synthesize: rtl_file is empty or invalid."
        )

    rtl_path = Path(rtl_file).resolve()

    if not rtl_path.is_file():
        raise FileNotFoundError(
            f"Cannot synthesize: RTL file does not exist: {rtl_path}"
        )

    rtl_code = state.get("rtl_code")

    if not isinstance(rtl_code, str) or not rtl_code.strip():
        raise ValueError(
            "Cannot synthesize: rtl_code is empty or invalid."
        )

    saved_code = rtl_path.read_text(encoding="utf-8")

    if saved_code.strip() != rtl_code.strip():
        raise ValueError(
            "Cannot synthesize: saved RTL differs from state rtl_code."
        )

    structured_spec = state.get("structured_spec")

    if not isinstance(structured_spec, dict):
        raise ValueError(
            "Cannot synthesize: structured_spec is missing or invalid."
        )

    module_name = structured_spec.get("module_name")

    if not isinstance(module_name, str) or not module_name.strip():
        raise ValueError(
            "Cannot synthesize: module_name is missing or invalid."
        )

    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.call_tool(
            "synthesize_systemverilog",
            {
                "rtl_file": str(rtl_path),
                "module_name": module_name,
            },
        )

        response_text = "\n".join(
            block.text
            for block in result.content
            if hasattr(block, "text")
        )

        if result.is_error:
            raise RuntimeError(
                "MCP synthesis tool execution failed:\n"
                f"{response_text}"
            )

        try:
            synthesis_result = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "MCP synthesis tool returned invalid JSON."
            ) from exc

    if not isinstance(synthesis_result, dict):
        raise RuntimeError(
            "MCP synthesis result must be a dictionary."
        )

    passed = synthesis_result.get("passed")

    if not isinstance(passed, bool):
        raise RuntimeError(
            "MCP synthesis result must contain a boolean 'passed'."
        )

    if synthesis_result.get("module_name") != module_name:
        raise RuntimeError(
            "MCP synthesis result contains an unexpected module name."
        )

    if passed:
        return_code = synthesis_result.get("return_code")

        if type(return_code) is not int or return_code != 0:
            raise RuntimeError(
                "Successful synthesis requires return_code=0."
            )

        netlist_file = synthesis_result.get("netlist_file")

        if (
            not isinstance(netlist_file, str)
            or not netlist_file.strip()
            or not Path(netlist_file).is_file()
        ):
            raise RuntimeError(
                "Successful synthesis did not provide an existing netlist."
            )

    return {
        "synthesis_result": synthesis_result,
        "status": (
            "synthesis_passed"
            if passed
            else "synthesis_failed"
        ),
    }