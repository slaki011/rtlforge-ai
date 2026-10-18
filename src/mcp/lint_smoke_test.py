import asyncio
import json
import tempfile
from pathlib import Path

from mcp import Client

from src.mcp.mcp_server import mcp


RTL_CODE = """\
module mcp_lint_smoke (
    input  logic data_in,
    output logic data_out
);

    assign data_out = data_in;

endmodule
"""


async def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="rtlforge_mcp_lint_"
    ) as temporary_directory:
        rtl_path = (
            Path(temporary_directory) / "mcp_lint_smoke.sv"
        )

        rtl_path.write_text(
            RTL_CODE,
            encoding="utf-8",
        )

        print("TEMPORARY RTL CREATED")

        async with Client(
            mcp,
            raise_exceptions=True,
        ) as client:
            print("MCP CONNECTION OK")

            result = await client.call_tool(
                "lint_systemverilog",
                {
                    "rtl_file": str(rtl_path),
                },
            )

            response_text = "\n".join(
                block.text
                for block in result.content
                if hasattr(block, "text")
            )

            if result.is_error:
                raise AssertionError(
                    "MCP lint tool failed:\n"
                    f"{response_text}"
                )

            try:
                lint_result = json.loads(response_text)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    "Expected a JSON lint result, received:\n"
                    f"{response_text}"
                ) from exc

            if not isinstance(lint_result, dict):
                raise AssertionError(
                    "Expected the lint result to be a dictionary."
                )

            print("\n--- LINT RESULT ---")
            print(
                json.dumps(
                    lint_result,
                    indent=2,
                    ensure_ascii=False,
                )
            )
            print("--- END RESULT ---")

            if lint_result.get("passed") is not True:
                raise AssertionError(
                    "Expected the smoke-test RTL to pass lint."
                )

            if lint_result.get("return_code") != 0:
                raise AssertionError(
                    "Expected Verilator return code 0."
                )

            print("\nVERILATOR LINT VIA MCP OK")

    print("TEMPORARY RTL REMOVED")
    print("MCP LINT SMOKE TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())