# Reset Guidelines

## Synchronous Reset

A synchronous reset is evaluated inside the active clock edge.

Example:

always_ff @(posedge clk) begin
    if (!rst_n)
        q <= '0;
    else
        q <= d;
end

## Asynchronous Reset

An asynchronous reset is part of the event control.

Example:

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        q <= '0;
    else
        q <= d;
end

The RTL implementation must preserve both the reset type
and polarity defined in the specification.