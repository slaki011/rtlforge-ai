import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "generated" / "synthesis"

MODULE_NAME_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_$]*"
)


def run_yosys_synthesis(
    rtl_file: str,
    module_name: str,
    output_dir: str | None = None,
    timeout_seconds: int = 60,
) -> dict:
    """
    Synthesize one self-contained SystemVerilog source file.

    This initial runner does not configure include directories,
    additional source files, libraries, or external frontends.

    Synthesis success is not proof of functional correctness.
    """
    if not MODULE_NAME_PATTERN.fullmatch(module_name):
        raise ValueError(
            "module_name must be a simple Verilog identifier."
        )

    if type(timeout_seconds) is not int or timeout_seconds < 1:
        raise ValueError(
            "timeout_seconds must be a positive integer."
        )

    if not rtl_file.strip():
        raise ValueError("rtl_file must not be empty.")

    rtl_path = Path(rtl_file).resolve()

    if not rtl_path.is_file():
        raise FileNotFoundError(
            f"RTL source file does not exist: {rtl_path}"
        )

    yosys_path = shutil.which("yosys")

    if yosys_path is None:
        raise RuntimeError(
            "Yosys executable was not found in PATH."
        )

    output_root = (
        Path(output_dir).resolve()
        if output_dir is not None
        else DEFAULT_OUTPUT_DIR
    )
    output_root.mkdir(parents=True, exist_ok=True)

    run_dir = Path(
        tempfile.mkdtemp(
            prefix=f"{module_name}_",
            dir=str(output_root),
        )
    )

    source_copy = run_dir / "source.sv"
    script_path = run_dir / "synthesis.ys"
    netlist_path = run_dir / "netlist.json"
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"

    shutil.copyfile(rtl_path, source_copy)

    script_path.write_text(
        "read_verilog -sv source.sv\n"
        f"synth -top {module_name}\n"
        "write_json netlist.json\n",
        encoding="utf-8",
    )

    command = [
        yosys_path,
        "-s",
        script_path.name,
    ]

    timed_out = False
    return_code = None

    try:
        process = subprocess.run(
            command,
            cwd=run_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        return_code = process.returncode
        stdout = process.stdout
        stderr = process.stderr

    except subprocess.TimeoutExpired as exc:
        timed_out = True

        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")

        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    netlist_valid = False
    failure_reason = None

    if timed_out:
        failure_reason = (
            f"Yosys exceeded timeout of {timeout_seconds} seconds."
        )
    elif return_code != 0:
        failure_reason = (
            f"Yosys exited with return code {return_code}."
        )
    elif not netlist_path.is_file():
        failure_reason = "Yosys did not create a JSON netlist."
    else:
        try:
            netlist = json.loads(
                netlist_path.read_text(encoding="utf-8")
            )

            modules = (
                netlist.get("modules")
                if isinstance(netlist, dict)
                else None
            )

            netlist_valid = (
                isinstance(modules, dict)
                and isinstance(modules.get(module_name), dict)
            )

            if not netlist_valid:
                failure_reason = (
                    "JSON netlist does not contain the requested module."
                )

        except (ValueError, OSError) as exc:
            failure_reason = (
                f"Cannot read a valid JSON netlist: {exc}"
            )

    passed = (
        not timed_out
        and return_code == 0
        and netlist_valid
    )

    return {
        "passed": passed,
        "return_code": return_code,
        "timed_out": timed_out,
        "failure_reason": failure_reason,
        "command": command,
        "module_name": module_name,
        "source_file": str(rtl_path),
        "source_snapshot": str(source_copy),
        "output_dir": str(run_dir),
        "netlist_file": str(netlist_path) if passed else None,
        "stdout_file": str(stdout_path),
        "stderr_file": str(stderr_path),
        "stdout": stdout,
        "stderr": stderr,
    }