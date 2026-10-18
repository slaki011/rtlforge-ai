import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


MODULE_NAME_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_$]*"
)


def render_schematic(
    netlist_file: str,
    module_name: str,
) -> Path:
    """
    Render a module from an existing Yosys JSON netlist.

    Does not regenerate RTL or rerun synthesis.
    Creates a separate directory for each rendering.
    """
    if not MODULE_NAME_PATTERN.fullmatch(module_name):
        raise ValueError(
            "module_name must be a simple Verilog identifier."
        )

    netlist_path = Path(netlist_file).resolve()

    if not netlist_path.is_file():
        raise FileNotFoundError(
            f"Netlist file does not exist: {netlist_path}"
        )

    netlist = json.loads(
        netlist_path.read_text(encoding="utf-8")
    )

    modules = (
        netlist.get("modules")
        if isinstance(netlist, dict)
        else None
    )

    if (
        not isinstance(modules, dict)
        or not isinstance(modules.get(module_name), dict)
    ):
        raise ValueError(
            f"Netlist does not contain module {module_name!r}."
        )

    yosys_path = shutil.which("yosys")
    dot_path = shutil.which("dot")

    if yosys_path is None:
        raise RuntimeError("Yosys was not found in PATH.")

    if dot_path is None:
        raise RuntimeError("Graphviz dot was not found in PATH.")

    render_dir = Path(
        tempfile.mkdtemp(
            prefix="schematic_",
            dir=str(netlist_path.parent),
        )
    )

    snapshot_path = render_dir / "input.json"
    script_path = render_dir / "render.ys"
    svg_path = render_dir / "schematic.svg"
    dot_file = render_dir / "schematic.dot"

    shutil.copyfile(netlist_path, snapshot_path)

    script_path.write_text(
        "read_json input.json\n"
        "show -format svg -viewer none "
        f"-prefix schematic -width {module_name}\n",
        encoding="utf-8",
    )

    print("INPUT NETLIST:", netlist_path)
    print("OUTPUT DIRECTORY:", render_dir)

    try:
        result = subprocess.run(
            [yosys_path, "-s", script_path.name],
            cwd=render_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        def as_text(value):
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return value or ""

        (render_dir / "stdout.log").write_text(
            as_text(exc.stdout),
            encoding="utf-8",
        )
        (render_dir / "stderr.log").write_text(
            as_text(exc.stderr),
            encoding="utf-8",
        )

        raise RuntimeError(
            f"Schematic rendering timed out. Logs: {render_dir}"
        ) from exc

    (render_dir / "stdout.log").write_text(
        result.stdout,
        encoding="utf-8",
    )
    (render_dir / "stderr.log").write_text(
        result.stderr,
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Schematic rendering failed.\n"
            f"Return code: {result.returncode}\n"
            f"Logs: {render_dir}\n"
            f"{result.stderr}"
        )

    if not svg_path.is_file() or not dot_file.is_file():
        raise RuntimeError(
            "Rendering finished without the expected SVG and DOT files. "
            f"Inspect logs in: {render_dir}"
        )

    svg_root = ET.parse(svg_path).getroot()

    if svg_root.tag.split("}")[-1] != "svg":
        raise RuntimeError(
            "The generated file does not have an SVG root element."
        )

    print("SVG FILE:", svg_path)
    print("DOT FILE:", dot_file)
    print("SCHEMATIC RENDER PASSED")

    return svg_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render an SVG schematic from a Yosys JSON netlist."
    )
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the SVG using the macOS default application.",
    )

    arguments = parser.parse_args()

    svg_path = render_schematic(
        netlist_file=arguments.netlist,
        module_name=arguments.module,
    )

    if arguments.open:
        if sys.platform != "darwin":
            raise RuntimeError(
                "Automatic opening is currently implemented for macOS only. "
                f"Open this SVG manually: {svg_path}"
            )

        subprocess.run(
            ["open", str(svg_path)],
            check=True,
        )

    print("The schematic is not proof of functional correctness.")


if __name__ == "__main__":
    main()