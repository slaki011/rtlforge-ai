# FSM Design Guidelines

- Prefer SystemVerilog enum types for states.
- Separate state storage from next-state calculation.
- Use sequential logic for the state register.
- Use combinational logic for next-state calculation.
- Provide default assignments in combinational state logic.
- Reset should initialize the FSM to an explicitly defined state.
- Avoid unintended latches.
