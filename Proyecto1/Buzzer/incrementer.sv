// =============================================================================
// incrementer — Suma 1 a la entrada, parametrizable en ancho de bits
//
// Parámetros:
//   WIDTH : ancho del dato en bits (default 26)
//
// Puertos:
//   in  : valor actual
//   out : valor actual + 1
// =============================================================================

module incrementer #(
    parameter integer WIDTH = 26
)(
    input  logic [WIDTH-1:0] in,
    output logic [WIDTH-1:0] out
);

    assign out = in + 1'b1;

endmodule