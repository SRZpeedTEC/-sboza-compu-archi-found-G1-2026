module mic_timer #(
)(
    input logic clk,
    input logic reset,
    input logic enable,
    input logic CLK_FREQ_HZ,
    input logic LISTEN_TIME_MS,
    output logic mic_times_done
);

    localparam int unsigned TERMINAL_COUNT = ((CLK_FREQ_HZ / 1000) * LISTEN_TIME_MS) - 1;
    localparam int unsigned WIDTH = $clog2(TERMINAL_COUNT + 1);

    localparam logic [WIDTH-1:0] TERMINAL_COUNT_VEC = TERMINAL_COUNT[WIDTH-1:0];

    logic [WIDTH-1:0] count_q;
    logic [WIDTH-1:0] count_d;

    logic count_enable;

    assign mic_times_done = (count_q == TERMINAL_COUNT_VEC);
    assign count_enable   = enable & ~mic_times_done;

    // Bit 0
    assign count_d[0] = count_enable & ~count_q[0];

    // Bits restantes
    genvar i;
    generate
        for (i = 1; i < WIDTH; i = i + 1) begin : gen_counter_bits
            logic lower_bits_all_ones;

            assign lower_bits_all_ones = &count_q[i-1:0];
            assign count_d[i] = count_enable & (count_q[i] ^ lower_bits_all_ones);

            flip_flop_d ff_count (
                .clk(clk),
                .reset(reset),
                .d(count_d[i]),
                .q(count_q[i])
            );
        end
    endgenerate

    // Flip-flop del bit 0
    flip_flop_d ff_count_0 (
        .clk(clk),
        .reset(reset),
        .d(count_d[0]),
        .q(count_q[0])
    );

endmodule