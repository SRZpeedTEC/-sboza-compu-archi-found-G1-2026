
// Module that control the flow of microphone FSM
module mic_control_fsm (
    input  logic clk,
    input  logic reset,
    input  logic activate_mic,
    input  logic mic_times_done,
    input  logic clap_event,
    input  logic [2:0] mode_mic,
    input  logic seen_clap,

    output logic s1,
    output logic s0,
    output logic clear_clap_seen,
    output logic set_clap_seen,
    output logic mic_done,
    output logic init_system,
    output logic listening_led,
    output logic [2:0] load_bit
);

    logic next_s1, next_s0;
    logic m2, m1, m0;

    assign m2 = mode_mic[2];
    assign m1 = mode_mic[1];
    assign m0 = mode_mic[0];

    // Next state
    assign next_s1 = (~s1 & s0 & mic_times_done);
    assign next_s0 = (~s1 & ~s0 & activate_mic) | (~s1 &  s0 & ~mic_times_done);

    // Control outputs
    assign clear_clap_seen = (~s1 & ~s0);
    assign set_clap_seen   = (~s1 &  s0 & clap_event);
    assign mic_done        = ( s1 & ~s0);
    assign listening_led   = (~s1 &  s0);
    assign init_system = (s1 & ~s0 & ~m2 & ~m1 & ~m0 & seen_clap);

    // load_bit is active only in S2
    assign load_bit[2] = (s1 & ~s0 & m2);
    assign load_bit[1] = (s1 & ~s0 & m1);
    assign load_bit[0] = (s1 & ~s0 & m0);

    // State flip flops
    flip_flop_d ff_s1 (
        .clk(clk),
        .reset(reset),
        .d(next_s1),
        .q(s1)
    );

    flip_flop_d ff_s0 (
        .clk(clk),
        .reset(reset),
        .d(next_s0),
        .q(s0)
    );

endmodule