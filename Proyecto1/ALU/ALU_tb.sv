`timescale 1ns/1ps

// Testbench para ALU con timer de 1 segundo y output 'done'
// CLK_FREQ=10 → tick cada 10 ciclos de clk = 100 ns (simulacion rapida)

module tb_alu_ascensor;
    reg        clk, rst_n, load, op;
    reg  [3:0] piso_init, pisos_delta;
    wire [6:0] seg;
    wire [3:0] piso_actual;
    wire [2:0] pwm_level;
    wire       done;

    // Instancia con CLK_FREQ pequeno para simulacion (tick cada 100 ns)
    ALU #(.CLK_FREQ(10)) dut (
        .clk(clk), .rst_n(rst_n),
        .piso_init(piso_init), .pisos_delta(pisos_delta),
        .load(load), .op(op),
        .piso_actual(piso_actual),
        .pwm_level(pwm_level),
        .seg(seg),
        .done(done)
    );

    always #5 clk = ~clk;

    function automatic [7:0] hex_char;
        input [3:0] val;
        case (val)
            4'h0: hex_char = "0";  4'h1: hex_char = "1";
            4'h2: hex_char = "2";  4'h3: hex_char = "3";
            4'h4: hex_char = "4";  4'h5: hex_char = "5";
            4'h6: hex_char = "6";  4'h7: hex_char = "7";
            4'h8: hex_char = "8";  4'h9: hex_char = "9";
            4'hA: hex_char = "A";  4'hB: hex_char = "B";
            4'hC: hex_char = "C";  4'hD: hex_char = "D";
            4'hE: hex_char = "E";  4'hF: hex_char = "F";
        endcase
    endfunction

    function automatic [6:0] pwm_pct;
        input [2:0] lvl;
        case (lvl)
            3'b000: pwm_pct = 7'd0;
            3'b001: pwm_pct = 7'd25;
            3'b010: pwm_pct = 7'd50;
            3'b011: pwm_pct = 7'd75;
            3'b100: pwm_pct = 7'd100;
            default: pwm_pct = 7'd0;
        endcase
    endfunction

    task automatic print_state;
        input [3:0] piso;
        input [2:0] lvl;
        input [6:0] segmentos;
        input       direccion;
        input       done_sig;
        reg [6:0] pct;
        reg [7:0] c;
        begin
            pct = pwm_pct(lvl);
            c   = hex_char(piso);
            $display("| Piso: %2d (hex: %s) | Dir: %s | PWM: %3d%% (%03b) | seg: %b | done: %b |",
                     piso, c,
                     direccion ? "BAJA" : "SUBE",
                     pct, lvl, segmentos, done_sig);
        end
    endtask

    // Imprime SOLO cuando piso_actual o done cambian (un estado por paso)
    // Evita la repeticion causada por el timer interno (CLK_FREQ ciclos por tick)
    reg [3:0] piso_prev;
    reg       done_prev;

    always @(posedge clk) begin
        if (~rst_n) begin
            piso_prev <= 4'hF;   // valor imposible para forzar primer print
            done_prev <= 1'b1;
        end else if (piso_actual !== piso_prev || done !== done_prev) begin
            print_state(piso_actual, pwm_level, seg, op, done);
            piso_prev <= piso_actual;
            done_prev <= done;
        end
    end

    // espera_ns como integer para soportar tiempos mayores
    task automatic do_test;
        input [3:0]  p_init;
        input [3:0]  p_delta;
        input        direccion;
        input [3:0]  esperado;
        input integer espera_ns;
        begin
            piso_init   = p_init;
            pisos_delta = p_delta;
            op          = direccion;
            #10 load = 1;
            #10 load = 0;
            #(espera_ns);
            $display("|----------------------------------------------------------------------|");
            $display("Resultado: %2d | Esperado: %2d | done: %b | %s\n",
                     piso_actual, esperado, done,
                     (piso_actual == esperado) ? "PASS" : "FAIL");
        end
    endtask

    initial begin
        $dumpfile("sim.vcd");
        $dumpvars(0, tb_alu_ascensor);

        clk = 0; rst_n = 0; load = 0; op = 0;
        piso_init = 0; pisos_delta = 0;
        #12 rst_n = 1;

        // Con CLK_FREQ=10 cada tick = 100 ns
        // Espera = pasos * 100 ns + 150 ns de margen

        // ==== SUBIR (op=0) ====
        $display("\n=== SUBE: piso 3 + 5 → esperado 8 (5 pasos x 100ns = 650ns total) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd3, 4'd5, 1'b0, 4'd8, 650);

        $display("=== SUBE: piso 13 + 5 → satura en 15 (B efectivo = 2, 350ns total) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd13, 4'd5, 1'b0, 4'd15, 350);

        $display("=== SUBE: piso 1 + 1 → piso 2 (1 paso, 250ns total) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd1, 4'd1, 1'b0, 4'd2, 250);

        $display("=== SUBE: piso 15 + 3 → ya en maximo (B efectivo = 0, done inmediato) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd15, 4'd3, 1'b0, 4'd15, 150);

        // ==== BAJAR (op=1) ====
        $display("=== BAJA: piso 10 - 5 → esperado 5 (5 pasos, 650ns total) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd10, 4'd5, 1'b1, 4'd5, 650);

        $display("=== BAJA: piso 3 - 5 → satura en 0 (B efectivo = 3, 450ns total) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd3, 4'd5, 1'b1, 4'd0, 450);

        $display("=== BAJA: piso 8 - 1 → piso 7 (1 paso, 250ns total) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd8, 4'd1, 1'b1, 4'd7, 250);

        $display("=== BAJA: piso 0 - 3 → ya en minimo (B efectivo = 0, done inmediato) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd0, 4'd3, 1'b1, 4'd0, 150);

        $finish;
    end

endmodule
