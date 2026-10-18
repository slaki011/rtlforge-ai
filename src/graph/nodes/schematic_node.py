import json
from pathlib import Path

from mcp import Client

from src.graph.state import RTLState
from src.mcp.mcp_server import mcp


async def schematic_node(state: RTLState) -> dict:
    """
    Render an SVG schematic through the in-process MCP server.

    Requires a successful synthesis result and an existing
    Yosys JSON netlist.

    A rendered schematic is not proof of functional correctness.
    """
    if state.get("status") != "synthesis_passed":
        raise ValueError(
            "Cannot render schematic: "
            "status must be 'synthesis_passed'."
        )

    synthesis_result = state.get("synthesis_result")

    if not isinstance(synthesis_result, dict):
        raise ValueError(
            "Cannot render schematic: "
            "synthesis_result is missing or invalid."
        )

    if synthesis_result.get("passed") is not True:
        raise ValueError(
            "Cannot render schematic: "
            "synthesis_result did not pass."
        )

    return_code = synthesis_result.get("return_code")

    if type(return_code) is not int or return_code != 0:
        raise ValueError(
            "Cannot render schematic: "
            "successful synthesis requires return_code=0."
        )

    netlist_file = synthesis_result.get("netlist_file")

    if (
        not isinstance(netlist_file, str)
        or not netlist_file.strip()
    ):
        raise ValueError(
            "Cannot render schematic: "
            "netlist_file is missing or invalid."
        )

    netlist_path = Path(netlist_file).resolve()

    if not netlist_path.is_file():
        raise FileNotFoundError(
            "Cannot render schematic: "
            f"netlist does not exist: {netlist_path}"
        )

    structured_spec = state.get("structured_spec")

    if not isinstance(structured_spec, dict):
        raise ValueError(
            "Cannot render schematic: "
            "structured_spec is missing or invalid."
        )

    module_name = structured_spec.get("module_name")

    if (
        not isinstance(module_name, str)
        or not module_name.strip()
    ):
        raise ValueError(
            "Cannot render schematic: "
            "module_name is missing or invalid."
        )

    synthesis_module_name = synthesis_result.get(
        "module_name"
    )

    if synthesis_module_name != module_name:
        raise ValueError(
            "Cannot render schematic: module name in "
            "synthesis_result does not match structured_spec."
        )

    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.call_tool(
            "render_netlist_schematic",
            {
                "netlist_file": str(netlist_path),
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
                "MCP schematic tool execution failed:\n"
                f"{response_text}"
            )

        try:
            schematic_result = json.loads(
                response_text
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "MCP schematic tool returned invalid JSON."
            ) from exc

    if not isinstance(schematic_result, dict):
        raise RuntimeError(
            "MCP schematic result must be a dictionary."
        )

    if schematic_result.get("passed") is not True:
        raise RuntimeError(
            "MCP schematic renderer returned passed=False."
        )

    if schematic_result.get("module_name") != module_name:
        raise RuntimeError(
            "MCP schematic result contains an unexpected "
            "module name."
        )

    result_netlist = schematic_result.get(
        "netlist_file"
    )

    if (
        not isinstance(result_netlist, str)
        or Path(result_netlist).resolve() != netlist_path
    ):
        raise RuntimeError(
            "MCP schematic result references an unexpected "
            "netlist file."
        )

    svg_file = schematic_result.get("svg_file")
    dot_file = schematic_result.get("dot_file")

    if (
        not isinstance(svg_file, str)
        or not Path(svg_file).is_file()
    ):
        raise RuntimeError(
            "MCP schematic result does not contain an "
            "existing SVG file."
        )

    if (
        not isinstance(dot_file, str)
        or not Path(dot_file).is_file()
    ):
        raise RuntimeError(
            "MCP schematic result does not contain an "
            "existing DOT file."
        )

    return {
        "schematic_result": schematic_result,
        "status": "schematic_generated",
    }