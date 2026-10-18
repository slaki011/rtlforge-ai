from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.graph.state import RTLState
from src.models.spec import StructuredRTLSpec


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


SYSTEM_PROMPT = """
You are the specification analysis component of RTLForge AI.

Your task is to convert a user's natural-language digital hardware
request into a structured RTL specification.

Rules:

1. Extract only requirements that are explicitly stated by the user.

2. Do not silently invent hardware behavior.

3. If information is missing but the design can still reasonably
   proceed with an assumption, record that assumption explicitly
   in the assumptions field.

4. If missing information could materially change RTL behavior,
   record it in the ambiguities field.

5. Distinguish combinational, sequential, and FSM-based designs.

6. Only create clock information when a clock is explicitly stated
   or clearly required by the described synchronous behavior.

7. Only create reset information when reset behavior is specified.

8. Port widths must reflect the user's specification when given.

9. Do not generate SystemVerilog.

10. Do not perform verification.

11. Do not claim that the specification is functionally correct.

Your responsibility is specification extraction and structuring only.
"""


def analyze_spec(state: RTLState) -> dict:
    """
    Convert the natural-language user specification into a structured
    RTL specification using an LLM and Pydantic structured output.
    """

    user_spec = state.get("user_spec", "").strip()

    if not user_spec:
        raise ValueError(
            "Cannot analyze RTL specification because user_spec is empty."
        )

    model = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
    )

    structured_model = model.with_structured_output(
        StructuredRTLSpec
    )

    prompt = f"""
{SYSTEM_PROMPT}

USER RTL SPECIFICATION:

{user_spec}
"""

    result = structured_model.invoke(prompt)

    return {
        "structured_spec": result.model_dump(),
        "status": "spec_analyzed",
    }