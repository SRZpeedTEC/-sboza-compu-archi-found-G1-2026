// =============================================================================
// beep_counter_tb — Testbench para beep_counter
//
// Casos de prueba:
//   1. Reset: done=0 con target=11
//   2. Target=01 (1 beep): done=1 durante el 1er pulso de en
//   3. Target=10 (2 beeps): done=0 en 1er pulso, done=1 en 2do pulso
//   4. Target=11 (3 beeps): done=0 en 1er y 2do pulso, done=1 en 3er pulso
//   5. Reset a mitad de secuencia
// =============================================================================

`timescale 1ns/1ps

module beep_counter_tb;

    // -------------------------------------------------------------------------
    // Señales
    // -------------------------------------------------------------------------
    localparam integer WIDTH      = 2;
    localparam integer CLK_PERIOD = 20;

    logic             clk;
    logic             reset;
    logic             en;
    logic [WIDTH-1:0] target;
    logic             done;

    // -------------------------------------------------------------------------
    // DUT
    // -------------------------------------------------------------------------
    beep_counter #(.WIDTH(WIDTH)) dut (
        .clk    (clk),
        .reset  (reset),
        .en     (en),
        .target (target),
        .done   (done)
    );

    // -------------------------------------------------------------------------
    // Clock
    // -------------------------------------------------------------------------
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -------------------------------------------------------------------------
    // Tarea: genera pulso de en y captura done durante ese pulso
    // done es válido combinacionalmente mientras en=1
    // -------------------------------------------------------------------------
    logic done_captured;

    task pulse_en_and_capture();
        @(negedge clk);       // bajada: punto estable para manejar señales
        en = 1;               // sube en
        #1;                   // pequeño delta para que combinacional se propague
        done_captured = done; // capturamos done mientras en=1
        @(negedge clk);       // siguiente bajada
        en = 0;               // baja en
    endtask

    // -------------------------------------------------------------------------
    // Tarea: reset del DUT
    // -------------------------------------------------------------------------
    task do_reset();
        reset = 1;
        en    = 0;
        @(posedge clk); #1;
        reset = 0;
    endtask

    // -------------------------------------------------------------------------
    // Stimulus
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("beep_counter_tb.vcd");
        $dumpvars(0, beep_counter_tb);

        // Inicialización — generamos flanco posedge reset
        reset  = 0;
        en     = 0;
        target = 2'b11;  // target != 0 para caso 1 válido
        #1;
        reset  = 1;

        // ---------------------------------------------------------------------
        // Caso 1: Reset — done=0 porque count=0 != target=11
        // ---------------------------------------------------------------------
        $display("=== Caso 1: Reset ===");
        @(posedge clk); #1;
        if (done !== 1'b0)
            $display("FAIL: done=%b esperado 0 durante reset", done);
        else
            $display("PASS: done=0 durante reset");
        reset = 0;

        // ---------------------------------------------------------------------
        // Caso 2: Target=01 (1 beep)
        // done debe ser 1 durante el 1er pulso de en
        // ---------------------------------------------------------------------
        $display("=== Caso 2: Target=01 (1 beep) ===");
        do_reset();
        target = 2'b01;

        pulse_en_and_capture();
        if (done_captured !== 1'b1)
            $display("FAIL: done=%b esperado 1 durante 1er pulso con target=01", done_captured);
        else
            $display("PASS: done=1 durante 1er pulso con target=01");

        // ---------------------------------------------------------------------
        // Caso 3: Target=10 (2 beeps)
        // ---------------------------------------------------------------------
        $display("=== Caso 3: Target=10 (2 beeps) ===");
        do_reset();
        target = 2'b10;

        pulse_en_and_capture();
        if (done_captured !== 1'b0)
            $display("FAIL: done=%b esperado 0 durante 1er pulso con target=10", done_captured);
        else
            $display("PASS: done=0 durante 1er pulso con target=10");

        pulse_en_and_capture();
        if (done_captured !== 1'b1)
            $display("FAIL: done=%b esperado 1 durante 2do pulso con target=10", done_captured);
        else
            $display("PASS: done=1 durante 2do pulso con target=10");

        // ---------------------------------------------------------------------
        // Caso 4: Target=11 (3 beeps)
        // ---------------------------------------------------------------------
        $display("=== Caso 4: Target=11 (3 beeps) ===");
        do_reset();
        target = 2'b11;

        pulse_en_and_capture();
        if (done_captured !== 1'b0)
            $display("FAIL: done=%b esperado 0 durante 1er pulso con target=11", done_captured);
        else
            $display("PASS: done=0 durante 1er pulso con target=11");

        pulse_en_and_capture();
        if (done_captured !== 1'b0)
            $display("FAIL: done=%b esperado 0 durante 2do pulso con target=11", done_captured);
        else
            $display("PASS: done=0 durante 2do pulso con target=11");

        pulse_en_and_capture();
        if (done_captured !== 1'b1)
            $display("FAIL: done=%b esperado 1 durante 3er pulso con target=11", done_captured);
        else
            $display("PASS: done=1 durante 3er pulso con target=11");

        // ---------------------------------------------------------------------
        // Caso 5: Reset a mitad de secuencia
        // ---------------------------------------------------------------------
        $display("=== Caso 5: Reset a mitad de secuencia ===");
        do_reset();
        target = 2'b11;

        pulse_en_and_capture(); // beep 1
        pulse_en_and_capture(); // beep 2

        // Reset antes del 3er beep
        reset = 1;
        @(posedge clk); #1;
        if (done !== 1'b0)
            $display("FAIL: done=%b esperado 0 tras reset a mitad", done);
        else
            $display("PASS: done=0 tras reset a mitad de secuencia");
        reset = 0;

        $display("=== Testbench beep_counter completo ===");
        $finish;
    end

endmodule