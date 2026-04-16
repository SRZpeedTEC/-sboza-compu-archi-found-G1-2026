// =============================================================================
// comparator_pwm — Genera pwm_out = 1 cuando count < duty (estructural)
//
// Delega la comparacion de magnitud a magnitude_comparator, que implementa
// A < B mediante la cadena ripple-borrow de A - B.
// =============================================================================

module comparator_pwm(
    input  [7:0] count,
    input  [7:0] duty,
    output       pwm_out
);

    magnitude_comparator #(.WIDTH(8)) u_cmp (
        .a         (count),
        .b         (duty),
        .less_than (pwm_out)
    );

endmodule
