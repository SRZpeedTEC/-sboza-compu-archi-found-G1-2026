// =============================================================================
// buzzer_top_tb — Testbench para buzzer_top
//
// Estrategia de simulación rápida:
//   Se pasan targets reducidos via parámetros del módulo:
//   BEEP_TARGET  = 10 ciclos
//   PAUSE_TARGET = 5  ciclos
//
// Casos de prueba:
//   1. Reset: led=0, buzzer_done=0
//   2. Sin activate_buz: permanece en IDLE
//   3. BEEP1 — 1 beep, verifica led encendido y buzzer_done al final
//   4. BEEP2 — 2 beeps con pausa entre ellos
//   5. BEEP3 — 3 beeps con pausas
// =============================================================================

`timescale 1ns/1ps

module buzzer_top_tb;

    // -------------------------------------------------------------------------
    // Señales
    // -------------------------------------------------------------------------
    localparam integer CLK_PERIOD  = 20;
    localparam integer BEEP_TARGET  = 10;
    localparam integer PAUSE_TARGET = 5;

    logic        clk;
    logic        reset;
    logic        activate_buz;
    logic [1:0]  buzzer_mode;
    logic        led;
    logic        buzzer_done;

    // -------------------------------------------------------------------------
    // DUT — targets reducidos para simulación rápida
    // -------------------------------------------------------------------------
    buzzer_top #(
        .BEEP_TARGET  (BEEP_TARGET),
        .PAUSE_TARGET (PAUSE_TARGET)
    ) dut (
        .clk         (clk),
        .reset       (reset),
        .activate_buz(activate_buz),
        .buzzer_mode (buzzer_mode),
        .led         (led),
        .buzzer_done (buzzer_done)
    );

    initial begin
    #1;
    $display("DEBUG: beep_timer target = %0d", dut.u_beep_timer.target);
    $display("DEBUG: pause_timer target = %0d", dut.u_pause_timer.target);
    end

    // -------------------------------------------------------------------------
    // Clock
    // -------------------------------------------------------------------------
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -------------------------------------------------------------------------
    // Tarea: reset del DUT
    // -------------------------------------------------------------------------
    task do_reset();
        reset = 1;
        @(posedge clk); #1;
        reset = 0;
        @(posedge clk); #1;
    endtask

    // -------------------------------------------------------------------------
    // Tarea: espera buzzer_done con timeout
    // -------------------------------------------------------------------------
    task wait_done(input integer timeout_cycles);
        integer i;
        for (i = 0; i < timeout_cycles; i++) begin
            @(posedge clk); #1;
            if (buzzer_done) begin
                $display("  buzzer_done=1 tras %0d ciclos", i+1);
                disable wait_done;
            end
        end
        $display("  FAIL: timeout esperando buzzer_done");
    endtask

    // -------------------------------------------------------------------------
    // Tarea: cuenta ciclos de led hasta buzzer_done o timeout
    // -------------------------------------------------------------------------
    integer led_cycles;

    task count_led_cycles(input integer max_cycles);
        integer i;
        led_cycles = 0;
        for (i = 0; i < max_cycles; i++) begin
            @(posedge clk); #1;
            if (led) led_cycles++;
            if (buzzer_done) disable count_led_cycles;
        end
    endtask

    // -------------------------------------------------------------------------
    // Stimulus
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("buzzer_top_tb.vcd");
        $dumpvars(0, buzzer_top_tb);

        // Inicialización
        reset        = 0;
        activate_buz = 0;
        buzzer_mode  = 2'b00;
        #1;
        reset = 1;

        // ---------------------------------------------------------------------
        // Caso 1: Reset — led=0, buzzer_done=0
        // ---------------------------------------------------------------------
        $display("=== Caso 1: Reset ===");
        @(posedge clk); #1;
        if (led !== 0 || buzzer_done !== 0)
            $display("FAIL: led=%b buzzer_done=%b esperados 0", led, buzzer_done);
        else
            $display("PASS: led=0 buzzer_done=0 tras reset");
        reset = 0;

        // ---------------------------------------------------------------------
        // Caso 2: Sin activate_buz — permanece en IDLE
        // ---------------------------------------------------------------------
        $display("=== Caso 2: Sin activate_buz permanece en IDLE ===");
        repeat(5) @(posedge clk); #1;
        if (led !== 0 || buzzer_done !== 0)
            $display("FAIL: led=%b buzzer_done=%b esperados 0 en IDLE", led, buzzer_done);
        else
            $display("PASS: permanece en IDLE sin activate_buz");

        // ---------------------------------------------------------------------
        // Caso 3: BEEP1 — 1 beep
        // ---------------------------------------------------------------------
        $display("=== Caso 3: BEEP1 — 1 beep ===");
        do_reset();
        buzzer_mode  = 2'b01;
        activate_buz = 1;

        @(posedge clk); #1;
        if (led !== 1)
            $display("FAIL: led=%b esperado 1 al entrar a BEEPING", led);
        else
            $display("PASS: led=1 al entrar a BEEPING");

        wait_done(BEEP_TARGET * 3);


        if (buzzer_done !== 1)
            $display("FAIL: buzzer_done=%b esperado 1", buzzer_done);
        else
            $display("PASS: BEEP1 completado correctamente");

        activate_buz = 0;
        @(posedge clk); #1;

        // ---------------------------------------------------------------------
        // Caso 4: BEEP2 — 2 beeps con pausa
        // ---------------------------------------------------------------------
        $display("=== Caso 4: BEEP2 — 2 beeps ===");
        do_reset();
        buzzer_mode  = 2'b10;
        activate_buz = 1;

        count_led_cycles((BEEP_TARGET + PAUSE_TARGET) * 4);

        if (led_cycles < BEEP_TARGET * 2)
            $display("FAIL: led encendido %0d ciclos, esperado >= %0d",
                     led_cycles, BEEP_TARGET * 2);
        else
            $display("PASS: led encendido %0d ciclos en BEEP2", led_cycles);

        if (buzzer_done !== 1)
            $display("FAIL: buzzer_done=%b esperado 1 al final de BEEP2", buzzer_done);
        else
            $display("PASS: BEEP2 completado correctamente");

        activate_buz = 0;
        @(posedge clk); #1;

        // ---------------------------------------------------------------------
        // Caso 5: BEEP3 — 3 beeps con pausas
        // ---------------------------------------------------------------------
        $display("=== Caso 5: BEEP3 — 3 beeps ===");
        do_reset();
        buzzer_mode  = 2'b11;
        activate_buz = 1;

        count_led_cycles((BEEP_TARGET + PAUSE_TARGET) * 6);

        if (led_cycles < BEEP_TARGET * 3)
            $display("FAIL: led encendido %0d ciclos, esperado >= %0d",
                     led_cycles, BEEP_TARGET * 3);
        else
            $display("PASS: led encendido %0d ciclos en BEEP3", led_cycles);

        if (buzzer_done !== 1)
            $display("FAIL: buzzer_done=%b esperado 1 al final de BEEP3", buzzer_done);
        else
            $display("PASS: BEEP3 completado correctamente");

        activate_buz = 0;

        $display("=== Testbench buzzer_top completo ===");
        $finish;
    end

endmodule