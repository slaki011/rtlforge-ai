from typing import Literal

from langgraph.graph import END, START, StateGraph

from src.graph.state import RTLState
from src.graph.nodes.architect import design_architecture
from src.graph.nodes.lint_routing import route_after_lint
from src.graph.nodes.mcp_verilator_lint import (
    mcp_verilator_lint_node,
)
from src.graph.nodes.retrieve_guidelines import (
    retrieve_guidelines_node,
)
from src.graph.nodes.rtl_corrector import correct_rtl
from src.graph.nodes.rtl_generator import generate_rtl
from src.graph.nodes.save_rtl import save_rtl
from src.graph.nodes.schematic_node import schematic_node
from src.graph.nodes.spec_analyzer import analyze_spec
from src.graph.nodes.yosys_synthesis_node import (
    yosys_synthesis_node,
)


def route_after_generation(
    state: RTLState,
) -> Literal["save_rtl", "stop"]:
    """
    Continue only when generation or correction produced
    non-empty RTL.

    A clarification request ends the current workflow run.
    """
    status = state.get("status")

    if status == "needs_clarification":
        return "stop"

    if status == "generated":
        rtl_code = state.get("rtl_code", "")

        if not isinstance(rtl_code, str) or not rtl_code.strip():
            raise ValueError(
                "Cannot continue: status='generated' "
                "but rtl_code is empty or invalid."
            )

        return "save_rtl"

    raise ValueError(
        f"Unexpected status after RTL generation: {status!r}"
    )


def route_after_synthesis(
    state: RTLState,
) -> Literal["render_schematic", "stop"]:
    """
    Render a schematic only after successful synthesis.
    """
    status = state.get("status")
    synthesis_result = state.get("synthesis_result")

    if not isinstance(synthesis_result, dict):
        raise ValueError(
            "Cannot route after synthesis: "
            "synthesis_result is missing or invalid."
        )

    passed = synthesis_result.get("passed")

    if not isinstance(passed, bool):
        raise ValueError(
            "Cannot route after synthesis: "
            "passed must be a boolean."
        )

    if status == "synthesis_passed" and passed:
        return "render_schematic"

    if status == "synthesis_failed" and not passed:
        return "stop"

    raise ValueError(
        "Cannot route after synthesis: "
        "status and synthesis_result disagree."
    )


def build_workflow():
    """
    Build the complete RTLForge AI workflow.

    The workflow supports:
    - structured specification analysis
    - project guideline retrieval through MCP
    - microarchitecture generation
    - RTL generation
    - bounded lint correction
    - Verilator lint through MCP
    - Yosys synthesis through MCP
    - SVG schematic rendering through MCP
    """
    builder = StateGraph(RTLState)

    builder.add_node(
        "analyze_spec",
        analyze_spec,
    )

    builder.add_node(
        "retrieve_guidelines",
        retrieve_guidelines_node,
    )

    builder.add_node(
        "design_architecture",
        design_architecture,
    )

    builder.add_node(
        "generate_rtl",
        generate_rtl,
    )

    builder.add_node(
        "save_rtl",
        save_rtl,
    )

    builder.add_node(
        "verilator_lint",
        mcp_verilator_lint_node,
    )

    builder.add_node(
        "correct_rtl",
        correct_rtl,
    )

    builder.add_node(
        "yosys_synthesis",
        yosys_synthesis_node,
    )

    builder.add_node(
        "render_schematic",
        schematic_node,
    )

    builder.add_edge(
        START,
        "analyze_spec",
    )

    builder.add_edge(
        "analyze_spec",
        "retrieve_guidelines",
    )

    builder.add_edge(
        "retrieve_guidelines",
        "design_architecture",
    )

    builder.add_edge(
        "design_architecture",
        "generate_rtl",
    )

    builder.add_conditional_edges(
        "generate_rtl",
        route_after_generation,
        {
            "save_rtl": "save_rtl",
            "stop": END,
        },
    )

    builder.add_edge(
        "save_rtl",
        "verilator_lint",
    )

    builder.add_conditional_edges(
        "verilator_lint",
        route_after_lint,
        {
            "finish": "yosys_synthesis",
            "correct": "correct_rtl",
            "stop": END,
        },
    )

    builder.add_conditional_edges(
        "correct_rtl",
        route_after_generation,
        {
            "save_rtl": "save_rtl",
            "stop": END,
        },
    )

    builder.add_conditional_edges(
        "yosys_synthesis",
        route_after_synthesis,
        {
            "render_schematic": "render_schematic",
            "stop": END,
        },
    )

    builder.add_edge(
        "render_schematic",
        END,
    )

    return builder.compile()


graph = build_workflow()