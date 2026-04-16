module mic_saver (
    input  logic clk,
    input  logic reset,
    input  logic clear_clap_seen,
    input  logic set_clap_seen,
    input  logic [2:0] load_bit,

    output logic seen_clap,
    output logic dir_reg,
    output logic [3:0] num_reg
);

    logic next_seen;
    logic next_dir;
    logic next_num0, next_num1, next_num2, next_num3;

    logic load_dir, load_reg0, load_reg1, load_reg2, load_reg3;

    // seen_clap next
    assign next_seen = set_clap_seen | (seen_clap & ~clear_clap_seen);

    // serializer de load_bit
    assign load_dir = (~load_bit[2] & ~load_bit[1] &  load_bit[0]); // 001
    assign load_reg0 = (~load_bit[2] &  load_bit[1] & ~load_bit[0]); // 010
    assign load_reg1 = (~load_bit[2] &  load_bit[1] &  load_bit[0]); // 011
    assign load_reg2 = ( load_bit[2] & ~load_bit[1] & ~load_bit[0]); // 100
    assign load_reg3 = ( load_bit[2] & ~load_bit[1] &  load_bit[0]); // 101

    // Next register state
    assign next_dir = ( load_dir  & seen_clap) | (~load_dir  & dir_reg);
    assign next_num0 = ( load_reg0 & seen_clap) | (~load_reg0 & num_reg[0]);
    assign next_num1 = ( load_reg1 & seen_clap) | (~load_reg1 & num_reg[1]);
    assign next_num2 = ( load_reg2 & seen_clap) | (~load_reg2 & num_reg[2]);
    assign next_num3 = ( load_reg3 & seen_clap) | (~load_reg3 & num_reg[3]);

    // Flip-flops that storage the 4 bits
    flip_flop_d ff_seen (.clk(clk), .reset(reset), .d(next_seen), .q(seen_clap)); // internal register
    flip_flop_d ff_dir  (.clk(clk), .reset(reset), .d(next_dir),  .q(dir_reg));

    flip_flop_d ff_bit0 (.clk(clk), .reset(reset), .d(next_num0), .q(num_reg[0]));
    flip_flop_d ff_bit1 (.clk(clk), .reset(reset), .d(next_num1), .q(num_reg[1]));
    flip_flop_d ff_bit2 (.clk(clk), .reset(reset), .d(next_num2), .q(num_reg[2]));
    flip_flop_d ff_bit3 (.clk(clk), .reset(reset), .d(next_num3), .q(num_reg[3]));

endmodule