import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.graph.state import RTLState
from src.models.rtl import RTLGenerationResult


PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")


SYSTEM_PROMPT = """
You are the SystemVerilog generation component of RTLForge AI.

Your task is to generate a clear, simple, synthesizable SystemVerilog
implementation from:

1. A structured RTL specification.
2. A proposed microarchitecture.
3. Retrieved project RTL coding guidelines.

Rules:

1. Treat the structured specification as the source of functional
   requirements.

2. Treat the architecture as an implementation proposal.

3. Treat retrieved guidelines as coding guidance, not as additional
   functional requirements.

4. Do not invent unspecified functional behavior silently.

5. Preserve explicitly recorded assumptions and unresolved ambiguities.

6. If an ambiguity would materially change module behavior and no safe
   implementation can be produced without choosing behavior for the user,
   set generation_status to needs_clarification and return an empty
   rtl_code string.

7. If generation can proceed using only assumptions already explicitly
   listed in the specification or architecture, record those assumptions
   in assumptions_used.

8. Generate exactly one complete SystemVerilog module.

9. Return raw SystemVerilog code in rtl_code without Markdown fences.

10. Use synthesizable SystemVerilog constructs.

11. Use always_ff for sequential logic when appropriate.

12. Use always_comb for non-trivial combinational logic when appropriate.

13. Use nonblocking assignments in sequential logic.

14. Use blocking assignments in combinational logic.

15. Implement clock edge, reset polarity, and reset type exactly as
    described in the structured specification.

16. Avoid latches by assigning combinational outputs on all paths.

17. Do not add a testbench.

18. Do not add assertions yet.

19. Do not add verification code.

20. Do not claim the RTL has passed lint, synthesis, simulation, formal
    verification, or functional verification.

21. Do not include explanatory text inside rtl_code except normal
    SystemVerilog comments.

22. In guideline_sources, include only filenames present in the retrieved
    guideline context.

Your responsibility is RTL code generation only.
"""


def format_retrieved_guidelines(
    retrieved_guidelines: list[dict],
) -> str:
    """
    Convert retrieved guideline dictionaries into prompt context.
    """

    if not retrieved_guidelines:
        return "No RTL guidelines were retrieved."

    sections = []

    for guideline in retrieved_guidelines:
        source = guideline.get("source", "unknown")
        content = guideline.get("content", "").strip()

        if not content:
            continue

        sections.append(
            f"GUIDELINE SOURCE: {source}\n"
            f"GUIDELINE CONTENT:\n{content}"
        )

    if not sections:
        return "No non-empty RTL guidelines were retrieved."

    return "\n\n---\n\n".join(sections)


def strip_markdown_fences(rtl_code: str) -> str:
    """
    Remove Markdown code fences if the model returns them despite
    instructions.
    """

    cleaned_code = rtl_code.strip()

    if cleaned_code.startswith("```systemverilog"):
        cleaned_code = cleaned_code[len("```systemverilog"):].lstrip()
    elif cleaned_code.startswith("```sv"):
        cleaned_code = cleaned_code[len("```sv"):].lstrip()
    elif cleaned_code.startswith("```"):
        cleaned_code = cleaned_code[3:].lstrip()

    if cleaned_code.endswith("```"):
        cleaned_code = cleaned_code[:-3].rstrip()

    return cleaned_code


def generate_rtl(state: RTLState) -> dict:
    """
    Generate SystemVerilog from the structured specification,
    proposed architecture, and retrieved project guidelines.
    """

    structured_spec = state.get("structured_spec")

    if not structured_spec:
        raise ValueError(
            "Cannot generate RTL because structured_spec is empty."
        )

    architecture = state.get("architecture")

    if not architecture:
        raise ValueError(
            "Cannot generate RTL because architecture is empty."
        )

    retrieved_guidelines = state.get(
        "retrieved_guidelines",
        [],
    )

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY was not found. "
            f"Expected .env at: {PROJECT_ROOT / '.env'}"
        )

    model = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
    )

    structured_model = model.with_structured_output(
        RTLGenerationResult
    )

    structured_spec_json = json.dumps(
        structured_spec,
        indent=2,
        ensure_ascii=False,
    )

    architecture_json = json.dumps(
        architecture,
        indent=2,
        ensure_ascii=False,
    )

    guideline_context = format_retrieved_guidelines(
        retrieved_guidelines
    )

    prompt = f"""
{SYSTEM_PROMPT}

STRUCTURED RTL SPECIFICATION:

{structured_spec_json}

PROPOSED MICROARCHITECTURE:

{architecture_json}

RETRIEVED PROJECT RTL GUIDELINES:

{guideline_context}
"""

    result = structured_model.invoke(prompt)

    generation_result = result.model_dump()

    generation_status = generation_result["generation_status"]
    rtl_code = strip_markdown_fences(
        generation_result["rtl_code"]
    )

    if generation_status == "needs_clarification":
        rtl_code = ""

    if generation_status == "generated" and not rtl_code:
        raise ValueError(
            "RTL Generator returned status='generated' but rtl_code is empty."
        )

    generation_result["rtl_code"] = rtl_code

    return {
        "generation_result": generation_result,
        "rtl_code": rtl_code,
        "status": generation_status,
    }

