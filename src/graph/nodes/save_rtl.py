from pathlib import Path

from src.graph.state import RTLState


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GENERATED_DIR = PROJECT_ROOT / "generated"


def save_rtl(state: RTLState) -> dict:
    """
    Save generated SystemVerilog code to the generated/ directory.
    """

    rtl_code = state.get("rtl_code", "").strip()

    if not rtl_code:
        raise ValueError(
            "Cannot save RTL because rtl_code is empty."
        )

    structured_spec = state.get("structured_spec", {})

    module_name = structured_spec.get(
        "module_name",
        "",
    ).strip()

    if not module_name:
        raise ValueError(
            "Cannot save RTL because module_name is missing "
            "from structured_spec."
        )

    GENERATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rtl_file = GENERATED_DIR / f"{module_name}.sv"

    rtl_file.write_text(
        rtl_code + "\n",
        encoding="utf-8",
    )

    return {
        "rtl_file": str(rtl_file),
        "status": "rtl_saved",
    }