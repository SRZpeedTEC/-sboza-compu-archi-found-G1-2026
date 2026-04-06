module counter_pwm(
    input clk,
    input rst_n,
    output reg [7:0] count
);

reg [9:0] prescaler;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count     <= 0;
        prescaler <= 0;
    end
    else begin
        prescaler <= prescaler + 1;
        if (prescaler == 10'd999) begin
            prescaler <= 0;
            if (count == 8'd99)
                count <= 0;
            else
                count <= count + 1;
        end
    end
end

endmodule