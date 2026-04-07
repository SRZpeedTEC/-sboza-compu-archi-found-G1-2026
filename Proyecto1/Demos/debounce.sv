// =============================================================================
// debounce — Filtro de rebote para señales mecánicas (estructural)
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
// Implementación:
//   - incrementer   para counter+1
//   - eq_comparator para counter==TARGET
//   - Lógica next_counter con AND/OR (misma mascara que ALU.sv y counter_pwm.sv)
//   - always_ff para todos los registros
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
    // (localparam: calculo en tiempo de elaboracion, no genera hardware)
    // -------------------------------------------------------------------------
    localparam integer TARGET     = (CLK_FREQ / 1000) * DEBOUNCE_MS;
    localparam integer TIMER_BITS = $clog2(TARGET + 2);

    localparam logic [TIMER_BITS-1:0] TARGET_VEC = TARGET[TIMER_BITS-1:0];

    // -------------------------------------------------------------------------
    // Registros internos
    // -------------------------------------------------------------------------
    logic btn_sync;
    logic btn_prev;
    logic [TIMER_BITS-1:0] counter;

    // -------------------------------------------------------------------------
    // Sincronizador: evita metaestabilidad al cruzar dominio asincrono->sincrono
    // -------------------------------------------------------------------------
    always_ff @(posedge clk or posedge reset)
        if (reset) btn_sync <= 1'b0;
        else       btn_sync <= btn_in;

    // -------------------------------------------------------------------------
    // Registro del valor previo para detectar cambio en btn_sync
    // -------------------------------------------------------------------------
    always_ff @(posedge clk or posedge reset)
        if (reset) btn_prev <= 1'b0;
        else       btn_prev <= btn_sync;

    // -------------------------------------------------------------------------
    // Detector de cambio: XOR entre ciclo actual y anterior
    // -------------------------------------------------------------------------
    wire changed;
    assign changed = btn_sync ^ btn_prev;

    // -------------------------------------------------------------------------
    // Incrementer y comparador para el contador de estabilidad
    // -------------------------------------------------------------------------
    wire [TIMER_BITS-1:0] counter_inc;
    incrementer #(.WIDTH(TIMER_BITS)) u_inc (
        .in  (counter),
        .out (counter_inc)
    );

    wire at_target;
    eq_comparator #(.WIDTH(TIMER_BITS)) u_cmp (
        .a  (counter),
        .b  (TARGET_VEC),
        .eq (at_target)
    );

    // -------------------------------------------------------------------------
    // next_counter (tres casos mutuamente excluyentes):
    //   changed=1              → 0          (reset del contador)
    //   changed=0, at_target=1 → counter    (hold, ya llegó)
    //   changed=0, at_target=0 → counter+1  (sigue contando)
    // Cuando changed=1: ambos terminos son 0, resultado = 0. Sin ?:
    // -------------------------------------------------------------------------
    wire [TIMER_BITS-1:0] next_counter;
    assign next_counter = ({TIMER_BITS{~changed &  at_target}} & counter)
                        | ({TIMER_BITS{~changed & ~at_target}} & counter_inc);

    always_ff @(posedge clk or posedge reset)
        if (reset) counter <= {TIMER_BITS{1'b0}};
        else       counter <= next_counter;

    // -------------------------------------------------------------------------
    // Salida: se actualiza combinacionalmente y se registra en FF
    // -------------------------------------------------------------------------
    wire next_btn_out;
    assign next_btn_out = at_target & btn_sync;

    always_ff @(posedge clk or posedge reset)
        if (reset) btn_out <= 1'b0;
        else       btn_out <= next_btn_out;

endmodule
