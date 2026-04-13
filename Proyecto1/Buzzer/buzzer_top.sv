// =============================================================================
// buzzer_top — Módulo top del buzzer, conecta FSM y contadores
//
// Parámetros:
//   BEEP_TARGET  : ciclos para 1s  (default 49_999_999 @ 50MHz)
//   PAUSE_TARGET : ciclos para 0.5s (default 24_999_999 @ 50MHz)
//
// Instancias:
//   u_fsm         : buzzer_fsm   — FSM one-hot de 4 estados
//   u_beep_timer  : counter      — contador de 1s
//   u_pause_timer : counter      — contador de 0.5s
//   u_beep_counter: beep_counter — contador de beeps emitidos
//
// Puertos externos:
//   clk          : reloj 50MHz
//   reset        : reset asíncrono activo alto
//   activate_buz : activa la secuencia desde elevator_fsm
//   buzzer_mode  : target de beeps (01=1, 10=2, 11=3)
//   led          : salida visible para verificación (futuro: buzzer físico)
//   buzzer_done  : señaliza fin de secuencia a elevator_fsm
// =============================================================================

module buzzer_top #(
    parameter integer BEEP_TARGET  = 49_999_999,
    parameter integer PAUSE_TARGET = 24_999_999
)(
    input  logic        clk,
    input  logic        reset,
    input  logic        activate_buz,
    input  logic [1:0]  buzzer_mode,
    output logic        led,
    output logic        buzzer_done
);

    // -------------------------------------------------------------------------
    // Señales internas
    // -------------------------------------------------------------------------
    logic beep_timer_done;
    logic pause_timer_done;
    logic beeps_done;
    logic beep_timer_en;
    logic pause_timer_en;
    logic beep_timer_reset;
    logic pause_timer_reset;
    logic beep_cnt_reset;

    // -------------------------------------------------------------------------
    // FSM
    // -------------------------------------------------------------------------
    logic fsm_led;

    buzzer_fsm u_fsm (
        .clk              (clk),
        .reset            (reset),
        .activate_buz     (activate_buz),
        .beep_timer_done  (beep_timer_done),
        .pause_timer_done (pause_timer_done),
        .beeps_done       (beeps_done),
        .led              (fsm_led),
        .buzzer_done      (buzzer_done),
        .beep_timer_en    (beep_timer_en),
        .pause_timer_en   (pause_timer_en),
        .beep_timer_reset (beep_timer_reset),
        .pause_timer_reset(pause_timer_reset),
        .beep_cnt_reset   (beep_cnt_reset)
    );

    // -------------------------------------------------------------------------
    // Generador de tono ~1kHz para buzzer pasivo
    // Semiperíodo = 25,000 ciclos @ 50MHz → target = 24_999
    // -------------------------------------------------------------------------
    logic tone_done;
    logic tone_toggle;
    logic tone_reset;

    assign tone_reset = reset | ~fsm_led;

    counter #(.WIDTH(16)) u_tone (
        .clk   (clk),
        .reset (tone_reset),
        .en    (fsm_led),
        .target(16'd24_999),
        .done  (tone_done)
    );

    always_ff @(posedge clk or posedge tone_reset) begin
        if (tone_reset) tone_toggle <= 1'b0;
        else if (tone_done) tone_toggle <= ~tone_toggle;
    end

    assign led = fsm_led & tone_toggle;

    // -------------------------------------------------------------------------
    // Contador de 1s — beep activo
    // -------------------------------------------------------------------------
    counter #(.WIDTH(26)) u_beep_timer (
        .clk    (clk),
        .reset  (beep_timer_reset),
        .en     (beep_timer_en),
        .target (26'(BEEP_TARGET)),
        .done   (beep_timer_done)
    );

    // -------------------------------------------------------------------------
    // Contador de 0.5s — pausa entre beeps
    // -------------------------------------------------------------------------
    counter #(.WIDTH(26)) u_pause_timer (
        .clk    (clk),
        .reset  (pause_timer_reset),
        .en     (pause_timer_en),
        .target (26'(PAUSE_TARGET)),
        .done   (pause_timer_done)
    );

    // -------------------------------------------------------------------------
    // Contador de beeps emitidos
    // beep_timer_done es el enable: pulsa 1 ciclo al terminar cada beep
    // -------------------------------------------------------------------------
    beep_counter #(.WIDTH(2)) u_beep_counter (
        .clk    (clk),
        .reset  (beep_cnt_reset),
        .en     (beep_timer_done),
        .target (buzzer_mode),
        .done   (beeps_done)
    );

endmodule