// =============================================================================
// mux2 — Multiplexor 2:1 parametrizable (estructural)
//
// Parámetros:
//   WIDTH : ancho del dato en bits (default 26)
//
// Puertos:
//   a   : entrada 0 (seleccionada cuando sel=0)
//   b   : entrada 1 (seleccionada cuando sel=1)
//   sel : selector
//   out : salida seleccionada
//
// Implementación:
//   out[i] = (sel & b[i]) | (~sel & a[i])
//   Equivale a: NOT + AND + AND + OR por bit — compuertas explícitas.
// =============================================================================

module mux2 #(
    parameter integer WIDTH = 26
)(
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    input  logic             sel,
    output logic [WIDTH-1:0] out
);

    genvar i;
    generate
        for (i = 0; i < WIDTH; i++) begin : mux_bits
            assign out[i] = (sel & b[i]) | (~sel & a[i]);
        end
    endgenerate

endmodule
