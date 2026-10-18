import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from src.graph.workflow import graph


def print_json_section(
    title: str,
    value: dict,
) -> None:
    print(f"\n--- {title} ---")
    print(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the RTLForge AI design pipeline."
    )

    parser.add_argument(
        "--spec",
        required=True,
        help="Natural-language RTL specification.",
    )

    parser.add_argument(
        "--open-schematic",
        action="store_true",
        help=(
            "Open the generated SVG schematic using the "
            "macOS default application."
        ),
    )

    arguments = parser.parse_args()

    if not arguments.spec.strip():
        parser.error("--spec must not be empty.")

    return arguments


def require_dictionary(
    result: dict,
    key: str,
) -> dict:
    value = result.get(key)

    if not isinstance(value, dict):
        raise RuntimeError(
            f"{key} is missing or invalid."
        )

    return value


def open_schematic(svg_file: str) -> None:
    svg_path = Path(svg_file).resolve()

    if not svg_path.is_file():
        raise FileNotFoundError(
            f"SVG schematic does not exist: {svg_path}"
        )

    if sys.platform != "darwin":
        print(
            "Automatic schematic opening is currently "
            "implemented only for macOS."
        )
        print("Open the SVG manually:", svg_path)
        return

    subprocess.run(
        ["open", str(svg_path)],
        check=True,
    )


async def run_pipeline(
    user_spec: str,
    should_open_schematic: bool,
) -> None:
    print("RTLForge AI: starting pipeline")

    result = await graph.ainvoke(
        {
            "user_spec": user_spec,
            "iteration": 0,
        }
    )

    status = result.get("status")
    iteration = result.get("iteration", 0)

    generation_result = require_dictionary(
        result,
        "generation_result",
    )

    print_json_section(
        "GENERATION RESULT",
        generation_result,
    )

    print("\nFINAL STATUS:", status)
    print("CORRECTION ATTEMPTS:", iteration)

    if status == "needs_clarification":
        print(
            "\nGeneration stopped because clarification "
            "is required."
        )

        ambiguities = generation_result.get(
            "unresolved_ambiguities",
            [],
        )

        if ambiguities:
            print("\nUNRESOLVED AMBIGUITIES:")

            for ambiguity in ambiguities:
                print(f"- {ambiguity}")
        else:
            print(
                "\nNo unresolved ambiguity details "
                "were returned."
            )

        print(
            "\nNo further save, lint, synthesis, "
            "or schematic rendering was performed."
        )
        return

    rtl_file = result.get("rtl_file")

    if not isinstance(rtl_file, str) or not rtl_file.strip():
        raise RuntimeError(
            "Pipeline finished without a valid RTL file."
        )

    print("\nRTL FILE:", rtl_file)

    lint_result = require_dictionary(
        result,
        "lint_result",
    )

    print_json_section(
        "LINT RESULT",
        lint_result,
    )

    if status == "lint_failed":
        if lint_result.get("passed") is not False:
            raise RuntimeError(
                "Final status disagrees with lint_result."
            )

        print(
            "\nPipeline stopped after the maximum "
            "number of lint correction attempts."
        )

        print(
            "\nSynthesis and schematic rendering "
            "were skipped."
        )

        print(
            "\nLint failure is not a functional "
            "verification result."
        )
        return

    if lint_result.get("passed") is not True:
        raise RuntimeError(
            "Pipeline continued beyond lint without "
            "a successful lint result."
        )

    synthesis_result = require_dictionary(
        result,
        "synthesis_result",
    )

    print_json_section(
        "SYNTHESIS RESULT",
        synthesis_result,
    )

    if status == "synthesis_failed":
        if synthesis_result.get("passed") is not False:
            raise RuntimeError(
                "Final status disagrees with synthesis_result."
            )

        print(
            "\nSYNTHESIS FAILURE:",
            synthesis_result.get("failure_reason"),
        )

        print(
            "\nSCHEMATIC SKIPPED: synthesis did not pass."
        )

        print(
            "\nLint and synthesis results are not proof "
            "of functional correctness."
        )
        return

    if synthesis_result.get("passed") is not True:
        raise RuntimeError(
            "Pipeline continued beyond synthesis without "
            "a successful synthesis result."
        )

    if status != "schematic_generated":
        raise RuntimeError(
            f"Unexpected final pipeline status: {status!r}"
        )

    schematic_result = require_dictionary(
        result,
        "schematic_result",
    )

    if schematic_result.get("passed") is not True:
        raise RuntimeError(
            "Final status disagrees with schematic_result."
        )

    print_json_section(
        "SCHEMATIC RESULT",
        schematic_result,
    )

    netlist_file = synthesis_result.get(
        "netlist_file"
    )
    svg_file = schematic_result.get(
        "svg_file"
    )
    dot_file = schematic_result.get(
        "dot_file"
    )

    print("\n--- FINAL ARTIFACTS ---")
    print("RTL:", rtl_file)
    print("JSON NETLIST:", netlist_file)
    print("SVG SCHEMATIC:", svg_file)
    print("DOT SCHEMATIC:", dot_file)

    if should_open_schematic:
        if not isinstance(svg_file, str):
            raise RuntimeError(
                "Cannot open schematic: svg_file is invalid."
            )

        open_schematic(svg_file)
        print("SCHEMATIC OPENED")

    print("\nRTLForge AI pipeline completed successfully.")
    print(
        "Lint, synthesis and schematic generation "
        "do not establish functional correctness."
    )


def main() -> None:
    arguments = parse_arguments()

    asyncio.run(
        run_pipeline(
            user_spec=arguments.spec,
            should_open_schematic=(
                arguments.open_schematic
            ),
        )
    )


if __name__ == "__main__":
    main()