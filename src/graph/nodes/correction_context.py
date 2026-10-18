from copy import deepcopy

from src.graph.state import RTLState
from src.graph.nodes.lint_routing import (
    MAX_CORRECTIONS,
    route_after_lint,
)


def build_correction_context(state: RTLState) -> dict:
    """
    Prepare input for a future RTL correction node.

    Does not call an LLM, modify RTL, update state,
    increment iteration, or execute tools.
    """
    decision = route_after_lint(state)

    if decision != "correct":
        raise ValueError(
            "Correction context requires a failed lint result "
            "with remaining correction attempts. "
            f"Routing decision: {decision!r}"
        )

    structured_spec = state.get("structured_spec")

    if not isinstance(structured_spec, dict) or not structured_spec:
        raise ValueError(
            "Cannot prepare correction: structured_spec is empty "
            "or invalid."
        )

    architecture = state.get("architecture")

    if not isinstance(architecture, dict) or not architecture:
        raise ValueError(
            "Cannot prepare correction: architecture is empty "
            "or invalid."
        )

    rtl_code = state.get("rtl_code")

    if not isinstance(rtl_code, str) or not rtl_code.strip():
        raise ValueError(
            "Cannot prepare correction: rtl_code is empty or invalid."
        )

    generation_result = state.get("generation_result")

    if (
        not isinstance(generation_result, dict)
        or generation_result.get("generation_status") != "generated"
    ):
        raise ValueError(
            "Cannot prepare correction: generation_result must "
            "describe generated RTL."
        )

    if generation_result.get("rtl_code") != rtl_code:
        raise ValueError(
            "Cannot prepare correction: generation_result.rtl_code "
            "does not match the current rtl_code."
        )

    iteration = state.get("iteration", 0)

    context = {
        "structured_spec": structured_spec,
        "architecture": architecture,
        "retrieved_guidelines": state.get(
            "retrieved_guidelines",
            [],
        ),
        "generation_result": generation_result,
        "rtl_code": rtl_code,
        "lint_result": state["lint_result"],
        "completed_corrections": iteration,
        "next_correction_attempt": iteration + 1,
        "max_corrections": MAX_CORRECTIONS,
    }

    # Keep nested context data independent from the original state.
    return deepcopy(context)