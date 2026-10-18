import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.graph.state import RTLState
from src.models.architecture import ArchitectureSpec


PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(PROJECT_ROOT / ".env")


SYSTEM_PROMPT = """
You are the microarchitecture design component of RTLForge AI.

Your task is to propose a clear and implementable RTL microarchitecture
from a structured digital hardware specification.

You may also receive retrieved RTL coding guidelines from the project's
local knowledge base.

Rules:

1. Base the architecture on the structured specification.

2. Use the retrieved guidelines as project coding guidance, not as
   additional functional requirements.

3. Do not invent user requirements.

4. Preserve ambiguities from the structured specification.

5. If you make an architectural assumption, record it explicitly in
   the assumptions field.

6. Do not generate SystemVerilog.

7. Do not generate a testbench.

8. Do not perform simulation, formal verification, lint, or synthesis.

9. Do not claim that the architecture is functionally verified.

10. Do not claim that schema validation proves semantic correctness.

11. Prefer a simple architecture when the requested design does not
    require an FSM.

12. Only propose an FSM when the required behavior contains meaningful
    states or sequencing.

13. Only include reset behavior when it exists in the structured
    specification.

14. Keep the architecture suitable for synthesizable SystemVerilog.

15. In guideline_sources, list only source filenames that appear in
    the retrieved guidelines.

Your responsibility is architectural planning only.
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


def design_architecture(state: RTLState) -> dict:
    """
    Propose an RTL microarchitecture from the structured specification
    and retrieved project guidelines.
    """

    structured_spec = state.get("structured_spec")

    if not structured_spec:
        raise ValueError(
            "Cannot design architecture because structured_spec is empty."
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
        ArchitectureSpec
    )

    structured_spec_json = json.dumps(
        structured_spec,
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

RETRIEVED PROJECT RTL GUIDELINES:

{guideline_context}
"""

    result = structured_model.invoke(prompt)

    return {
        "architecture": result.model_dump(),
        "status": "architecture_designed",
    }