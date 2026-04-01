`timescale 1ns/1ps

module tb_mic_saver;

    logic clk;
    logic reset;
    logic clear_clap_seen;
    logic set_clap_seen;
    logic [2:0] load_bit;

    logic seen_clap;
    logic dir_reg;
    logic [3:0] num_reg;

    mic_saver dut (
        .clk(clk),
        .reset(reset),
        .clear_clap_seen(clear_clap_seen),
        .set_clap_seen(set_clap_seen),
        .load_bit(load_bit),
        .seen_clap(seen_clap),
        .dir_reg(dir_reg),
        .num_reg(num_reg)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 0;
        reset = 1;
        clear_clap_seen = 0;
        set_clap_seen = 0;
        load_bit = 3'b000;

        #12;
        reset = 0;

        // Inicialmente todo debe estar en 0
        #1;
        if (seen_clap !== 0 || dir_reg !== 0 || num_reg !== 4'b0000) begin
            $display("ERROR: reset incorrecto en mic_saver");
            $stop;
        end

        // Set seen_clap
        set_clap_seen = 1;
        @(posedge clk);
        #1;
        set_clap_seen = 0;
        if (seen_clap !== 1) begin
            $display("ERROR: seen_clap no se puso en 1");
            $stop;
        end

        // Guardar en dir_reg
        load_bit = 3'b001;
        @(posedge clk);
        #1;
        load_bit = 3'b000;
        if (dir_reg !== 1) begin
            $display("ERROR: dir_reg no guardó seen_clap");
            $stop;
        end

        // Guardar en num_reg[0]
        load_bit = 3'b010;
        @(posedge clk);
        #1;
        if (num_reg[0] !== 1) begin
            $display("ERROR: num_reg[0] no guardó seen_clap");
            $stop;
        end

        // Guardar en num_reg[1]
        load_bit = 3'b011;
        @(posedge clk);
        #1;
        if (num_reg[1] !== 1) begin
            $display("ERROR: num_reg[1] no guardó seen_clap");
            $stop;
        end

        // Guardar en num_reg[2]
        load_bit = 3'b100;
        @(posedge clk);
        #1;
        if (num_reg[2] !== 1) begin
            $display("ERROR: num_reg[2] no guardó seen_clap");
            $stop;
        end

        // Guardar en num_reg[3]
        load_bit = 3'b101;
        @(posedge clk);
        #1;
        if (num_reg[3] !== 1) begin
            $display("ERROR: num_reg[3] no guardó seen_clap");
            $stop;
        end

        // Limpiar seen_clap
        load_bit = 3'b000;
        clear_clap_seen = 1;
        @(posedge clk);
        #1;
        clear_clap_seen = 0;
        if (seen_clap !== 0) begin
            $display("ERROR: seen_clap no se limpió");
            $stop;
        end

        $display("tb_mic_saver OK");
        $finish;
    end

endmodule