`timescale 1ns/1ps

module tb_mic_top;

    logic clk;
    logic reset;
    logic activate_mic;
    logic clap_event;
    logic [2:0] mode_mic;

    logic mic_done;
    logic init_system;
    logic listening_led;
    logic dir_reg;
    logic [3:0] num_reg;

    mic_top #(
        .CLK_FREQ_HZ(1000),
        .LISTEN_TIME_MS(4)
    ) dut (
        .clk(clk),
        .reset(reset),
        .activate_mic(activate_mic),
        .clap_event(clap_event),
        .mode_mic(mode_mic),
        .mic_done(mic_done),
        .init_system(init_system),
        .listening_led(listening_led),
        .dir_reg(dir_reg),
        .num_reg(num_reg)
    );

    always #5 clk = ~clk;

    task run_capture(
        input [2:0] mode,
        input bit clap_present
    );
        integer i;
        begin
            mode_mic = mode;
            activate_mic = 1;
            clap_event = 0;

            // Entra a Listen
            @(posedge clk);
            #1;

            // Meter un aplauso durante la ventana si aplica
            if (clap_present) begin
                clap_event = 1;
                #10;
                clap_event = 0;
            end

            // Esperar a que termine el ciclo completo
            for (i = 0; i < 10; i = i + 1) begin
                @(posedge clk);
                if (mic_done || init_system)
                    disable wait_loop;
            end

            wait_loop: ;
            activate_mic = 0;
            @(posedge clk);
            #1;
        end
    endtask

    initial begin
        clk = 0;
        reset = 1;
        activate_mic = 0;
        clap_event = 0;
        mode_mic = 3'b000;

        #12;
        reset = 0;

        // Caso 1: aplauso inicial
        run_capture(3'b000, 1);
        if (init_system !== 1) begin
            $display("ERROR: init_system no se activó");
            $stop;
        end

        // Dejar que baje
        @(posedge clk);

        // Caso 2: dirección = 1
        run_capture(3'b001, 1);
        if (dir_reg !== 1) begin
            $display("ERROR: dir_reg no quedó en 1");
            $stop;
        end

        // Caso 3: bit0 = 1
        run_capture(3'b010, 1);
        if (num_reg[0] !== 1) begin
            $display("ERROR: num_reg[0] no quedó en 1");
            $stop;
        end

        // Caso 4: bit1 = 0, sin aplauso
        run_capture(3'b011, 0);
        if (num_reg[1] !== 0) begin
            $display("ERROR: num_reg[1] debia quedar en 0");
            $stop;
        end

        // Caso 5: bit2 = 1
        run_capture(3'b100, 1);
        if (num_reg[2] !== 1) begin
            $display("ERROR: num_reg[2] no quedó en 1");
            $stop;
        end

        // Caso 6: bit3 = 0
        run_capture(3'b101, 0);
        if (num_reg[3] !== 0) begin
            $display("ERROR: num_reg[3] debia quedar en 0");
            $stop;
        end

        $display("Resultado final num_reg = %b", num_reg);
        $display("tb_mic_top OK");
        $finish;
    end

endmodule