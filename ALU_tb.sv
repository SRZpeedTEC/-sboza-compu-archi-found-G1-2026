`timescale 1ns/1ps

module tb_alu_ascensor;
    reg        clk, rst_n, load, op;
    reg  [3:0] piso_init, pisos_delta;
    wire [6:0] seg;
    wire [3:0] piso_actual;
    wire [2:0] pwm_level;

    ALU dut (
        .clk(clk), .rst_n(rst_n),
        .piso_init(piso_init), .pisos_delta(pisos_delta),
        .load(load), .op(op),
        .piso_actual(piso_actual),
        .pwm_level(pwm_level),
        .seg(seg)
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
        reg [6:0] pct;
        reg [7:0] c;
        begin
            pct = pwm_pct(lvl);
            c   = hex_char(piso);
            $display("| Piso: %2d (hex: %s) | Dir: %s | PWM: %3d%% (%03b) | seg: %b |",
                     piso, c,
                     direccion ? "BAJA" : "SUBE",
                     pct, lvl, segmentos);
        end
    endtask

    always @(posedge clk) begin
        if (rst_n)
            print_state(piso_actual, pwm_level, seg, op);
    end

    task automatic do_test;
        input [3:0] p_init;
        input [3:0] p_delta;
        input       direccion;
        input [3:0] esperado;
        input [7:0] espera_ns;
        begin
            piso_init   = p_init;
            pisos_delta = p_delta;
            op          = direccion;
            #10 load = 1;
            #10 load = 0;
            #(espera_ns);
            $display("|----------------------------------------------------------------------|");
            $display("Resultado: %2d | Esperado: %2d | %s\n",
                     piso_actual, esperado,
                     (piso_actual == esperado) ? "PASS" : "FAIL");
        end
    endtask

    initial begin
        $dumpfile("sim.vcd");
        $dumpvars(0, tb_alu_ascensor);

        clk = 0; rst_n = 0; load = 0; op = 0;
        piso_init = 0; pisos_delta = 0;
        #12 rst_n = 1;

        // ==== SUBIR (op=0) ====
        $display("\n=== SUBE: piso 3 + 5 → esperado 8 ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd3, 4'd5, 1'b0, 4'd8, 8'd120);

        $display("=== SUBE: piso 13 + 5 → satura en 15 (B efectivo = 2) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd13, 4'd5, 1'b0, 4'd15, 8'd80);

        $display("=== SUBE: piso 1 + 1 → piso 2 (25%% PWM) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd1, 4'd1, 1'b0, 4'd2, 8'd60);

        $display("=== SUBE: piso 15 + 3 → ya en maximo, B efectivo = 0 ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd15, 4'd3, 1'b0, 4'd15, 8'd60);

        // ==== BAJAR (op=1) ====
        $display("=== BAJA: piso 10 - 5 → esperado 5 ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd10, 4'd5, 1'b1, 4'd5, 8'd120);

        $display("=== BAJA: piso 3 - 5 → satura en 0 (B efectivo = 3) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd3, 4'd5, 1'b1, 4'd0, 8'd80);

        $display("=== BAJA: piso 8 - 1 → piso 7 (25%% PWM) ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd8, 4'd1, 1'b1, 4'd7, 8'd60);

        $display("=== BAJA: piso 0 - 3 → ya en minimo, B efectivo = 0 ===");
        $display("|----------------------------------------------------------------------|");
        do_test(4'd0, 4'd3, 1'b1, 4'd0, 8'd60);

        $finish;
    end

endmodule
