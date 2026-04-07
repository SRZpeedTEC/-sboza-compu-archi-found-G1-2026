// =============================================================================
// magnitude_comparator — Comparador de magnitud estructural (A < B)
//
// Parámetros:
//   WIDTH : ancho de los operandos en bits (default 8)
//
// Puertos:
//   a         : operando A
//   b         : operando B
//   less_than : 1 si A < B, 0 si no
//
// Implementación:
//   A < B  ↔  la resta A − B produce borrow final = 1.
//   Cadena ripple-borrow idéntica a ALU_Substractor.sv:
//     bw[0]   = ~a[0] & b[0]
//     bw[i]   = (~a[i] & b[i]) | (~a[i] & bw[i-1]) | (b[i] & bw[i-1])
//   Solo se propaga el borrow; el resultado de la resta no se usa.
// =============================================================================

module magnitude_comparator #(
    parameter integer WIDTH = 8
)(
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    output logic             less_than
);

    wire [WIDTH-1:0] bw;

    // Bit 0: borrow inicial
    assign bw[0] = ~a[0] & b[0];

    genvar i;
    generate
        for (i = 1; i < WIDTH; i++) begin : ripple_borrow
            assign bw[i] = (~a[i] & b[i]) | (~a[i] & bw[i-1]) | (b[i] & bw[i-1]);
        end
    endgenerate

    assign less_than = bw[WIDTH-1];

endmodule
