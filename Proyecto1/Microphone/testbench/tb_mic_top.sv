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

    logic saw_init;
    logic saw_done;

    // Ajustados pequeños para simular rápido
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

    // Clock de 10 ns
    always #5 clk = ~clk;

    // Task para ejecutar una captura completa
    task automatic run_capture(
        input  logic [2:0] mode,
        input  logic       clap_present,
        output logic       got_init,
        output logic       got_done
    );
        integer timeout;
        begin
            got_init = 1'b0;
            got_done = 1'b0;

            mode_mic      = mode;
            activate_mic  = 1'b1;
            clap_event    = 1'b0;

            // Deja que entre a Listen
            @(posedge clk);
            #1;

            if (listening_led !== 1'b1) begin
                $display("ERROR: listening_led no se activó al entrar a Listen");
                $stop;
            end

            // Genera aplauso dentro de la ventana si aplica
            if (clap_present) begin
                clap_event = 1'b1;
                @(posedge clk);
                #1;
                clap_event = 1'b0;
            end

            // Espera hasta que aparezca init_system o mic_done
            timeout = 0;
            while (!(mic_done || init_system) && timeout < 50) begin
                @(posedge clk);
                timeout = timeout + 1;
            end

            if (timeout >= 50) begin
                $display("ERROR: timeout esperando fin de captura. mode=%b", mode);
                $stop;
            end

            if (init_system) got_init = 1'b1;
            if (mic_done)    got_done = 1'b1;

            // Baja activación y deja que la FSM vuelva a S0
            activate_mic = 1'b0;
            clap_event   = 1'b0;
            mode_mic     = 3'b000;

            @(posedge clk);
            #1;

            if (listening_led !== 1'b0) begin
                $display("ERROR: listening_led debia apagarse al salir de Listen");
                $stop;
            end
        end
    endtask

    initial begin
        clk = 1'b0;
        reset = 1'b1;
        activate_mic = 1'b0;
        clap_event = 1'b0;
        mode_mic = 3'b000;

        #12;
        reset = 1'b0;
        #1;

        // Verificación inicial
        if (dir_reg !== 1'b0 || num_reg !== 4'b0000) begin
            $display("ERROR: reset incorrecto en mic_top");
            $stop;
        end

        // 1) Aplauso inicial: debe activar init_system
        run_capture(3'b000, 1'b1, saw_init, saw_done);
        if (!saw_init) begin
            $display("ERROR: init_system no se activó");
            $stop;
        end

        // 2) Dirección = 1
        run_capture(3'b001, 1'b1, saw_init, saw_done);
        if (!saw_done) begin
            $display("ERROR: mic_done no se activó en captura de dirección");
            $stop;
        end
        if (dir_reg !== 1'b1) begin
            $display("ERROR: dir_reg no quedó en 1");
            $stop;
        end

        // 3) num_reg[0] = 1
        run_capture(3'b010, 1'b1, saw_init, saw_done);
        if (num_reg[0] !== 1'b1) begin
            $display("ERROR: num_reg[0] no quedó en 1");
            $stop;
        end

        // 4) num_reg[1] = 0
        run_capture(3'b011, 1'b0, saw_init, saw_done);
        if (num_reg[1] !== 1'b0) begin
            $display("ERROR: num_reg[1] debia quedar en 0");
            $stop;
        end

        // 5) num_reg[2] = 1
        run_capture(3'b100, 1'b1, saw_init, saw_done);
        if (num_reg[2] !== 1'b1) begin
            $display("ERROR: num_reg[2] no quedó en 1");
            $stop;
        end

        // 6) num_reg[3] = 0
        run_capture(3'b101, 1'b0, saw_init, saw_done);
        if (num_reg[3] !== 1'b0) begin
            $display("ERROR: num_reg[3] debia quedar en 0");
            $stop;
        end

        $display("tb_mic_top OK");
        $display("dir_reg = %b", dir_reg);
        $display("num_reg = %b", num_reg);

        $finish;
    end

endmodule