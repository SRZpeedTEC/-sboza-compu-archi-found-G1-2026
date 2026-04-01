`timescale 1ns/1ps

module tb_mic_control_fsm;

    logic clk;
    logic reset;
    logic activate_mic;
    logic mic_times_done;
    logic clap_event;
    logic [2:0] mode_mic;
    logic seen_clap;

    logic s1, s0;
    logic clear_clap_seen;
    logic set_clap_seen;
    logic mic_done;
    logic init_system;
    logic listening_led;
    logic [2:0] load_bit;

    mic_control_fsm dut (
        .clk(clk),
        .reset(reset),
        .activate_mic(activate_mic),
        .mic_times_done(mic_times_done),
        .clap_event(clap_event),
        .mode_mic(mode_mic),
        .seen_clap(seen_clap),
        .s1(s1),
        .s0(s0),
        .clear_clap_seen(clear_clap_seen),
        .set_clap_seen(set_clap_seen),
        .mic_done(mic_done),
        .init_system(init_system),
        .listening_led(listening_led),
        .load_bit(load_bit)
    );

    always #5 clk = ~clk;

    task expect_state(input logic exp_s1, input logic exp_s0, input string msg);
        begin
            if ({s1,s0} !== {exp_s1,exp_s0}) begin
                $display("ERROR: %s | state=%b%b esperado=%b%b", msg, s1, s0, exp_s1, exp_s0);
                $stop;
            end
        end
    endtask

    initial begin
        clk = 0;
        reset = 1;
        activate_mic = 0;
        mic_times_done = 0;
        clap_event = 0;
        mode_mic = 3'b000;
        seen_clap = 0;

        #12;
        reset = 0;

        // Debe iniciar en S0 = 00
        #2;
        expect_state(1'b0, 1'b0, "reset -> S0");
        if (clear_clap_seen !== 1 || listening_led !== 0 || mic_done !== 0) begin
            $display("ERROR: outputs incorrectos en S0");
            $stop;
        end

        // Activar micrófono -> pasa a S1 en siguiente flanco
        activate_mic = 1;
        @(posedge clk);
        #1;
        expect_state(1'b0, 1'b1, "S0 -> S1");

        if (listening_led !== 1) begin
            $display("ERROR: listening_led debia estar encendido en S1");
            $stop;
        end

        // clap_event en S1
        clap_event = 1;
        #1;
        if (set_clap_seen !== 1) begin
            $display("ERROR: set_clap_seen debia valer 1 en S1 con clap_event");
            $stop;
        end
        clap_event = 0;

        // Mientras mic_times_done=0, debe quedarse en S1
        @(posedge clk);
        #1;
        expect_state(1'b0, 1'b1, "permanece en S1");

        // Termina tiempo -> pasa a S2
        mic_times_done = 1;
        @(posedge clk);
        #1;
        expect_state(1'b1, 1'b0, "S1 -> S2");

        if (mic_done !== 1) begin
            $display("ERROR: mic_done debia valer 1 en S2");
            $stop;
        end

        // Probar init_system con mode=000 y seen_clap=1
        mode_mic = 3'b000;
        seen_clap = 1;
        #1;
        if (init_system !== 1) begin
            $display("ERROR: init_system debia valer 1 en S2 con mode 000 y seen_clap=1");
            $stop;
        end

        // Probar load_bit
        mode_mic = 3'b101;
        #1;
        if (load_bit !== 3'b101) begin
            $display("ERROR: load_bit incorrecto en S2");
            $stop;
        end

        // En siguiente flanco debe volver a S0
        mic_times_done = 0;
        activate_mic = 0;
        @(posedge clk);
        #1;
        expect_state(1'b0, 1'b0, "S2 -> S0");

        $display("tb_mic_control_fsm OK");
        $finish;
    end

endmodule