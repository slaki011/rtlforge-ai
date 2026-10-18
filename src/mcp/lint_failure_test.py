import asyncio
import json
import tempfile
from pathlib import Path

from mcp import Client

from src.mcp.mcp_server import mcp


INVALID_RTL = """\
module mcp_lint_failure (
    input  logic data_in,
    output logic data_out
);

    assign data_out = ;

endmodule
"""


async def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="rtlforge_mcp_lint_failure_"
    ) as temporary_directory:
        rtl_path = (
            Path(temporary_directory) / "mcp_lint_failure.sv"
        )

        rtl_path.write_text(
            INVALID_RTL,
            encoding="utf-8",
        )

        print("INVALID RTL CREATED")

        async with Client(
            mcp,
            raise_exceptions=True,
        ) as client:
            print("MCP CONNECTION OK")

            result = await client.call_tool(
                "lint_systemverilog",
                {"rtl_file": str(rtl_path)},
            )

            response_text = "\n".join(
                block.text
                for block in result.content
                if hasattr(block, "text")
            )

            if result.is_error:
                raise AssertionError(
                    "The MCP tool itself failed. Expected a normal "
                    "tool response containing a failed lint result:\n"
                    f"{response_text}"
                )

            lint_result = json.loads(response_text)

            if not isinstance(lint_result, dict):
                raise AssertionError(
                    "Expected a dictionary containing lint results."
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

            if lint_result.get("passed") is not False:
                raise AssertionError(
                    "Invalid RTL must produce passed=False."
                )

            return_code = lint_result.get("return_code")

            if (
                not isinstance(return_code, int)
                or return_code == 0
            ):
                raise AssertionError(
                    "Expected a nonzero Verilator return code."
                )

            if lint_result.get("error_count", 0) < 1:
                raise AssertionError(
                    "Expected at least one parsed error diagnostic."
                )

            print("\nINVALID RTL REJECTED AS EXPECTED")

    print("TEMPORARY RTL REMOVED")
    print("MCP NEGATIVE LINT TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())