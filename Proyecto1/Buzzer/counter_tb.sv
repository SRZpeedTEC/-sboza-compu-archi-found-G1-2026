// =============================================================================
// counter_tb — Testbench para counter
//
// Casos de prueba:
//   1. Reset asíncrono: done=0, count=0
//   2. Cuenta hasta target=10, verifica done en ciclo correcto
//   3. Auto-congelado: ciclos extra con en=1 no modifican count
//   4. En=0: contador no avanza
// =============================================================================

`timescale 1ns/1ps

module counter_tb;

    // -------------------------------------------------------------------------
    // Señales
    // -------------------------------------------------------------------------
    localparam integer WIDTH  = 4;
    localparam integer TARGET = 10;
    localparam integer CLK_PERIOD = 20; // 50 MHz

    logic             clk;
    logic             reset;
    logic             en;
    logic [WIDTH-1:0] target;
    logic             done;

    // -------------------------------------------------------------------------
    // DUT
    // -------------------------------------------------------------------------
    counter #(.WIDTH(WIDTH)) dut (
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
    // Stimulus
    // -------------------------------------------------------------------------
    integer i;

    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);

        // Inicialización
        reset  = 1;
        en     = 0;
        target = WIDTH'(TARGET);

        // ---------------------------------------------------------------------
        // Caso 1: Reset asíncrono
        // ---------------------------------------------------------------------
        @(posedge clk); #1;
        $display("=== Caso 1: Reset asíncrono ===");
        if (done !== 1'b0)
            $display("FAIL: done=%b esperado 0", done);
        else
            $display("PASS: done=0 durante reset");

        // ---------------------------------------------------------------------
        // Caso 2: Cuenta hasta target
        // ---------------------------------------------------------------------
        $display("=== Caso 2: Cuenta hasta target=%0d ===", TARGET);
        reset = 0;
        en    = 1;

        // Esperamos TARGET+1 ciclos (de 0 a TARGET inclusive)
        for (i = 0; i <= TARGET; i++) begin
            @(posedge clk); #1;
            $display("  ciclo %0d: done=%b", i, done);
        end

        if (done !== 1'b1)
            $display("FAIL: done=%b esperado 1 al llegar a target", done);
        else
            $display("PASS: done=1 al llegar a target=%0d", TARGET);

        // ---------------------------------------------------------------------
        // Caso 3: Auto-congelado (5 ciclos extra con en=1)
        // ---------------------------------------------------------------------
        $display("=== Caso 3: Auto-congelado ===");
        for (i = 0; i < 5; i++) begin
            @(posedge clk); #1;
            if (done !== 1'b1)
                $display("FAIL ciclo extra %0d: done=%b esperado 1", i, done);
        end
        $display("PASS: done se mantiene en 1 tras %0d ciclos extra", 5);

        // ---------------------------------------------------------------------
        // Caso 4: Reset libera el contador
        // ---------------------------------------------------------------------
        $display("=== Caso 4: Reset libera contador ===");
        reset = 1;
        @(posedge clk); #1;
        if (done !== 1'b0)
            $display("FAIL: done=%b esperado 0 tras reset", done);
        else
            $display("PASS: done=0 tras reset");

        // ---------------------------------------------------------------------
        // Caso 5: en=0 no avanza
        // ---------------------------------------------------------------------
        $display("=== Caso 5: en=0 no avanza ===");
        reset = 0;
        en    = 0;
        for (i = 0; i < 5; i++) begin
            @(posedge clk); #1;
        end
        if (done !== 1'b0)
            $display("FAIL: done=%b esperado 0 con en=0", done);
        else
            $display("PASS: contador no avanza con en=0");

        $display("=== Testbench counter completo ===");
        $finish;
    end

endmodule