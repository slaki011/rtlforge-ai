from typing import Literal

from pydantic import BaseModel, Field


class RTLGenerationResult(BaseModel):
    generation_status: Literal[
        "generated",
        "needs_clarification",
    ] = Field(
        description=(
            "Whether RTL was generated or generation was stopped because "
            "important ambiguities require clarification."
        )
    )

    module_name: str | None = Field(
        default=None,
        description=(
            "SystemVerilog module name when RTL was generated."
        ),
    )

    rtl_code: str = Field(
        description=(
            "Generated synthesizable SystemVerilog source code. "
            "Must be empty when generation_status is needs_clarification."
        )
    )

    assumptions_used: list[str] = Field(
        description=(
            "Assumptions explicitly used while generating the RTL."
        )
    )

    unresolved_ambiguities: list[str] = Field(
        description=(
            "Requirements that remain ambiguous and may affect RTL behavior."
        )
    )

    applied_guidelines: list[str] = Field(
        description=(
            "Project RTL guideline principles applied during generation."
        )
    )

    guideline_sources: list[str] = Field(
        description=(
            "Source filenames of retrieved project guidelines used during "
            "RTL generation."
        )
    )

    implementation_notes: list[str] = Field(
        description=(
            "Short technical notes about the generated implementation."
        )
    )