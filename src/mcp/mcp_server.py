from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from src.graph.nodes.verilator_lint import run_verilator_lint
from src.graph.nodes.yosys_synthesis import run_yosys_synthesis
from src.rag.retriever import retrieve_guidelines
from src.render_schematic import render_schematic


mcp = MCPServer("RTLForge AI")


@mcp.tool()
def search_rtl_guidelines(
    query: str,
    k: int = 3,
) -> list[dict]:
    """
    Search the RTLForge project RTL coding guidelines.

    Returns retrieved document content and source filenames.
    """
    if not query.strip():
        raise ToolError(
            "Guideline search query must not be empty."
        )

    if k < 1:
        raise ToolError(
            "k must be greater than or equal to 1."
        )

    documents = retrieve_guidelines(
        query=query,
        k=k,
    )

    return [
        {
            "source": document.metadata.get(
                "source",
                "unknown",
            ),
            "content": document.page_content,
        }
        for document in documents
    ]


@mcp.tool()
def lint_systemverilog(
    rtl_file: str,
) -> dict:
    """
    Run Verilator lint on a SystemVerilog source file.

    A lint pass is not proof of functional correctness.
    """
    if not rtl_file.strip():
        raise ToolError(
            "RTL file path must not be empty."
        )

    try:
        return run_verilator_lint(
            rtl_file=rtl_file,
        )
    except (ValueError, OSError, RuntimeError) as exc:
        raise ToolError(
            f"Cannot execute Verilator lint: {exc}"
        ) from exc


@mcp.tool()
def synthesize_systemverilog(
    rtl_file: str,
    module_name: str,
) -> dict:
    """
    Run Yosys synthesis for one self-contained RTL source file.

    Saves a source snapshot, synthesis script, logs and,
    on success, a JSON netlist.

    The caller is responsible for requiring successful lint
    before invoking synthesis in the design workflow.

    Synthesis success is not proof of functional correctness.
    """
    if not rtl_file.strip():
        raise ToolError(
            "RTL file path must not be empty."
        )

    if not module_name.strip():
        raise ToolError(
            "Module name must not be empty."
        )

    try:
        return run_yosys_synthesis(
            rtl_file=rtl_file,
            module_name=module_name,
        )
    except (ValueError, OSError, RuntimeError) as exc:
        raise ToolError(
            f"Cannot execute Yosys synthesis: {exc}"
        ) from exc


@mcp.tool()
def render_netlist_schematic(
    netlist_file: str,
    module_name: str,
) -> dict:
    """
    Render an SVG schematic from an existing Yosys JSON netlist.

    Creates SVG and DOT files in a separate rendering directory.
    Does not regenerate RTL or rerun synthesis.

    A rendered schematic is not proof of functional correctness.
    """
    if not netlist_file.strip():
        raise ToolError(
            "Netlist file path must not be empty."
        )

    if not module_name.strip():
        raise ToolError(
            "Module name must not be empty."
        )

    try:
        svg_path = render_schematic(
            netlist_file=netlist_file,
            module_name=module_name,
        )
    except (
        ValueError,
        OSError,
        RuntimeError,
    ) as exc:
        raise ToolError(
            f"Cannot render netlist schematic: {exc}"
        ) from exc

    svg_path = Path(svg_path).resolve()
    dot_path = svg_path.with_suffix(".dot")
    render_dir = svg_path.parent

    if not svg_path.is_file():
        raise ToolError(
            "Schematic renderer did not create an SVG file."
        )

    if not dot_path.is_file():
        raise ToolError(
            "Schematic renderer did not create a DOT file."
        )

    return {
        "passed": True,
        "module_name": module_name,
        "netlist_file": str(Path(netlist_file).resolve()),
        "output_dir": str(render_dir),
        "svg_file": str(svg_path),
        "dot_file": str(dot_path),
        "stdout_file": str(render_dir / "stdout.log"),
        "stderr_file": str(render_dir / "stderr.log"),
    }