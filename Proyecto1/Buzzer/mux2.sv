// =============================================================================
// mux2 — Multiplexor 2:1 parametrizable
//
// Parámetros:
//   WIDTH : ancho del dato en bits (default 26)
//
// Puertos:
//   a   : entrada 0
//   b   : entrada 1
//   sel : selector (0 = a, 1 = b)
//   out : salida seleccionada
// =============================================================================

module mux2 #(
    parameter integer WIDTH = 26
)(
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    input  logic             sel,
    output logic [WIDTH-1:0] out
);

    assign out = sel ? b : a;

endmodule