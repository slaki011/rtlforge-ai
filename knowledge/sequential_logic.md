# Sequential Logic Guidelines

- Use always_ff for sequential SystemVerilog logic.
- Use non-blocking assignments in sequential processes.
- Registers should normally be driven by a single sequential process.
- Clocked state changes should occur on a clearly defined clock edge.
- Reset behavior must exactly match the specification.
- Avoid mixing combinational and sequential behavior inside the same process.