import re
import shutil
import subprocess
from pathlib import Path

from src.graph.state import RTLState


DIAGNOSTIC_PATTERN = re.compile(
    r"^%"
    r"(?P<severity>Error|Warning)"
    r"(?:-(?P<code>[A-Z0-9_]+))?"
    r":\s*"
    r"(?:(?P<file>\S+):(?P<line>\d+):(?:(?P<column>\d+):)?\s*)?"
    r"(?P<message>.*)$"
)


def parse_verilator_diagnostics(output: str) -> list:
    """
    Parse Verilator text diagnostics into structured dictionaries.

    Only primary %Error and %Warning lines are parsed.
    The complete raw stdout/stderr is still preserved separately.
    """

    diagnostics = []

    for line in output.splitlines():
        match = DIAGNOSTIC_PATTERN.match(line.strip())

        if not match:
            continue

        data = match.groupdict()

        diagnostic = {
            "severity": data["severity"].lower(),
            "code": data["code"],
            "message": data["message"].strip(),
            "file": data["file"],
            "line": (
                int(data["line"])
                if data["line"] is not None
                else None
            ),
            "column": (
                int(data["column"])
                if data["column"] is not None
                else None
            ),
        }

        diagnostics.append(diagnostic)

    return diagnostics


def run_verilator_lint(rtl_file: str) -> dict:
    """
    Run Verilator lint on a SystemVerilog file.

    Returns:
        Dictionary containing:
        - pass/fail status
        - Verilator return code
        - executed command
        - warning/error counts
        - structured diagnostics
        - raw stdout/stderr
    """

    verilator_path = shutil.which("verilator")

    if verilator_path is None:
        raise RuntimeError(
            "Verilator executable was not found in PATH."
        )

    rtl_path = Path(rtl_file).resolve()

    if not rtl_path.exists():
        raise FileNotFoundError(
            f"RTL file does not exist: {rtl_path}"
        )

    command = [
        verilator_path,
        "--lint-only",
        "-Wall",
        str(rtl_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    diagnostic_text = "\n".join(
        part
        for part in [stdout, stderr]
        if part
    )

    diagnostics = parse_verilator_diagnostics(
        diagnostic_text
    )

    warning_count = sum(
        1
        for diagnostic in diagnostics
        if diagnostic["severity"] == "warning"
    )

    error_count = sum(
        1
        for diagnostic in diagnostics
        if diagnostic["severity"] == "error"
    )

    passed = result.returncode == 0

    return {
        "passed": passed,
        "return_code": result.returncode,
        "command": command,
        "warning_count": warning_count,
        "error_count": error_count,
        "diagnostics": diagnostics,
        "stdout": stdout,
        "stderr": stderr,
    }


def verilator_lint_node(state: RTLState) -> dict:
    """
    LangGraph adapter that runs Verilator lint
    on the RTL file stored in RTLState.
    """

    rtl_file = state.get(
        "rtl_file",
        "",
    ).strip()

    if not rtl_file:
        raise ValueError(
            "Cannot run Verilator because rtl_file is empty."
        )

    lint_result = run_verilator_lint(
        rtl_file
    )

    if lint_result["passed"]:
        status = "lint_passed"
    else:
        status = "lint_failed"

    return {
        "lint_result": lint_result,
        "status": status,
    }