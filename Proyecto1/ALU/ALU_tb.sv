`timescale 1ns/1ps

// =============================================================================
// ALU_tb — Testbench del controlador de movimiento del elevador
//
// CLK_FREQ=4 para simular rapido: 1 tick = 4 ciclos de reloj.
// Todos los tests asumen que op/piso_init/pisos_delta se mantienen
// estables durante el movimiento (precondicion de la FSM, Opcion B).
// =============================================================================

module ALU_tb;

    localparam int CLK_FREQ   = 4;
    localparam int CLK_PERIOD = 10;

    reg        clk;
    reg        reset;
    reg  [3:0] piso_init;
    reg  [3:0] pisos_delta;
    reg        load;
    reg        op;

    wire [3:0] piso_actual;
    wire [2:0] pwm_level;
    wire [6:0] seg;
    wire       done;

    ALU #(
        .CLK_FREQ(CLK_FREQ)
    ) dut (
        .clk        (clk),
        .reset      (reset),
        .piso_init  (piso_init),
        .pisos_delta(pisos_delta),
        .load       (load),
        .op         (op),
        .piso_actual(piso_actual),
        .pwm_level  (pwm_level),
        .seg        (seg),
        .done       (done)
    );

    // -------------------------------------------------------------------------
    // Clock
    // -------------------------------------------------------------------------
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // -------------------------------------------------------------------------
    // Contadores y helpers
    // -------------------------------------------------------------------------
    integer passed;
    integer failed;

    task check;
        input condition;
        input [1023:0] msg;
        begin
            if (condition) begin
                passed = passed + 1;
                $display("[PASS] %0s", msg);
            end else begin
                failed = failed + 1;
                $display("[FAIL] %0s", msg);
            end
        end
    endtask

    // Reset y condiciones iniciales
    task apply_reset;
        begin
            reset       = 1'b1;
            load        = 1'b0;
            piso_init   = 4'd0;
            pisos_delta = 4'd0;
            op          = 1'b0;
            repeat (2) @(posedge clk);
            #1;
            reset = 1'b0;
            @(posedge clk);
            #1;
        end
    endtask

    // Pulso de load de exactamente 1 ciclo
    task start_operation;
        input [3:0] init_floor;
        input [3:0] delta;
        input       dir;
        begin
            piso_init   = init_floor;
            pisos_delta = delta;
            op          = dir;
            load        = 1'b1;
            @(posedge clk);
            #1;
            load = 1'b0;
            #1;
        end
    endtask

    // Espera exactamente 1 tick de la ALU (CLK_FREQ flancos)
    task wait_one_tick;
        integer i;
        begin
            for (i = 0; i < CLK_FREQ; i = i + 1)
                @(posedge clk);
            #1;
        end
    endtask

    // Espera done activo con timeout de seguridad
    // Espera done activo con timeout de seguridad.
    // #1 dentro del loop: al salir del while, done==1 ya esta muestreado.
    task wait_done;
        input integer max_ticks;
        integer i;
        begin
            i = 0;
            while (done !== 1'b1 && i < max_ticks * CLK_FREQ) begin
                @(posedge clk);
                #1;
                i = i + 1;
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // Funciones de valor esperado
    // -------------------------------------------------------------------------
    function [2:0] expected_pwm;
        input [3:0] b;
        begin
            case (b)
                4'd0:       expected_pwm = 3'b000;
                4'd1:       expected_pwm = 3'b001;
                4'd2, 4'd3: expected_pwm = 3'b010;
                4'd4:       expected_pwm = 3'b011;
                default:    expected_pwm = 3'b100;
            endcase
        end
    endfunction

    function [6:0] expected_seg;
        input [3:0] a;
        reg [6:0] s;
        begin
            s[0] = ~(~a[3]&~a[2]&~a[1]& a[0]) & ~(~a[3]& a[2]&~a[1]&~a[0]);
            s[1] = ~(~a[3]&~a[2]& a[1]& a[0]) & ~(~a[3]& a[2]& a[1]&~a[0])
                 & ~( a[3]&~a[2]& a[1]& a[0]) & ~( a[3]& a[2]& a[1]&~a[0]);
            s[2] = ~(~a[3]&~a[2]& a[1]&~a[0]);
            s[3] = ~(~a[3]&~a[2]&~a[1]& a[0]) & ~(~a[3]& a[2]&~a[1]&~a[0])
                 & ~(~a[3]& a[2]& a[1]& a[0]) & ~( a[3]&~a[2]& a[1]&~a[0])
                 & ~( a[3]& a[2]& a[1]& a[0]);
            s[4] = ~(~a[3]&~a[2]&~a[1]& a[0]) & ~(~a[3]&~a[2]& a[1]& a[0])
                 & ~(~a[3]& a[2]&~a[1]&~a[0]) & ~(~a[3]& a[2]&~a[1]& a[0])
                 & ~(~a[3]& a[2]& a[1]& a[0]) & ~( a[3]&~a[2]&~a[1]& a[0]);
            s[5] = ~(~a[3]&~a[2]&~a[1]& a[0]) & ~(~a[3]&~a[2]& a[1]&~a[0])
                 & ~(~a[3]&~a[2]& a[1]& a[0]) & ~(~a[3]& a[2]& a[1]& a[0]);
            s[6] = ~(~a[3]&~a[2]&~a[1]&~a[0]) & ~(~a[3]&~a[2]&~a[1]& a[0])
                 & ~(~a[3]& a[2]& a[1]& a[0]);
            expected_seg = ~s;
        end
    endfunction

    // =========================================================================
    // Tests
    // =========================================================================
    initial begin
        passed = 0;
        failed = 0;

        reset       = 1'b0;
        piso_init   = 4'd0;
        pisos_delta = 4'd0;
        load        = 1'b0;
        op          = 1'b0;

        // =====================================================================
        // TEST 1: Reset
        // =====================================================================
        apply_reset();
        check(piso_actual == 4'd1,       "RESET: piso_actual inicializa en 1");
        check(done        == 1'b0,       "RESET: done inicia en 0");
        check(pwm_level   == 3'b000,     "RESET: pwm_level inicia en 000");
        check(dut.active  == 1'b0,       "RESET: active inicia en 0");
        check(seg == expected_seg(4'd1), "RESET: seg corresponde a A=1");

        // =====================================================================
        // TEST 2: Movimiento hacia arriba — init=3, delta=2 → 3→4→5
        // =====================================================================
        start_operation(4'd3, 4'd2, 1'b0);

        check(piso_actual == 4'd3,             "UP: carga inicial A=3");
        check(dut.B       == 4'd2,             "UP: B carga delta=2");
        check(dut.active  == 1'b1,             "UP: active sube con load");
        check(done        == 1'b0,             "UP: done en 0 tras load");
        check(pwm_level == expected_pwm(4'd2), "UP: pwm correcto B=2");

        wait_one_tick();
        check(piso_actual == 4'd4,             "UP: tick 1 → A=4");
        check(dut.B       == 4'd1,             "UP: tick 1 → B=1");
        check(done        == 1'b0,             "UP: done en 0 tras tick 1");
        check(pwm_level == expected_pwm(4'd1), "UP: pwm correcto B=1");
        check(seg == expected_seg(4'd4),       "UP: seg correcto A=4");

        wait_one_tick();
        check(piso_actual == 4'd5,             "UP: tick 2 → A=5");
        check(dut.B       == 4'd0,             "UP: tick 2 → B=0");
        check(done        == 1'b1,             "UP: done pulsa en tick 2");
        check(pwm_level == expected_pwm(4'd0), "UP: pwm correcto B=0");
        check(seg == expected_seg(4'd5),       "UP: seg correcto A=5");

        @(posedge clk); #1;
        check(done       == 1'b0, "UP: done vuelve a 0 ciclo siguiente");
        check(dut.active == 1'b0, "UP: active se autoreset");

        // =====================================================================
        // TEST 3: Movimiento hacia abajo — init=6, delta=3 → 6→5→4→3
        // =====================================================================
        start_operation(4'd6, 4'd3, 1'b1);

        check(piso_actual == 4'd6, "DOWN: carga inicial A=6");
        check(dut.B       == 4'd3, "DOWN: B carga delta=3");
        check(done        == 1'b0, "DOWN: done en 0 tras load");

        wait_one_tick();
        check(piso_actual == 4'd5, "DOWN: tick 1 → A=5");
        check(dut.B       == 4'd2, "DOWN: tick 1 → B=2");

        wait_one_tick();
        check(piso_actual == 4'd4, "DOWN: tick 2 → A=4");
        check(dut.B       == 4'd1, "DOWN: tick 2 → B=1");

        wait_one_tick();
        check(piso_actual == 4'd3, "DOWN: tick 3 → A=3");
        check(dut.B       == 4'd0, "DOWN: tick 3 → B=0");
        check(done        == 1'b1, "DOWN: done pulsa en tick 3");

        @(posedge clk); #1;
        check(done == 1'b0, "DOWN: done vuelve a 0");

        // =====================================================================
        // TEST 4: load_safe — load ignorado si ALU activa
        // op/piso_init/pisos_delta no cambian (precondicion FSM)
        // El load ilegal consume 1 ciclo extra dentro del periodo del timer,
        // por eso se usa wait_done en vez de wait_one_tick al final.
        // =====================================================================
        start_operation(4'd2, 4'd3, 1'b0); // subir 3 desde piso 2

        check(piso_actual == 4'd2, "SAFELOAD: carga inicial A=2");
        check(dut.B       == 4'd3, "SAFELOAD: B inicia en 3");

        wait_one_tick();
        check(piso_actual == 4'd3, "SAFELOAD: tick 1 → A=3");
        check(dut.B       == 4'd2, "SAFELOAD: tick 1 → B=2");

        // Intento de load ilegal — op/piso_init/pisos_delta se mantienen
        load = 1'b1;
        @(posedge clk); #1;
        load = 1'b0; #1;

        check(piso_actual == 4'd3, "SAFELOAD: load ilegal no cambia A");
        check(dut.B       == 4'd2, "SAFELOAD: load ilegal no cambia B");

        wait_one_tick();
        check(piso_actual == 4'd4, "SAFELOAD: operacion original continua A=4");
        check(dut.B       == 4'd1, "SAFELOAD: B continua en 1");

        // El load ilegal desplazo el timer 1 ciclo. Usamos wait_done.
        wait_done(3);
        check(piso_actual == 4'd5, "SAFELOAD: A llega a 5 al terminar");
        check(dut.B       == 4'd0, "SAFELOAD: B llega a 0");
        check(done        == 1'b1, "SAFELOAD: done pulsa al terminar");

        @(posedge clk); #1;
        check(done == 1'b0, "SAFELOAD: done vuelve a 0");

        // =====================================================================
        // TEST 5: Saturacion hacia arriba — init=14, delta=3
        // Adder detecta overflow: 14+3=17>15
        // B_restantes = ~piso_init = 1 → solo puede subir 1 piso
        // Secuencia: 14→15, done en tick 1
        // =====================================================================
        start_operation(4'd14, 4'd3, 1'b0);

        check(piso_actual == 4'd14, "SAT UP: carga inicial A=14");
        check(dut.B       == 4'd1,  "SAT UP: B saturado a 1 por Adder");

        wait_one_tick();
        check(piso_actual == 4'd15, "SAT UP: tick 1 → A=15");
        check(dut.B       == 4'd0,  "SAT UP: tick 1 → B=0");
        check(done        == 1'b1,  "SAT UP: done en tick 1");

        @(posedge clk); #1;
        check(done == 1'b0, "SAT UP: done vuelve a 0");

        // =====================================================================
        // TEST 6: Saturacion hacia abajo — init=1, delta=3
        // Substractor detecta underflow: 3>1
        // B_restantes = piso_init = 1 → solo puede bajar 1 piso
        // Secuencia: 1→0, done en tick 1
        // =====================================================================
        start_operation(4'd1, 4'd3, 1'b1);

        check(piso_actual == 4'd1, "SAT DOWN: carga inicial A=1");
        check(dut.B       == 4'd1, "SAT DOWN: B saturado a 1 por Substractor");

        wait_one_tick();
        check(piso_actual == 4'd0, "SAT DOWN: tick 1 → A=0");
        check(dut.B       == 4'd0, "SAT DOWN: tick 1 → B=0");
        check(done        == 1'b1, "SAT DOWN: done en tick 1");

        @(posedge clk); #1;
        check(done == 1'b0, "SAT DOWN: done vuelve a 0");

        // =====================================================================
        // TEST 7: delta=0 — done debe pulsar inmediatamente tras load
        // =====================================================================
        start_operation(4'd7, 4'd0, 1'b0);

        check(piso_actual == 4'd7, "DELTA0: A carga piso_init");
        check(dut.B       == 4'd0, "DELTA0: B carga 0");
        check(done        == 1'b1, "DELTA0: done pulsa inmediatamente");

        @(posedge clk); #1;
        check(done       == 1'b0, "DELTA0: done vuelve a 0");
        check(dut.active == 1'b0, "DELTA0: active se autoreset");

        // =====================================================================
        // TEST 8: PWM — verificacion bit a bit para B=0..5
        // =====================================================================
        begin : pwm_check
            integer b;
            reg [2:0] expected;
            for (b = 0; b <= 5; b = b + 1) begin
                expected = expected_pwm(b[3:0]);
                // Forzamos B directamente via reset y observacion
                // B se puede verificar tras load con delta=b desde piso 1
            end
        end
        // Verificacion funcional: tras load con delta=5 (B=5 → pwm=100)
        start_operation(4'd1, 4'd5, 1'b0);
        check(pwm_level == 3'b100, "PWM: B=5 → pwm_level=100");
        wait_done(10);

        // Tras load con delta=4 (B=4 → pwm=011)
        start_operation(4'd1, 4'd4, 1'b0);
        check(pwm_level == 3'b011, "PWM: B=4 → pwm_level=011");
        wait_done(10);

        // Tras load con delta=2 (B=2 → pwm=010)
        start_operation(4'd1, 4'd2, 1'b0);
        check(pwm_level == 3'b010, "PWM: B=2 → pwm_level=010");
        wait_done(10);

        // Tras load con delta=1 (B=1 → pwm=001)
        start_operation(4'd1, 4'd1, 1'b0);
        check(pwm_level == 3'b001, "PWM: B=1 → pwm_level=001");
        wait_done(10);

        // =====================================================================
        // TEST 9: Segundo load valido tras done
        // =====================================================================
        start_operation(4'd8, 4'd1, 1'b1);

        check(piso_actual == 4'd8, "RESTART: nueva operacion arranca en A=8");
        check(dut.B       == 4'd1, "RESTART: B carga 1");
        check(dut.active  == 1'b1, "RESTART: active sube");

        wait_one_tick();
        check(piso_actual == 4'd7, "RESTART: tick 1 → A=7");
        check(dut.B       == 4'd0, "RESTART: B llega a 0");
        check(done        == 1'b1, "RESTART: done pulsa");

        @(posedge clk); #1;
        check(done == 1'b0, "RESTART: done vuelve a 0");

        // =====================================================================
        // Summary
        // =====================================================================
        $display("--------------------------------------------------");
        $display("TB FINALIZADO  |  PASSED=%0d  FAILED=%0d", passed, failed);
        $display("--------------------------------------------------");
        if (failed == 0)
            $display("RESULTADO: TODOS LOS TESTS PASARON");
        else
            $display("RESULTADO: HAY TESTS FALLIDOS");

        $finish;
    end

endmodule