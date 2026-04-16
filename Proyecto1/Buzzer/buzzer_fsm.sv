// =============================================================================
// buzzer_fsm — FSM one-hot del módulo buzzer
//
// Estados:
//   IDLE    [0] : espera activate_buz
//   BEEPING [1] : led encendido, contador de 1s corriendo
//   PAUSE   [2] : led apagado, contador de 0.5s corriendo
//   DONE    [3] : señaliza buzzer_done por 1 ciclo, regresa a IDLE
//
// Codificación one-hot: state[3:0]
//   IDLE=0001  BEEPING=0010  PAUSE=0100  DONE=1000
//
// Entradas:
//   clk, reset       : reloj y reset asíncrono activo alto
//   activate_buz     : activa la secuencia
//   buzzer_mode[1:0] : target de beeps (01=1, 10=2, 11=3)
//   beep_timer_done  : contador de 1s llegó al tope
//   pause_timer_done : contador de 0.5s llegó al tope
//   beeps_done       : beep_counter llegó al target
//
// Salidas Moore:
//   led              : encendido en BEEPING
//   buzzer_done      : alto en DONE
//   beep_timer_en    : habilita contador de 1s en BEEPING
//   pause_timer_en   : habilita contador de 0.5s en PAUSE
//   beep_timer_reset : resetea contador de 1s fuera de BEEPING
//   pause_timer_reset: resetea contador de 0.5s fuera de PAUSE
//   beep_cnt_reset   : resetea beep_counter en IDLE
// =============================================================================

module buzzer_fsm (
    input  logic        clk,
    input  logic        reset,
    input  logic        activate_buz,
    input  logic        beep_timer_done,
    input  logic        pause_timer_done,
    input  logic        beeps_done,
    output logic        led,
    output logic        buzzer_done,
    output logic        beep_timer_en,
    output logic        pause_timer_en,
    output logic        beep_timer_reset,
    output logic        pause_timer_reset,
    output logic        beep_cnt_reset
);

    // -------------------------------------------------------------------------
    // Localparams one-hot
    // -------------------------------------------------------------------------
    localparam integer IDLE    = 0;
    localparam integer BEEPING = 1;
    localparam integer PAUSE   = 2;
    localparam integer DONE    = 3;

    // -------------------------------------------------------------------------
    // Vector de estado
    // -------------------------------------------------------------------------
    logic [3:0] state;
    logic [3:0] next_state;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) state <= 4'b0001;
        else       state <= next_state;
    end

    // -------------------------------------------------------------------------
    // Lógica de siguiente estado
    // -------------------------------------------------------------------------
    assign next_state[IDLE]    = (state[IDLE]    & ~activate_buz)
                               | state[DONE];

    assign next_state[BEEPING] = (state[IDLE]    &  activate_buz)
                           | (state[PAUSE]   &  pause_timer_done)
                           | (state[BEEPING] & ~beep_timer_done);

    assign next_state[PAUSE]   = (state[BEEPING] &  beep_timer_done & ~beeps_done)
                           | (state[PAUSE]   & ~pause_timer_done);

    assign next_state[DONE]    =  state[BEEPING] &  beep_timer_done &  beeps_done;

    // -------------------------------------------------------------------------
    // Salidas Moore
    // -------------------------------------------------------------------------
    assign led               =  state[BEEPING];
    assign buzzer_done       =  state[DONE];
    assign beep_timer_en     =  state[BEEPING];
    assign pause_timer_en    =  state[PAUSE];

    // Resets de contadores: activos cuando NO están en su estado activo
    assign beep_timer_reset  = ~state[BEEPING] | reset;
    assign pause_timer_reset = ~state[PAUSE]   | reset;

    // beep_cnt_reset: activo en IDLE para que el contador arranque
    // limpio en cada nueva activación
    assign beep_cnt_reset    =  state[IDLE]    | reset;

endmodule