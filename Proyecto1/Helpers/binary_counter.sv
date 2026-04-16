module binary_counter #(
    parameter int unsigned CLK_FREQ_HZ = 50_000_000,
    parameter int unsigned LISTEN_TIME_MS = 4000

)(
    input  logic clk,
    input  logic reset,
    input  logic enable,
    output logic mic_times_done
);

    localparam int unsigned TERMINAL_COUNT = ((CLK_FREQ_HZ / 1000) * LISTEN_TIME_MS) - 1;
    localparam int unsigned WIDTH = $clog2(TERMINAL_COUNT + 1);
    localparam logic [WIDTH-1:0] TERMINAL_COUNT_VEC = TERMINAL_COUNT[WIDTH-1:0];

    logic [WIDTH-1:0] count_q;
    logic [WIDTH-1:0] count_d;
    logic count_enable;

    eq_comparator #(.WIDTH(WIDTH)) u_done_cmp (
        .a  (count_q),
        .b  (TERMINAL_COUNT_VEC),
        .eq (mic_times_done)
    );
    assign count_enable = enable & ~mic_times_done;

    // and_ones[i] = count_q[0] & count_q[1] & ... & count_q[i]
    // Reemplaza la reduccion &count_q[i-1:0] con cadena AND explicita bit a bit.
    wire [WIDTH-1:0] and_ones;
    assign and_ones[0] = count_q[0];

    assign count_d[0] = count_enable & ~count_q[0];

    genvar i;
    generate
        for (i = 1; i < WIDTH; i = i + 1) begin : gen_counter_bits
            assign and_ones[i] = and_ones[i-1] & count_q[i];
            assign count_d[i]  = count_enable & (count_q[i] ^ and_ones[i-1]);

            flip_flop_d ff_count (
                .clk(clk),
                .reset(reset),
                .d(count_d[i]),
                .q(count_q[i])
            );
        end
    endgenerate

    flip_flop_d ff_count_0 (
        .clk(clk),
        .reset(reset),
        .d(count_d[0]),
        .q(count_q[0])
    );

endmodule