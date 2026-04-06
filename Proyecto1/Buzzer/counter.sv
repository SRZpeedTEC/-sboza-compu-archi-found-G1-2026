// =============================================================================
// counter — Contador parametrizable con enable, reset asíncrono y done
//
// Parámetros:
//   WIDTH  : ancho del contador en bits (default 26)
//
// Puertos:
//   clk    : reloj
//   reset  : reset asíncrono activo alto
//   en     : enable externo
//   target : valor tope (cuenta de 0 a target inclusive)
//   done   : 1 cuando count == target, se congela hasta reset
//
// Comportamiento:
//   - Cuenta de 0 a target
//   - Se auto-congela cuando done=1 (en_internal = en & ~done)
//   - Reset asíncrono lleva count a 0
// =============================================================================

module counter #(
    parameter integer WIDTH = 26
)(
    input  logic             clk,
    input  logic             reset,
    input  logic             en,
    input  logic [WIDTH-1:0] target,
    output logic             done
);

    logic [WIDTH-1:0] count;
    logic [WIDTH-1:0] count_next;
    logic             en_internal;

    // done: comparacion combinacional
    comparator #(.WIDTH(WIDTH)) u_cmp (
        .a  (count),
        .b  (target),
        .eq (done)
    );

    // en_internal: solo corre si habilitado y no ha llegado al tope
    assign en_internal = en & ~done;

    // incrementer
    incrementer #(.WIDTH(WIDTH)) u_inc (
        .in  (count),
        .out (count_next)
    );

    // registro del contador
    flipflopD #(.WIDTH(WIDTH)) u_dff (
        .clk   (clk),
        .reset (reset),
        .en    (en_internal),
        .d     (count_next),
        .q     (count)
    );

endmodule