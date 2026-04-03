// =============================================================================
// comparator — Comparador de igualdad parametrizable
//
// Parámetros:
//   WIDTH : ancho de los operandos en bits (default 26)
//
// Puertos:
//   a     : operando A
//   b     : operando B
//   eq    : 1 si a == b, 0 si no
// =============================================================================

module comparator #(
    parameter integer WIDTH = 26
)(
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    output logic             eq
);

    assign eq = (a == b);

endmodule