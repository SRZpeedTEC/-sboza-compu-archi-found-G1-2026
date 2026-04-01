module mic_top #(
    parameter int unsigned CLK_FREQ_HZ = 50_000_000,
    parameter int unsigned LISTEN_TIME_MS = 4000
)(
    input  logic clk,
    input  logic reset,
    input  logic activate_mic,
    input  logic clap_event,
    input  logic [2:0] mode_mic,

    output logic mic_done,
    output logic init_system,
    output logic listening_led,
    output logic dir_reg,
    output logic [3:0] num_reg
);

    logic s1, s0;
    logic clear_clap_seen;
    logic set_clap_seen;
    logic [2:0] load_bit;
    logic seen_clap;
    logic mic_times_done_internal;
    logic timer_enable;

    // El timer se habilita en estado Listen
    assign timer_enable = (~s1 & s0);

    mic_control_fsm mic_fsm (
        .clk(clk),
        .reset(reset),
        .activate_mic(activate_mic),
        .mic_times_done(mic_times_done_internal),
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

    mic_saver mic_regs (
        .clk(clk),
        .reset(reset),
        .clear_clap_seen(clear_clap_seen),
        .set_clap_seen(set_clap_seen),
        .load_bit(load_bit),
        .seen_clap(seen_clap),
        .dir_reg(dir_reg),
        .num_reg(num_reg)
    );

    mic_timer #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .LISTEN_TIME_MS(LISTEN_TIME_MS)
    ) mic_listen_timer (
        .clk(clk),
        .reset(reset),
        .enable(timer_enable),
        .mic_times_done(mic_times_done_internal)
    );

endmodule