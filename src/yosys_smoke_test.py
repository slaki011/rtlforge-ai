import json
import shutil
import subprocess
import tempfile
from pathlib import Path


MODULE_NAME = "yosys_mux_smoke"

RTL_CODE = """\
module yosys_mux_smoke (
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic sel,
    output logic [7:0] y
);

    assign y = sel ? b : a;

endmodule
"""


def main() -> None:
    yosys_path = shutil.which("yosys")

    if yosys_path is None:
        raise RuntimeError(
            "Yosys executable was not found in PATH."
        )

    with tempfile.TemporaryDirectory(
        prefix="rtlforge_yosys_"
    ) as directory:
        working_directory = Path(directory)

        rtl_path = working_directory / f"{MODULE_NAME}.sv"
        script_path = working_directory / "synthesis.ys"
        netlist_path = working_directory / "netlist.json"

        rtl_path.write_text(
            RTL_CODE,
            encoding="utf-8",
        )

        # Relative filenames are resolved inside the temporary directory.
        script_path.write_text(
            f"read_verilog -sv {rtl_path.name}\n"
            f"synth -top {MODULE_NAME}\n"
            f"write_json {netlist_path.name}\n",
            encoding="utf-8",
        )

        print("TEMPORARY RTL CREATED")

        command = [
            yosys_path,
            "-s",
            script_path.name,
        ]

        try:
            result = subprocess.run(
                command,
                cwd=working_directory,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "Yosys exceeded the 60-second test timeout."
            ) from exc

        print("YOSYS RETURN CODE:", result.returncode)

        if result.returncode != 0:
            print("\n--- YOSYS STDOUT ---")
            print(result.stdout)
            print("\n--- YOSYS STDERR ---")
            print(result.stderr)

            raise RuntimeError(
                "Yosys synthesis failed. Inspect the output above."
            )

        if not netlist_path.is_file():
            raise AssertionError(
                "Yosys returned success but no JSON netlist was created."
            )

        netlist = json.loads(
            netlist_path.read_text(encoding="utf-8")
        )

        modules = netlist.get("modules")

        if not isinstance(modules, dict):
            raise AssertionError(
                "JSON netlist does not contain a modules dictionary."
            )

        top_module = modules.get(MODULE_NAME)

        if not isinstance(top_module, dict):
            raise AssertionError(
                f"JSON netlist does not contain top module {MODULE_NAME}."
            )

        ports = top_module.get("ports", {})

        expected_ports = {
            "a": ("input", 8),
            "b": ("input", 8),
            "sel": ("input", 1),
            "y": ("output", 8),
        }

        if set(ports) != set(expected_ports):
            raise AssertionError(
                f"Unexpected netlist ports: {sorted(ports)}"
            )

        for name, (direction, width) in expected_ports.items():
            port = ports[name]

            if port.get("direction") != direction:
                raise AssertionError(
                    f"Unexpected direction for port {name}."
                )

            if len(port.get("bits", [])) != width:
                raise AssertionError(
                    f"Unexpected width for port {name}."
                )

        print("JSON NETLIST CREATED")
        print("TOP MODULE:", MODULE_NAME)
        print("PORT NAMES, DIRECTIONS AND WIDTHS OK")

    print("TEMPORARY FILES REMOVED")
    print("YOSYS SYNTHESIS SMOKE TEST PASSED")
    print("Functional correctness was not verified.")


if __name__ == "__main__":
    main()
