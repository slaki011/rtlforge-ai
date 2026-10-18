from typing import Literal

from pydantic import BaseModel, Field


class RegisterSpec(BaseModel):
    name: str = Field(
        description="Suggested register name."
    )

    width: int = Field(
        ge=1,
        description="Register width in bits."
    )

    purpose: str = Field(
        description="Purpose of the register in the design."
    )

    reset_value: str | None = Field(
        default=None,
        description=(
            "Suggested reset value when reset behavior is explicitly "
            "defined or clearly required."
        ),
    )


class CombinationalBlockSpec(BaseModel):
    name: str = Field(
        description="Suggested name of the combinational block."
    )

    purpose: str = Field(
        description="Purpose of the combinational logic."
    )

    inputs: list[str] = Field(
        description="Signals used as inputs to the combinational block."
    )

    outputs: list[str] = Field(
        description="Signals driven by the combinational block."
    )


class ArchitectureSpec(BaseModel):
    architecture_type: Literal[
        "combinational",
        "registered_datapath",
        "fsm",
        "fsm_with_datapath",
        "unknown",
    ] = Field(
        description="Selected high-level implementation architecture."
    )

    summary: str = Field(
        description="Short explanation of the proposed microarchitecture."
    )

    registers: list[RegisterSpec] = Field(
        description="Registers required by the proposed architecture."
    )

    combinational_blocks: list[CombinationalBlockSpec] = Field(
        description="Combinational logic blocks required by the design."
    )

    control_strategy: str = Field(
        description=(
            "Description of the control approach, such as direct control "
            "signals, conditional register updates, or an FSM."
        )
    )

    reset_strategy: str | None = Field(
        default=None,
        description=(
            "Reset implementation strategy when reset behavior is part "
            "of the structured specification."
        ),
    )

    implementation_steps: list[str] = Field(
        description=(
            "Ordered implementation plan for the future RTL Generator."
        )
    )

    applied_guidelines: list[str] = Field(
        description=(
            "Relevant RTL guideline principles applied to the proposed "
            "architecture."
        )
    )

    guideline_sources: list[str] = Field(
        description=(
            "Source filenames of retrieved project guidelines used by "
            "the Architect."
        )
    )

    assumptions: list[str] = Field(
        description=(
            "Architecture-level assumptions that are not explicit user "
            "requirements."
        )
    )

    ambiguities: list[str] = Field(
        description=(
            "Unresolved requirements that could materially affect the "
            "proposed architecture or generated RTL."
        )
    )