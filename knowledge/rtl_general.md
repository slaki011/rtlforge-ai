# General RTL Design Guidelines

RTL should be simple, deterministic and synthesizable.

Preferred SystemVerilog constructs:

- logic
- always_ff
- always_comb
- enum
- parameters

Use explicit signal widths.

Avoid simulation-only constructs in synthesizable RTL.

Do not introduce functionality not required by the specification.

Prefer simple RTL architectures over unnecessarily complex implementations.