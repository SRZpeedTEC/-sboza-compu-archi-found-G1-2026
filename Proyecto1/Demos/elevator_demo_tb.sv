// =============================================================================
// tb_elevator_demo — Testbench del sistema completo del elevador
//
// Instancia todos los modulos con parametros reducidos para simulacion rapida.
// Verifica:
//   1. Reset inicial — IDLE, piso 1
//   2. Flujo completo primera iteracion — subir 3 pisos
//   3. Segunda iteracion — bajar 2 pisos, verifica retroalimentacion piso_init
//
// No modifica ningun modulo del diseño.
// =============================================================================
`timescale 1ns/1ps

module tb_elevator_demo;

    // -------------------------------------------------------------------------
    // Parametros reducidos para simulacion
    // -------------------------------------------------------------------------
    localparam integer CLK_FREQ      = 10000;
    localparam integer BEEP_TARGET   = 9999;
    localparam integer PAUSE_TARGET  = 4999;
    localparam integer LISTEN_TIME_MS = 2000;
    localparam integer CLK_PERIOD    = 20;

    // -------------------------------------------------------------------------
    // Señales del DUT
    // -------------------------------------------------------------------------
    logic        clk;
    logic        reset;
    logic        btn_clap;
    logic [3:0]  led;
    logic [6:0]  hex0;

    // -------------------------------------------------------------------------
    // Señales internas para observabilidad
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
    logic        dir_reg;
    logic [3:0]  num_reg;
    logic [3:0]  piso_actual;
    logic [2:0]  pwm_level_nc;

    // -------------------------------------------------------------------------
    // Instancia elevator_fsm
    // -------------------------------------------------------------------------
    elevator_fsm u_fsm (
        .clk         (clk),
        .reset       (reset),
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
    // Instancia mic_demo con parametros reducidos
    // -------------------------------------------------------------------------
    mic_demo #(
        .CLK_FREQ_HZ   (CLK_FREQ),
        .LISTEN_TIME_MS(LISTEN_TIME_MS),
        .DEBOUNCE_MS   (1)
    ) u_mic (
        .clk          (clk),
        .reset        (reset),
        .activate_mic (activate_mic),
        .mode_mic     (mode_mic),
        .btn_clap     (btn_clap),
        .mic_done     (mic_done),
        .init_system  (init_system),
        .listening_led(led[1]),
        .clap_led     (led[2]),
        .dir_reg      (dir_reg),
        .num_reg      (num_reg)
    );

    // -------------------------------------------------------------------------
    // Instancia buzzer_top con tiempos reducidos
    // -------------------------------------------------------------------------
    buzzer_top #(
        .BEEP_TARGET (BEEP_TARGET),
        .PAUSE_TARGET(PAUSE_TARGET)
    ) u_buzzer (
        .clk         (clk),
        .reset       (reset),
        .activate_buz(activate_buz),
        .buzzer_mode (buzzer_mode),
        .led         (led[0]),
        .buzzer_done (buzzer_done)
    );

    // -------------------------------------------------------------------------
    // Instancia ALU con CLK_FREQ reducido
    // -------------------------------------------------------------------------
    ALU #(
        .CLK_FREQ(CLK_FREQ)
    ) u_alu (
        .clk        (clk),
        .reset      (reset),
        .piso_init  (piso_actual),
        .pisos_delta(num_reg),
        .load       (load),
        .op         (dir_reg),
        .piso_actual(piso_actual),
        .pwm_level  (pwm_level_nc),
        .seg        (hex0),
        .done       (done)
    );

    assign led[3] = mic_done;

    // -------------------------------------------------------------------------
    // Generador de reloj
    // -------------------------------------------------------------------------
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -------------------------------------------------------------------------
    // Tarea: simular aplauso — pulso de btn_clap por 5 ciclos
    // -------------------------------------------------------------------------
    task clap();
        btn_clap = 1;
        repeat(12) @(posedge clk);
        btn_clap = 0;
        repeat(5) @(posedge clk);
    endtask

   // -------------------------------------------------------------------------
    // Tarea: esperar ventana de mic y aplaudir si corresponde
    // -------------------------------------------------------------------------
    task wait_and_clap(input logic [2:0] expected_mode, input logic do_clap);
        $display("[WC] Esperando mode_mic=%0b t=%0t", expected_mode, $time);
        wait(mode_mic === expected_mode);
        $display("[WC] Entrando mode_mic=%0b t=%0t", expected_mode, $time);
        if (do_clap) clap();
        wait(mode_mic !== expected_mode);
        @(posedge clk);
    endtask

    // -------------------------------------------------------------------------
    // Tarea: esperar buzzer_done
    // -------------------------------------------------------------------------
    task wait_buzzer_done();
        wait(buzzer_done === 1'b1 || $time > 49_000_000_000);
        @(posedge clk);
    endtask

    // -------------------------------------------------------------------------
    // Tarea: esperar done de ALU
    // -------------------------------------------------------------------------
    task wait_alu_done();
        // Sincronizar lectura con el reloj para evitar glitches combinacionales
        do begin
            @(posedge clk);
        end while (done !== 1'b1);
    endtask

    // -------------------------------------------------------------------------
    // Tarea: flujo completo de un comando
    //   op_clap  : 1=aplaudir en READOP (bajar), 0=no aplaudir (subir)
    //   bit3..0  : 1=aplaudir en ese READBIT, 0=no aplaudir
    // -------------------------------------------------------------------------
    
    task send_command(
        input logic op_clap,
        input logic bit3,
        input logic bit2,
        input logic bit1,
        input logic bit0
    );
        $display("[TB] Esperando BEEP1...");
        wait_buzzer_done();
        $display("[TB] READOP — op_clap=%0b", op_clap);
        wait_and_clap(3'b001, op_clap);
        $display("[TB] Esperando BEEP2...");
        wait_buzzer_done();
        $display("[TB] READBIT0 — bit=%0b", bit0);
        wait_and_clap(3'b010, bit0);
        @(posedge clk);
        $display("[TB] READBIT1 — bit=%0b", bit1);
        wait_and_clap(3'b011, bit1);
        @(posedge clk);
        $display("[TB] READBIT2 — bit=%0b", bit2);
        wait_and_clap(3'b100, bit2);
        @(posedge clk);
        $display("[TB] READBIT3 — bit=%0b", bit3);
        wait_and_clap(3'b101, bit3);
        @(posedge clk);
        $display("[TB] Esperando BEEP3...");
        wait_buzzer_done();
        $display("[TB] Esperando movimiento ALU...");
        wait_alu_done();
        $display("[TB] Movimiento completo — piso_actual=%0d", piso_actual);
    endtask
    // -------------------------------------------------------------------------
    // Estimulo principal
    // -------------------------------------------------------------------------
    initial begin
        $display("=== INICIO TESTBENCH ELEVADOR ===");

        // Reset
        btn_clap = 0;
        reset    = 1;
        repeat(4) @(posedge clk);
        reset = 0;
        @(posedge clk);

        $monitor("[MON] t=%0t num_reg=%b dir_reg=%b load=%b done=%b piso_actual=%0d",
         $time, num_reg, dir_reg, load, done, piso_actual);

        $display("[TB] Reset completo — piso_actual=%0d (esperado 1)", piso_actual);

        // -----------------------------------------------------------------
        // Iteracion 1: subir 3 pisos (desde piso 1 -> piso 4)
        // op=0 (no aplauso=subir), delta=0011 (3)
        // bit3=0 bit2=0 bit1=1 bit0=1
        // -----------------------------------------------------------------

        $display("[TB] === Iteracion 1: subir 3 pisos ===");
       $display("[TB] Aplauso inicial...");
        clap();
        repeat(10) @(posedge clk);
        $display("[TB] Post-clap — init_system=%b activate_mic=%b", init_system, activate_mic);

        send_command(
            .op_clap(0),
            .bit3(0), .bit2(0), .bit1(1), .bit0(1)
        );

        $display("[TB] Piso esperado: 4 — piso_actual: %0d", piso_actual);
        assert(piso_actual == 4) else $error("ERROR: piso esperado 4, obtenido %0d", piso_actual);

        // -----------------------------------------------------------------
        // Iteracion 2: bajar 2 pisos (desde piso 4 -> piso 2)
        // op=1 (aplauso=bajar), delta=0010 (2)
        // bit3=0 bit2=0 bit1=1 bit0=0
        // -----------------------------------------------------------------
        $display("[TB] === Iteracion 2: bajar 2 pisos ===");
        $display("[TB] Aplauso inicial...");
        clap();

        send_command(
            .op_clap(1),
            .bit3(0), .bit2(0), .bit1(1), .bit0(0)
        );

        $display("[TB] Piso esperado: 2 — piso_actual: %0d", piso_actual);
        assert(piso_actual == 2) else $error("ERROR: piso esperado 2, obtenido %0d", piso_actual);

        $display("=== TESTBENCH COMPLETADO ===");
        $finish;
    end

    // -------------------------------------------------------------------------
    // Timeout de seguridad — ajustar si la simulacion se corta antes
    // -------------------------------------------------------------------------
    initial begin
        #50_000_000;
        $display("TIMEOUT — simulacion detenida");
        $finish;
    end

endmodule