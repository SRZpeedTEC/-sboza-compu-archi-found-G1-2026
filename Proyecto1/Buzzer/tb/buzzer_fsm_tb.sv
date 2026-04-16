// =============================================================================
// buzzer_fsm_tb — Testbench para buzzer_fsm
//
// Estrategia: estimulamos las señales done de los contadores manualmente
// para verificar las transiciones sin instanciar los contadores reales.
// Verificamos salidas Moore en cada estado y transiciones correctas.
// =============================================================================

`timescale 1ns/1ps

module buzzer_fsm_tb;

    // -------------------------------------------------------------------------
    // Señales
    // -------------------------------------------------------------------------
    localparam integer CLK_PERIOD = 20;

    logic clk;
    logic reset;
    logic activate_buz;
    logic beep_timer_done;
    logic pause_timer_done;
    logic beeps_done;
    logic led;
    logic buzzer_done;
    logic beep_timer_en;
    logic pause_timer_en;
    logic beep_timer_reset;
    logic pause_timer_reset;
    logic beep_cnt_reset;

    // -------------------------------------------------------------------------
    // DUT
    // -------------------------------------------------------------------------
    buzzer_fsm dut (
        .clk              (clk),
        .reset            (reset),
        .activate_buz     (activate_buz),
        .beep_timer_done  (beep_timer_done),
        .pause_timer_done (pause_timer_done),
        .beeps_done       (beeps_done),
        .led              (led),
        .buzzer_done      (buzzer_done),
        .beep_timer_en    (beep_timer_en),
        .pause_timer_en   (pause_timer_en),
        .beep_timer_reset (beep_timer_reset),
        .pause_timer_reset(pause_timer_reset),
        .beep_cnt_reset   (beep_cnt_reset)
    );

    // -------------------------------------------------------------------------
    // Clock
    // -------------------------------------------------------------------------
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -------------------------------------------------------------------------
    // Tarea: verificar salidas Moore en estado IDLE
    // -------------------------------------------------------------------------
    task check_idle();
        if (led !== 0 || buzzer_done !== 0 || beep_timer_en !== 0 || pause_timer_en !== 0)
            $display("FAIL IDLE: salidas incorrectas led=%b buzzer_done=%b beep_timer_en=%b pause_timer_en=%b",
                     led, buzzer_done, beep_timer_en, pause_timer_en);
        else
            $display("PASS IDLE: todas las salidas en 0");
    endtask

    // -------------------------------------------------------------------------
    // Tarea: verificar salidas Moore en estado BEEPING
    // -------------------------------------------------------------------------
    task check_beeping();
        if (led !== 1 || buzzer_done !== 0 || beep_timer_en !== 1 || pause_timer_en !== 0)
            $display("FAIL BEEPING: salidas incorrectas led=%b buzzer_done=%b beep_timer_en=%b pause_timer_en=%b",
                     led, buzzer_done, beep_timer_en, pause_timer_en);
        else
            $display("PASS BEEPING: led=1 beep_timer_en=1");
    endtask

    // -------------------------------------------------------------------------
    // Tarea: verificar salidas Moore en estado PAUSE
    // -------------------------------------------------------------------------
    task check_pause();
        if (led !== 0 || buzzer_done !== 0 || beep_timer_en !== 0 || pause_timer_en !== 1)
            $display("FAIL PAUSE: salidas incorrectas led=%b buzzer_done=%b beep_timer_en=%b pause_timer_en=%b",
                     led, buzzer_done, beep_timer_en, pause_timer_en);
        else
            $display("PASS PAUSE: pause_timer_en=1");
    endtask

    // -------------------------------------------------------------------------
    // Tarea: verificar salidas Moore en estado DONE
    // -------------------------------------------------------------------------
    task check_done();
        if (led !== 0 || buzzer_done !== 1 || beep_timer_en !== 0 || pause_timer_en !== 0)
            $display("FAIL DONE: salidas incorrectas led=%b buzzer_done=%b beep_timer_en=%b pause_timer_en=%b",
                     led, buzzer_done, beep_timer_en, pause_timer_en);
        else
            $display("PASS DONE: buzzer_done=1");
    endtask

    // -------------------------------------------------------------------------
    // Tarea: reset del DUT
    // -------------------------------------------------------------------------
    task do_reset();
        reset = 1;
        @(posedge clk); #1;
        reset = 0;
    endtask

    // -------------------------------------------------------------------------
    // Tarea: simula un beep completo
    //   - Levanta beep_timer_done por 1 ciclo
    //   - beeps_done indica si es el ultimo beep
    // -------------------------------------------------------------------------
    task do_beep(input logic is_last);
        beep_timer_done = 0;
        beeps_done      = is_last;
        @(negedge clk);
        beep_timer_done = 1;
        @(posedge clk); #1;
        beep_timer_done = 0;
    endtask

    // -------------------------------------------------------------------------
    // Tarea: simula una pausa completa
    // -------------------------------------------------------------------------
    task do_pause();
        pause_timer_done = 0;
        @(negedge clk);
        pause_timer_done = 1;
        @(posedge clk); #1;
        pause_timer_done = 0;
    endtask

    // -------------------------------------------------------------------------
    // Stimulus
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("buzzer_fsm_tb.vcd");
        $dumpvars(0, buzzer_fsm_tb);

        // Inicialización
        reset            = 0;
        activate_buz     = 0;
        beep_timer_done  = 0;
        pause_timer_done = 0;
        beeps_done       = 0;
        #1;
        reset = 1;

        // ---------------------------------------------------------------------
        // Caso 1: Reset arranca en IDLE con salidas correctas
        // ---------------------------------------------------------------------
        $display("=== Caso 1: Reset arranca en IDLE ===");
        @(posedge clk); #1;
        check_idle();
        reset = 0;

        // ---------------------------------------------------------------------
        // Caso 2: activate_buz=0 se queda en IDLE
        // ---------------------------------------------------------------------
        $display("=== Caso 2: activate_buz=0 permanece en IDLE ===");
        repeat(3) @(posedge clk); #1;
        check_idle();

        // ---------------------------------------------------------------------
        // Caso 3: BEEP1 — 1 beep, transita a DONE y regresa a IDLE
        // ---------------------------------------------------------------------
        $display("=== Caso 3: BEEP1 — 1 beep ===");
        do_reset();

        // IDLE → BEEPING
        @(negedge clk);
        activate_buz = 1;
        @(posedge clk); #1;
        $display("  Tras activate_buz:");
        check_beeping();

        // BEEPING → DONE (es el ultimo beep)
        do_beep(1'b1);
        $display("  Tras beep completo (ultimo):");
        check_done();

        // DONE → IDLE
        @(posedge clk); #1;
        activate_buz = 0;
        $display("  Tras ciclo de DONE:");
        check_idle();

        // ---------------------------------------------------------------------
        // Caso 4: BEEP2 — 2 beeps con pausa
        // ---------------------------------------------------------------------
        $display("=== Caso 4: BEEP2 — 2 beeps ===");
        do_reset();

        // IDLE → BEEPING
        @(negedge clk);
        activate_buz = 1;
        @(posedge clk); #1;
        check_beeping();

        // BEEPING → PAUSE (no es el ultimo beep)
        do_beep(1'b0);
        $display("  Tras 1er beep (no ultimo):");
        check_pause();

        // PAUSE → BEEPING
        do_pause();
        $display("  Tras pausa:");
        check_beeping();

        // BEEPING → DONE (es el ultimo beep)
        do_beep(1'b1);
        $display("  Tras 2do beep (ultimo):");
        check_done();

        // DONE → IDLE
        @(posedge clk); #1;
        activate_buz = 0;
        check_idle();

        // ---------------------------------------------------------------------
        // Caso 5: BEEP3 — 3 beeps con pausas
        // ---------------------------------------------------------------------
        $display("=== Caso 5: BEEP3 — 3 beeps ===");
        do_reset();

        // IDLE → BEEPING
        @(negedge clk);
        activate_buz = 1;
        @(posedge clk); #1;
        check_beeping();

        // 1er beep → PAUSE
        do_beep(1'b0);
        $display("  Tras 1er beep:");
        check_pause();

        // PAUSE → BEEPING
        do_pause();
        check_beeping();

        // 2do beep → PAUSE
        do_beep(1'b0);
        $display("  Tras 2do beep:");
        check_pause();

        // PAUSE → BEEPING
        do_pause();
        check_beeping();

        // 3er beep → DONE
        do_beep(1'b1);
        $display("  Tras 3er beep (ultimo):");
        check_done();

        // DONE → IDLE
        @(posedge clk); #1;
        activate_buz = 0;
        check_idle();

        $display("=== Testbench buzzer_fsm completo ===");
        $finish;
    end

endmodule