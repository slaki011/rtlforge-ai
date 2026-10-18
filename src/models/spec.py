from typing import Literal

from pydantic import BaseModel, Field


class PortSpec(BaseModel):
    name: str = Field(
        description="Signal name."
    )

    direction: Literal["input", "output"] = Field(
        description="Signal direction."
    )

    width: int = Field(
        ge=1,
        description="Signal width in bits."
    )

    description: str = Field(
        description="Short description of the signal."
    )


class ClockSpec(BaseModel):
    signal: str = Field(
        description="Clock signal name."
    )

    edge: Literal["rising", "falling"] = Field(
        description="Active clock edge."
    )


class ResetSpec(BaseModel):
    signal: str = Field(
        description="Reset signal name."
    )

    polarity: Literal["active_high", "active_low"] = Field(
        description="Reset polarity."
    )

    reset_type: Literal["synchronous", "asynchronous"] = Field(
        description="Reset behavior."
    )


class StructuredRTLSpec(BaseModel):
    module_name: str = Field(
        description="Suggested SystemVerilog module name."
    )

    description: str = Field(
        description="Short description of the requested hardware block."
    )

    design_type: Literal[
        "combinational",
        "sequential",
        "fsm",
        "unknown",
    ] = Field(
        description="High-level RTL design category."
    )

    ports: list[PortSpec] = Field(
        description="Known top-level RTL ports."
    )

    clock: ClockSpec | None = Field(
        default=None,
        description="Clock configuration if specified."
    )

    reset: ResetSpec | None = Field(
        default=None,
        description="Reset configuration if specified."
    )

    behavior: list[str] = Field(
        description="Explicitly requested behavioral requirements."
    )

    assumptions: list[str] = Field(
        description=(
            "Necessary assumptions made because the user specification "
            "did not explicitly define something."
        )
    )

    ambiguities: list[str] = Field(
        description=(
            "Important missing or ambiguous requirements that could "
            "affect the generated RTL behavior."
        )
    )