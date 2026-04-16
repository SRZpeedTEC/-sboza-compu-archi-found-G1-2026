// =============================================================================
// decoder_pwm — Decodificador de nivel PWM a ciclo de trabajo (estructural)
//
// Traduce pwm_level (3 bits) al valor de duty (8 bits) correspondiente:
//   000 ->   0  (0000_0000)
//   001 ->  25  (0001_1001)
//   010 ->  50  (0011_0010)
//   011 ->  75  (0100_1011)
//   100 -> 100  (0110_0100)
//
// Implementación: suma de productos (SOP) por bit, derivada de tabla de verdad.
// Cada assign es NOT + AND + OR — compuertas explícitas.
// =============================================================================

module decoder_pwm(
    input  [2:0] pwm_level,
    output [7:0] duty
);

    wire p2, p1, p0;
    assign p2 = pwm_level[2];
    assign p1 = pwm_level[1];
    assign p0 = pwm_level[0];

    // duty[7]: nunca activo
    assign duty[7] = 1'b0;

    // duty[6]: activo en 011 y 100
    assign duty[6] = (~p2 & p1 & p0) | (p2 & ~p1 & ~p0);

    // duty[5]: activo en 010 y 100
    assign duty[5] = (~p2 & p1 & ~p0) | (p2 & ~p1 & ~p0);

    // duty[4]: activo en 001 y 010  →  ~p2 & (p1 XOR p0)
    assign duty[4] = ~p2 & (p1 ^ p0);

    // duty[3]: activo en 001 y 011  →  ~p2 & p0
    assign duty[3] = ~p2 & p0;

    // duty[2]: activo solo en 100
    assign duty[2] = p2 & ~p1 & ~p0;

    // duty[1]: activo en 010 y 011  →  ~p2 & p1
    assign duty[1] = ~p2 & p1;

    // duty[0]: activo en 001 y 011  →  ~p2 & p0
    assign duty[0] = ~p2 & p0;

endmodule
