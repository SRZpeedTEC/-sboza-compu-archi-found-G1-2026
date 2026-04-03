// =============================================================================
// beep_counter — Contador de beeps emitidos con comparación contra target
//
// Parámetros:
//   WIDTH  : ancho del contador en bits (default 2)
//
// Puertos:
//   clk    : reloj
//   reset  : reset asíncrono activo alto
//   en     : pulso de 1 ciclo por cada beep completado (beep_timer_done)
//   target : número de beeps a emitir (01=1, 10=2, 11=3)
//   done   : 1 cuando el próximo incremento alcanzaría target
//            válido y estable mientras en=1
//
// Comportamiento:
//   - done = (count_next == target), combinacional puro
//   - La FSM lee done exactamente cuando en=1 para decidir PAUSE vs DONE
//   - Reset asíncrono lleva count a 0
// =============================================================================

module beep_counter #(
    parameter integer WIDTH = 2
)(
    input  logic             clk,
    input  logic             reset,
    input  logic             en,
    input  logic [WIDTH-1:0] target,
    output logic             done
);

    logic [WIDTH-1:0] count;
    logic [WIDTH-1:0] count_next;

    // incrementer
    incrementer #(.WIDTH(WIDTH)) u_inc (
        .in  (count),
        .out (count_next)
    );

    // registro del contador
    dff #(.WIDTH(WIDTH)) u_dff (
        .clk   (clk),
        .reset (reset),
        .en    (en),
        .d     (count_next),
        .q     (count)
    );

    // done: combinacional sobre count_next
    // valido cuando en=1, que es exactamente cuando la FSM lo necesita
    comparator #(.WIDTH(WIDTH)) u_cmp (
        .a  (count_next),
        .b  (target),
        .eq (done)
    );

endmodule