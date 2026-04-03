// =============================================================================
// debounce — Filtro de rebote para señales mecánicas
//
// Parámetros:
//   CLK_FREQ    : frecuencia del reloj en Hz (default 50MHz)
//   DEBOUNCE_MS : tiempo de estabilidad requerido en ms (default 20ms)
//
// Funcionamiento:
//   Cada vez que btn_in cambia, el contador se reinicia.
//   Solo cuando btn_in se mantiene estable DEBOUNCE_MS ms completos
//   se transfiere el valor a btn_out.
//
// Puertos:
//   clk     : reloj del sistema
//   reset   : reset asíncrono activo alto
//   btn_in  : señal sucia del botón
//   btn_out : señal limpia y estable
// =============================================================================
module debounce #(
    parameter integer CLK_FREQ    = 50_000_000,
    parameter integer DEBOUNCE_MS = 20
)(
    input  logic clk,
    input  logic reset,
    input  logic btn_in,
    output logic btn_out
);

    // -------------------------------------------------------------------------
    // Calculo del target: ciclos necesarios para DEBOUNCE_MS milisegundos
    // -------------------------------------------------------------------------
    localparam integer TARGET = (CLK_FREQ / 1000) * DEBOUNCE_MS;
    localparam integer TIMER_BITS = $clog2(TARGET + 2);


    // -------------------------------------------------------------------------
    // Registros internos
    // -------------------------------------------------------------------------
    logic btn_sync;                      // btn_in sincronizado al dominio del reloj
    logic btn_prev;                      // valor anterior para detectar cambio
    logic [TIMER_BITS-1:0] counter;      // contador de estabilidad

    // -------------------------------------------------------------------------
    // Sincronizador: evita metaestabilidad al cruzar dominio asincrono->sincrono
    // -------------------------------------------------------------------------
    always @(posedge clk or posedge reset)
        if (reset) btn_sync <= 1'b0;
        else       btn_sync <= btn_in;

    // -------------------------------------------------------------------------
    // Registro del valor previo para detectar cambio en btn_sync
    // -------------------------------------------------------------------------
    always @(posedge clk or posedge reset)
        if (reset) btn_prev <= 1'b0;
        else       btn_prev <= btn_sync;

    // -------------------------------------------------------------------------
    // Detector de cambio: si btn_sync != btn_prev, la señal cambio este ciclo
    // -------------------------------------------------------------------------
    wire changed;
    assign changed = btn_sync ^ btn_prev;

    // -------------------------------------------------------------------------
    // Contador de estabilidad
    // Se reinicia si hay cambio, incrementa si no llego al target
    // -------------------------------------------------------------------------
    wire [TIMER_BITS-1:0] counter_inc;
    assign counter_inc = counter + 1'b1;

    wire at_target;
    assign at_target = (counter == TARGET[TIMER_BITS-1:0]);

    wire [TIMER_BITS-1:0] next_counter;
    assign next_counter = changed    ? {TIMER_BITS{1'b0}} :
                          at_target  ? counter             :
                                       counter_inc;

    always @(posedge clk or posedge reset)
        if (reset) counter <= {TIMER_BITS{1'b0}};
        else       counter <= next_counter;

    // -------------------------------------------------------------------------
    // Salida: se actualiza solo cuando el contador llega al target
    // -------------------------------------------------------------------------
    always @(posedge clk or posedge reset)
        if (reset)                    btn_out <= 1'b0;
        else if (at_target & btn_sync) btn_out <= 1'b1;
        else                           btn_out <= 1'b0;
        

endmodule