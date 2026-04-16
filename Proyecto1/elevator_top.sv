// =============================================================================
// elevator_top — Top level de la implementacion real del elevador en FPGA
//
// Diferencias con elevator_demo_top:
//   - mic_in     : sensor digital de sonido (reemplaza btn_clap + debounce)
//   - buzzer_out : buzzer activo (reemplaza LED simulado)
//   - motor_pwm  : PWM hacia ENA del H-bridge (velocidad)
//   - motor_in1  : IN1 del H-bridge (sube=1 baja=0 parado=0)
//   - motor_in2  : IN2 del H-bridge (sube=0 baja=1 parado=0)
//
// LEDs de debug (mismos que la demo):
//   led[0] : beep activo (mismo que buzzer_out)
//   led[1] : ventana de escucha activa (listening_led)
//   led[2] : aplauso registrado en la ventana de escucha
//   led[3] : mode_mic bit READBIT0 (010)
//   led[4] : mode_mic bit READBIT1 (011)
//   led[5] : mode_mic bit READBIT2 (100)
//   led[6] : mode_mic bit READBIT3 (101)
//
// Instancias:
//   u_fsm    : elevator_fsm — FSM principal (sin cambios)
//   u_mic    : mic_top      — logica de deteccion de aplausos
//   u_buzzer : buzzer_top   — generador de secuencias de beeps
//   u_alu    : ALU          — controlador de movimiento del elevador
//   u_pwm    : pwm_top      — generador PWM para velocidad del motor
// =============================================================================
module elevator_top #(
    parameter integer CLK_FREQ = 50_000_000
)(
    input  logic        clk,         // 50 MHz
    input  logic        reset,       // Boton reset activo LOW (KEY en DE1-SoC)
    input  logic        mic_in,      // Sensor digital de sonido (salida actual tratada como activa en LOW)
    output logic        buzzer_out,  // Buzzer activo (HIGH = beep)
    output logic        motor_pwm,   // PWM hacia ENA del H-bridge (velocidad)
    output logic        motor_in1,   // IN1 del H-bridge
    output logic        motor_in2,   // IN2 del H-bridge
    output logic [6:0]  led,         // LEDs de debug
    output logic [6:0]  hex0         // Display 7 segmentos — piso actual
);

    // -------------------------------------------------------------------------
    // Reset: boton activo LOW en DE1-SoC -> invertir a activo HIGH para logica
    // -------------------------------------------------------------------------
    logic reset_active;
    assign reset_active = ~reset;

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

    // -------------------------------------------------------------------------
    // Wires internos — mic_top -> ALU y motor
    // -------------------------------------------------------------------------
    logic        dir_reg;
    logic        clap_registered;
    logic [3:0]  num_reg;

    // -------------------------------------------------------------------------
    // Wire de retroalimentacion — ALU.piso_actual -> ALU.piso_init
    // -------------------------------------------------------------------------
    logic [3:0]  piso_actual;

    // -------------------------------------------------------------------------
    // Wire PWM — ALU.pwm_level -> pwm_top
    // -------------------------------------------------------------------------
    logic [2:0]  pwm_level;
    localparam int unsigned MIC_HOLDOFF_CYCLES = CLK_FREQ / 20;
    localparam int unsigned MIC_HOLDOFF_WIDTH  = $clog2(MIC_HOLDOFF_CYCLES + 1);

    // -------------------------------------------------------------------------
    // Acondicionamiento del microfono:
    //   - sincroniza la entrada asincrona a clk
    //   - convierte la salida activa baja del modulo en un pulso limpio
    //   - bloquea retriggers breves por vibracion/ruido del sensor
    // -------------------------------------------------------------------------
    logic mic_sync_0;
    logic mic_sync_1;
    logic mic_active;
    logic mic_active_prev;
    logic clap_pulse;
    logic mic_holdoff_active;
    logic [MIC_HOLDOFF_WIDTH-1:0] mic_holdoff_count;

    always_ff @(posedge clk or posedge reset_active) begin
        if (reset_active) begin
            mic_sync_0       <= 1'b1;
            mic_sync_1       <= 1'b1;
            mic_active_prev  <= 1'b0;
            mic_holdoff_count <= '0;
        end else begin
            mic_sync_0      <= mic_in;
            mic_sync_1      <= mic_sync_0;
            mic_active_prev <= mic_active;

            if (clap_pulse)
                mic_holdoff_count <= MIC_HOLDOFF_CYCLES[MIC_HOLDOFF_WIDTH-1:0];
            else if (mic_holdoff_active)
                mic_holdoff_count <= mic_holdoff_count - 1'b1;
        end
    end

    assign mic_active = ~mic_sync_1;
    assign mic_holdoff_active = (mic_holdoff_count != '0);
    assign clap_pulse = mic_active & ~mic_active_prev & ~mic_holdoff_active;

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
    // Microfono — entrada sincronizada y convertida a pulso unico por aplauso
    // -------------------------------------------------------------------------
    mic_top #(
        .CLK_FREQ_HZ   (CLK_FREQ),
        .LISTEN_TIME_MS(4000)
    ) u_mic (
        .clk          (clk),
        .reset        (reset_active),
        .activate_mic (activate_mic),
        .clap_event   (clap_pulse),
        .mode_mic     (mode_mic),
        .mic_done     (mic_done),
        .init_system  (init_system),
        .listening_led(led[1]),
        .clap_registered(clap_registered),
        .dir_reg      (dir_reg),
        .num_reg      (num_reg)
    );

    // -------------------------------------------------------------------------
    // Buzzer pasivo — buzzer_top entrega la onda cuadrada al pin S
    // led[0] refleja la misma señal para debug visual
    // -------------------------------------------------------------------------
    buzzer_top #(
        .BEEP_TARGET  (CLK_FREQ - 1),
        .PAUSE_TARGET (CLK_FREQ / 2 - 1),
        .ACTIVE_BUZZER(1'b0)
    ) u_buzzer (
        .clk         (clk),
        .reset       (reset_active),
        .activate_buz(activate_buz),
        .buzzer_mode (buzzer_mode),
        .led         (buzzer_out),
        .buzzer_done (buzzer_done)
    );

    assign led[0] = buzzer_out;

    // -------------------------------------------------------------------------
    // ALU — piso_init retroalimentado desde piso_actual
    // op: aplauso detectado (dir_reg=1) -> subir (op=0)
    //     sin aplauso         (dir_reg=0) -> bajar (op=1)
    // -------------------------------------------------------------------------
    ALU #(
        .CLK_FREQ(CLK_FREQ)
    ) u_alu (
        .clk        (clk),
        .reset      (reset_active),
        .piso_init  (piso_actual),
        .pisos_delta(num_reg),
        .load       (load),
        .op         (~dir_reg),
        .piso_actual(piso_actual),
        .pwm_level  (pwm_level),
        .seg        (hex0),
        .done       (done)
    );

    // -------------------------------------------------------------------------
    // PWM — convierte pwm_level[2:0] del ALU en señal PWM para el motor
    // rst_n es activo bajo: ~reset_active = reset (boton sin invertir)
    // -------------------------------------------------------------------------
    pwm_top u_pwm (
        .clk      (clk),
        .rst_n    (~reset_active),
        .pwm_level(pwm_level),
        .pwm_out  (motor_pwm)
    );

    // -------------------------------------------------------------------------
    // Control de direccion del motor via H-bridge (IN1/IN2)
    // motor_active: hay movimiento en curso (pwm_level != 0)
    // Subiendo (dir_reg=1): IN1=1, IN2=0
    // Bajando  (dir_reg=0): IN1=0, IN2=1
    // Parado   (pwm=000)  : IN1=0, IN2=0 (freno automatico)
    // -------------------------------------------------------------------------
    wire motor_active;
    assign motor_active = pwm_level[2] | pwm_level[1] | pwm_level[0];

    assign motor_in1 = motor_active &  dir_reg;
    assign motor_in2 = motor_active & ~dir_reg;

    // -------------------------------------------------------------------------
    // LEDs de debug
    // led[0] : buzzer_out (asignado junto al buzzer arriba)
    // led[1] : listening_led (asignado en u_mic arriba)
    // led[2] : aplauso registrado en el latch del microfono
    // led[3:6]: bits de modo del microfono para rastrear la lectura de bits
    // -------------------------------------------------------------------------
    assign led[2] = clap_registered;
    assign led[3] = ~mode_mic[2] & mode_mic[1] & ~mode_mic[0]; // READBIT0 (010)
    assign led[4] = ~mode_mic[2] & mode_mic[1] &  mode_mic[0]; // READBIT1 (011)
    assign led[5] =  mode_mic[2] & ~mode_mic[1] & ~mode_mic[0]; // READBIT2 (100)
    assign led[6] =  mode_mic[2] & ~mode_mic[1] &  mode_mic[0]; // READBIT3 (101)

endmodule
