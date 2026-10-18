# RTLForge AI

RTLForge AI is an AI-assisted, agentic RTL design assistant that converts natural-language hardware specifications into synthesizable SystemVerilog.

The project combines structured specification analysis, retrieval-augmented generation, microarchitecture planning, RTL generation, bounded lint correction, synthesis, and schematic rendering in a LangGraph workflow.

RTLForge AI is designed as an engineering assistant. It does not claim that generated RTL is functionally verified.

## Project Status

The current MVP supports the following pipeline:

```text
Natural-language RTL specification
                ↓
          Spec Analyzer
                ↓
     Structured Pydantic specification
                ↓
   Project RTL guideline retrieval via MCP
                ↓
      Microarchitecture Architect
                ↓
           RTL Generator
                ↓
             save_rtl
                ↓
      Verilator lint via MCP
          ↓ PASS       ↓ FAIL
          ↓        RTL Corrector
          ↓             ↓
          └──── save and re-lint
                ↓
        Yosys synthesis via MCP
                ↓
           JSON netlist
                ↓
   Schematic rendering via MCP
                ↓
          SVG and DOT files
```

The correction loop is intentionally bounded. The current configuration allows a maximum of two RTL correction attempts after lint failures.

## Important Disclaimer

RTLForge AI is an AI-assisted RTL design assistant.

A successful Verilator lint result means that the source passed the configured lint command. A successful Yosys synthesis result means that Yosys produced the expected synthesis output.

Neither result establishes:

- functional correctness;
- equivalence with the intended behavior;
- simulation coverage;
- formal correctness;
- implementation sign-off;
- production readiness;
- silicon readiness.

The project must not be described as a verified RTL generator.

## Main Capabilities

### Structured specification analysis

The Spec Analyzer converts a natural-language request into a Pydantic-validated structured specification.

The structured specification can include:

- module name;
- design description;
- design type;
- ports;
- clock definition;
- reset definition;
- required behavior;
- explicit assumptions;
- unresolved ambiguities.

Pydantic validation confirms the structure of the response. It does not establish semantic or functional correctness.

### Explicit ambiguity handling

RTLForge AI is designed not to silently invent material hardware behavior.

The RTL Generator and RTL Corrector support two outcomes:

```text
generated
needs_clarification
```

When unresolved ambiguity would materially affect module behavior, the workflow can stop with:

```text
status = needs_clarification
rtl_code = ""
```

The returned generation result preserves unresolved ambiguities and implementation notes.

### Retrieval-augmented generation

The project uses a local Chroma vector database containing project-specific RTL coding guidelines from:

```text
knowledge/*.md
```

These files are project g*idelines. They are not AMD documen*ation or third-party proprietary d*sign documentation.

The current R*G stack uses:

- `langchain_core.d*cuments.Document`;
- `langchain_op*nai.OpenAIEmbeddings`;
- `langchai*_chroma.Chroma`;
- `text-embedding*3-small`;
- collection name `rtl_g*idelines`;
- local persistence dir*ctory `.chroma_db`.

Guideline ret*ieval is exposed through the MCP t*ol:

```text
search_rtl_guidelines*```

Retrieved guidelines are trea*ed as coding guidance, not as new *unctional requirements.

### Micro*rchitecture generation

The Archit*ct receives:

- the structured spe*ification;
- retrieved project RTL*guidelines.

It produces a structu*ed microarchitecture proposal that*can include:

- architecture type;*- summary;
- registers;
- combinat*onal blocks;
- control strategy;
-*reset strategy;
- implementation s*eps;
- applied guidelines;
- guide*ine sources;
- assumptions;
- ambi*uities.

The Architect does not ge*erate RTL.

### SystemVerilog gene*ation

The RTL Generator receives:*
- the structured specification;
-*proposed microarchitecture;
- retr*eved project guidelines.

It produ*es one complete SystemVerilog modu*e using a structured output model.*
The generator is instructed to:

* preserve explicit functional requ*rements;
- avoid silently inventin* behavior;
- generate synthesizabl* SystemVerilog;
- use `always_ff` *or sequential logic when appropria*e;
- use `always_comb` for non-tri*ial combinational logic when appro*riate;
- use non-blocking assignme*ts in sequential logic;
- use bloc*ing assignments in combinational l*gic;
- avoid unintended latches;
-*implement reset and clock behavior*exactly as specified;
- avoid test*ench, UVM, assertion, and formal-v*rification code.

### RTL saving

*enerated RTL is saved under:

```t*xt
generated/<module_name>.sv
```
*After a correction attempt, the co*rected RTL is saved again before a*other lint run.

The current MVP o*erwrites the main module file with*the latest version. Per-attempt so*rce history is not yet persisted a* a dedicated run directory.

### V*rilator lint through MCP

Verilato* lint is exposed through the MCP t*ol:

```text
lint_systemverilog
``*

The configured command is equiva*ent to:

```bash
verilator --lint-*nly -Wall <rtl_file>
```

The resu*t contains:

- pass or fail status*
- return code;
- executed command*
- warning count;
- error count;
-*structured diagnostics;
- standard*output;
- standard error.

A lint *ass is not proof of functional cor*ectness.

### Bounded RTL correcti*n

When lint fails, the workflow c*n invoke the RTL Corrector.

The c*rrector receives:

- structured sp*cification;
- proposed architectur*;
- retrieved guidelines;
- curren* RTL;
- complete generation result*
- Verilator diagnostics;
- curren* correction iteration;
- maximum c*rrection count.

The corrector is *nstructed to make only changes req*ired to address lint diagnostics a*d to preserve the specified behavi*r and interface.

If correction wo*ld require choosing unspecified fu*ctional behavior, it can return:

*``text
needs_clarification
```

Th* current maximum number of correct*on attempts is:

```text
2
```

##* Yosys synthesis through MCP

Yosy* synthesis is exposed through the *CP tool:

```text
synthesize_syste*verilog
```

Synthesis runs only a*ter successful Verilator lint.

Th* initial synthesis flow uses:

```*ext
read_verilog -sv source.sv
syn*h -top <module_name>
write_json ne*list.json
```

Each synthesis run *reates a separate output directory*containing artifacts such as:

```*ext
source.sv
synthesis.ys
netlist*json
stdout.log
stderr.log
```

A *ynthesis pass is not proof of func*ional correctness.

### Schematic *endering through MCP

Schematic re*dering is exposed through the MCP *ool:

```text
render_netlist_schem*tic
```

The renderer reads an exi*ting Yosys JSON netlist and uses t*e Yosys `show` command together wi*h Graphviz.

The rendering flow pr*duces:

```text
schematic.svg
sche*atic.dot
stdout.log
stderr.log
```*
The schematic is generated from t*e synthesized netlist. It is not a* AI-generated illustration.

A ren*ered schematic is not proof of fun*tional correctness.

## MCP Tools
*The current MCP server is created *n:

```text
src/mcp/mcp_server.py
*``

It exposes the following tools*

| MCP tool | Purpose |
|---|---|*| `search_rtl_guidelines` | Retrie*e relevant project RTL guidelines *
| `lint_systemverilog` | Run Veri*ator lint on a saved SystemVerilog*file |
| `synthesize_systemverilog* | Run Yosys synthesis and create * JSON netlist |
| `render_netlist_*chematic` | Create SVG and DOT sch*matics from a JSON netlist |

The *urrent LangGraph integration uses *n in-process MCP client.

This con*irms the MCP tool boundaries and d*ta flow, but it is not yet a separ*tely deployed remote MCP service.
*## LangGraph State

The shared sta*e is defined in:

```text
src/grap*/state.py
```

The current state i*cludes fields such as:

```python
*ser_spec: str
structured_spec: dic*
retrieved_guidelines: list[dict]
*rchitecture: dict
generation_resul*: dict
rtl_code: str
rtl_file: str*lint_result: dict
synthesis_result* dict
schematic_result: dict
statu*: str
iteration: int
```

Each nod* returns a partial state update.

*# Final Workflow Statuses

A pipel*ne run can end with one of the fol*owing relevant statuses:

### `nee*s_clarification`

The workflow sto*ped because unresolved ambiguity r*quires user input.

RTL saving, li*t, synthesis, or schematic renderi*g after that clarification request*is skipped.

### `lint_failed`

Ve*ilator lint still failed after the*configured correction limit.

Synt*esis and schematic rendering are s*ipped.

### `synthesis_failed`

Li*t passed, but Yosys synthesis did *ot successfully create the expecte* netlist.

Schematic rendering is skipped.

### `schematic_generated`

Lint and synthesis completed successfully, and SVG and DOT schematic files were created.

This is the successful terminal state of the current MVP.

It does not establish functional correctness.

## Requirements

The current project has been developed and tested with:

- macOS;
- Python 3.12;
- a local Python virtual environment;
- OpenAI API access;
- Verilator;
- Yosys;
- Graphviz.

The project also uses Python libraries including:

- LangGraph;
- LangChain Core;
- LangChain OpenAI;
- LangChain Chroma;
- Chroma;
- Pydantic;
- python-dotenv;
- MCP Python SDK.

## External Tools

Verify that the required command-line tools are available:

```bash
verilator --version
yosys -V
dot -V
```

On macOS with Homebrew, the required tools can be installed with:

```bash
brew install verilator
brew install yosys
brew install graphviz
```

No package upgrade should be performed unless it is required by the local environment.

## Python Environment

Create and activate a local virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Upgrade `pip` only if required by the local environment:

```bash
python -m pip install --upgrade pip
```

Install the Python dependencies using the dependency file provided by the project.

If the repository contains `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

All project commands should be executed from the repository root.

## Environment Configuration

Create a root-level `.env` file:

```text
OPENAI_API_KEY=<your-openai-api-key>
```

The `.env` file must not be committed to Git.

Make sure `.gitignore` contains at least:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.chroma_db/
```

Generated RTL and synthesis artifacts can be ignored or committed selectively, depending on whether they are intended as project examples.

## RAG Knowledge Base

Project RTL guidelines are stored in:

```text
knowledge/*.md
```

Build or refresh the local Chroma database with:

```bash
python -m src.rag.ingest
```

The persisted vector database is stored in:

```text
.chroma_db
```

A successful ingestion command may complete without extensive terminal output, depending on the current implementation.

## Running RTLForge AI

The primary terminal entry point is:

```bash
python -m src.run_pipeline --spec "<natural-language RTL specification>"
```

To open the generated SVG schematic automatically on macOS:

```bash
python -m src.run_pipeline \
  --spec "<natural-language RTL specification>" \
  --open-schematic
```

## Example

Run a fully specified combinational multiplexer example:

```bash
python -m src.run_pipeline \
  --spec "Create exactly one synthesizable SystemVerilog module named rtlforge_mux2_demo. Ports: input logic [7:0] a, input logic [7:0] b, input logic sel, output logic [7:0] y. The module is purely combinational, with no clock, reset, registers, or internal state. When sel is 0, y equals a. When sel is 1, y equals b. Implement the output using exactly this continuous assignment: assign y = sel ? b : a; This expression defines the required SystemVerilog four-state behavior. Do not add parameters, additional ports, internal state, verification constructs, or other functionality." \
  --open-schematic
```

A successful run should end with:

```text
FINAL STATUS: schematic_generated
```

The runner prints the generated artifact paths:

```text
RTL
JSON netlist
SVG schematic
DOT schematic
```

## Generated Artifacts

The main generated RTL is stored under:

```text
generated/<module_name>.sv
```

Synthesis runs are stored under unique directories similar to:

```text
generated/synthesis/<module_name>_<unique_suffix>/
```

A synthesis directory can contain:

```text
source.sv
synthesis.ys
netlist.json
stdout.log
stderr.log
```

Schematic rendering creates a separate directory under the corresponding synthesis directory:

```text
schematic_<unique_suffix>/
```

It can contain:

```text
input.json
render.ys
schematic.svg
schematic.dot
stdout.log
stderr.log
```

## Example Successful Output

```text
RTLForge AI: starting pipeline

FINAL STATUS: schematic_generated
CORRECTION ATTEMPTS: 0

--- FINAL ARTIFACTS ---
RTL: generated/rtlforge_mux2_demo.sv
JSON NETLIST: generated/synthesis/.../netlist.json
SVG SCHEMATIC: generated/synthesis/.../schematic.svg
DOT SCHEMATIC: generated/synthesis/.../schematic.dot

RTLForge AI pipeline completed successfully.
Lint, synthesis and schematic generation do not establish
functional correctness.
```

Exact paths include unique synthesis and schematic run-directory suffixes.

## Project Structure

The relevant project structure is approximately:

```text
rtl-design-agent/
├── .env
├── .gitignore
├── README.md
├── generated/
├── knowledge/
├── src/
│   ├── graph/
│   │   ├── state.py
│   │   ├── workflow.py
│   │   └── nodes/
│   │       ├── architect.py
│   │       ├── correction_context.py
│   │       ├── lint_routing.py
│   │       ├── mcp_verilator_lint.py
│   │       ├── retrieve_guidelines.py
│   │       ├── rtl_corrector.py
│   │       ├── rtl_generator.py
│   │       ├── save_rtl.py
│   │       ├── schematic_node.py
│   │       ├── spec_analyzer.py
│   │       ├── verilator_lint.py
│   │       ├── yosys_synthesis.py
│   │       └── yosys_synthesis_node.py
│   ├── mcp/
│   │   └── mcp_server.py
│   ├── models/
│   │   └── rtl.py
│   ├── rag/
│   │   ├── ingest.py
│   │   └── retriever.py
│   ├── render_schematic.py
│   └── run_pipeline.py
└── .chroma_db/
```

The exact structure can evolve as tests, reports, and run-history support are added.

## Safety and Design Principles

RTLForge AI follows these principles:

1. Functional requirements come from the structured specification.
2. Architecture is an implementation proposal.
3. Retrieved guidelines are coding guidance.
4. Material ambiguity must not be silently resolved.
5. Lint failure can trigger only a bounded correction loop.
6. Corrected RTL must be saved before it is linted again.
7. Synthesis can run only after a successful lint result.
8. Schematic rendering can run only after successful synthesis.
9. Every tool result is preserved as structured state.
10. Tool success must not be described as functional verification.

## Current Limitations

The MVP currently has the following limitations:

- it does not generate testbenches;
- it does not use UVM;
- it does not run simulation;
- it does not perform formal verification;
- it does not perform equivalence checking;
- it does not prove end-to-end functional correctness;
- it does not prove that the generated implementation matches unstated user intent;
- it supports an initial single-source-file synthesis flow;
- it does not configure multiple RTL files, include directories, libraries, or vendor primitives;
- SystemVerilog support is constrained by the configured Yosys frontend;
- the main generated RTL file is overwritten by a later correction attempt;
- correction history is not yet stored as a first-class run artifact;
- the MCP client currently runs in process;
- a remote MCP deployment is not part of the current MVP;
- schematic rendering can become difficult to read for larger synthesized designs;
- human approval checkpoints are not yet part of the workflow.

## Possible Next Steps

Potential future improvements include:

- persistent run IDs;
- per-attempt RTL history;
- a unified `report.json`;
- human approval after specification analysis;
- human approval before RTL generation;
- LangGraph checkpointing;
- execution tracing and observability;
- regression tests using pytest;
- a web interface;
- embedded SVG schematic viewing;
- remote MCP transport;
- multi-file RTL synthesis;
- technology-library-aware synthesis;
- downloadable run archives.

Simulation, testbench generation, UVM, and formal verification are intentionally outside the scope of the current MVP.

## Positioning

RTLForge AI should be presented as:

> An AI-assisted, agentic RTL design assistant that converts natural-language specifications into structured hardware requirements, proposes a microarchitecture, generates SystemVerilog, retrieves project coding guidelines, performs bounded lint-driven correction, runs synthesis, and renders a synthesized schematic.

It should not be presented as:

> A verified RTL generator.

## License

No license is declared in this README.

Before publishing or distributing the repository, add an appropriate `LICENSE` file and update this section to match the selected license.