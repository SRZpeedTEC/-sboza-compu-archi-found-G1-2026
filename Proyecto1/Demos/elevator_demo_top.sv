// =============================================================================
// elevator_demo_top — Top level de la demo del elevador en FPGA
//
// Instancias:
//   u_fsm      : elevator_fsm — FSM principal
//   u_mic      : mic_demo     — mic con boton y debounce
//   u_buzzer   : buzzer_top   — buzzer simulado con LED
//   u_alu      : ALU          — controlador de movimiento
//
// Puertos fisicos:
//   clk        : reloj 50MHz
//   reset      : boton reset activo alto
//   btn_clap   : boton simula aplauso
//   led[3:0]   : LEDs de estado
//   hex0[6:0]  : display 7 segmentos piso actual
// =============================================================================
module elevator_demo_top #(
    parameter integer CLK_FREQ = 50_000_000
)(
    input  logic        clk,
    input  logic        reset,
    input  logic        btn_clap,
    output logic [6:0]  led,
    output logic [6:0]  hex0
);

    // -------------------------------------------------------------------------
    // Wires internos — FSM <-> modulos
    // -------------------------------------------------------------------------
    logic        activate_mic;
    logic [2:0]  mode_mic;
    logic        activate_buz;
    logic [1:0]  buzzer_mode;
    logic        load;
    logic        mic_done;
    logic        init_system;
    logic        buzzer_done;
    logic        done;
	 
	 logic btn_clap_active;
	logic reset_active;

	assign btn_clap_active = ~btn_clap;
	assign reset_active    = ~reset;

    // -------------------------------------------------------------------------
    // Wires internos — mic_demo -> ALU
    // -------------------------------------------------------------------------
    logic        dir_reg;
    logic [3:0]  num_reg;

    // -------------------------------------------------------------------------
    // Wire de retroalimentacion — ALU.piso_actual -> ALU.piso_init
    // -------------------------------------------------------------------------
    logic [3:0]  piso_actual;

    // -------------------------------------------------------------------------
    // Wires no utilizados en demo
    // -------------------------------------------------------------------------
    logic [2:0]  pwm_level_nc;

    // -------------------------------------------------------------------------
    // FSM principal
    // -------------------------------------------------------------------------
    elevator_fsm u_fsm (
        .clk         (clk),
        .reset       (reset_active),
        .init_system (init_system),
        .mic_done    (mic_done),
        .buzzer_done (buzzer_done),
        .done        (done),
        .activate_mic(activate_mic),
        .mode_mic    (mode_mic),
        .activate_buz(activate_buz),
        .buzzer_mode (buzzer_mode),
        .load        (load)
    );

    // -------------------------------------------------------------------------
    // Mic demo — boton + debounce + mic_top
    // -------------------------------------------------------------------------
    mic_demo #(
        .CLK_FREQ_HZ   (CLK_FREQ),
        .LISTEN_TIME_MS(4000),
        .DEBOUNCE_MS   (20)
    ) u_mic (
        .clk         (clk),
        .reset       (reset_active),
        .activate_mic(activate_mic),
        .mode_mic    (mode_mic),
        .btn_clap    (btn_clap_active),
        .mic_done    (mic_done),
        .init_system (init_system),
        .listening_led(led[1]),
        .clap_led    (led[2]),
        .dir_reg     (dir_reg),
        .num_reg     (num_reg)
    );

    // -------------------------------------------------------------------------
    // Buzzer simulado con LED
    // -------------------------------------------------------------------------
    buzzer_top #(
        .BEEP_TARGET (CLK_FREQ - 1),
        .PAUSE_TARGET(CLK_FREQ / 2 - 1)
    ) u_buzzer (
        .clk        (clk),
        .reset      (reset_active),
        .activate_buz(activate_buz),
        .buzzer_mode(buzzer_mode),
        .led        (led[0]),
        .buzzer_done(buzzer_done)
    );

    // -------------------------------------------------------------------------
    // ALU — piso_init retroalimentado desde piso_actual
    // -------------------------------------------------------------------------
    ALU #(
        .CLK_FREQ(CLK_FREQ)
    ) u_alu (
        .clk        (clk),
        .reset      (reset_active),
        .piso_init  (piso_actual),
        .pisos_delta(num_reg),
        .load       (load),
        .op(~dir_reg), // aplauso=1 -> subir (op=0), sin aplauso -> bajar (op=1)
        .piso_actual(piso_actual),
        .pwm_level  (pwm_level_nc),
        .seg        (hex0),
        .done       (done)
    );

    // -------------------------------------------------------------------------
    // LED[3] — mic_done
    // -------------------------------------------------------------------------
	 assign led[3] = ~mode_mic[2] & mode_mic[1] & ~mode_mic[0]; // READBIT0 — LSB  (010)
	 assign led[4] = ~mode_mic[2] & mode_mic[1] &  mode_mic[0]; // READBIT1        (011)
	 assign led[5] =  mode_mic[2] & ~mode_mic[1] & ~mode_mic[0]; // READBIT2       (100)
	 assign led[6] =  mode_mic[2] & ~mode_mic[1] &  mode_mic[0]; // READBIT3 — MSB (101)

endmodule