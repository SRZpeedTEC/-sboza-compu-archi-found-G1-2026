// =============================================================================
// dff — D flip-flop parametrizable con reset asíncrono y enable síncrono
//
// Parámetros:
//   WIDTH : ancho del dato en bits (default 1)
//
// Puertos:
//   clk   : reloj
//   reset : reset asíncrono activo alto
//   en    : enable síncrono (1 = captura D, 0 = mantiene Q)
//   d     : dato de entrada
//   q     : dato de salida
// =============================================================================

module flipflopD #(
    parameter integer WIDTH = 1
)(
    input  logic             clk,
    input  logic             reset,
    input  logic             en,
    input  logic [WIDTH-1:0] d,
    output logic [WIDTH-1:0] q
);

    always_ff @(posedge clk or posedge reset) begin
        if (reset)   q <= {WIDTH{1'b0}};
        else if (en) q <= d;
    end

endmodule