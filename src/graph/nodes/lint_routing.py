from typing import Literal

from src.graph.state import RTLState


MAX_CORRECTIONS = 2


def route_after_lint(
    state: RTLState,
) -> Literal["finish", "correct", "stop"]:
    """
    Decide what should happen after a completed lint run.

    This function does not modify RTL, increment iteration,
    or execute any tools.
    """
    status = state.get("status")
    lint_result = state.get("lint_result")

    if not isinstance(lint_result, dict):
        raise ValueError(
            "Cannot route after lint: lint_result is missing or invalid."
        )

    passed = lint_result.get("passed")
    return_code = lint_result.get("return_code")

    if not isinstance(passed, bool):
        raise ValueError(
            "Cannot route after lint: passed must be a boolean."
        )

    if type(return_code) is not int:
        raise ValueError(
            "Cannot route after lint: return_code must be an integer."
        )

    if passed != (return_code == 0):
        raise ValueError(
            "Cannot route after lint: passed and return_code disagree."
        )

    iteration = state.get("iteration", 0)

    if type(iteration) is not int or iteration < 0:
        raise ValueError(
            "Cannot route after lint: iteration must be "
            "a non-negative integer."
        )

    if status == "lint_passed" and passed:
        return "finish"

    if status == "lint_failed" and not passed:
        if iteration >= MAX_CORRECTIONS:
            return "stop"

        return "correct"

    raise ValueError(
        "Cannot route after lint: status and lint result disagree."
    )