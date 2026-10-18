from typing import TypedDict


class RTLState(TypedDict, total=False):

    # Original user request
    user_spec: str

    # Parsed specification
    structured_spec: dict

    # Complete structured generator output
    generation_result: dict

    # Proposed design architecture
    architecture: dict

    # Generated SystemVerilog
    rtl_code: str

    rtl_file: str

    # Tool results
    schematic_result: dict
    lint_result: dict
    synthesis_result: dict

    # Workflow control
    iteration: int
    status: str

    retrieved_guidelines: list[dict]


