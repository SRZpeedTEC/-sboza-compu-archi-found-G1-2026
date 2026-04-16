// Conectando todos los módulos para PWM

module pwm_top(
    input clk,
    input rst_n,
    input [2:0] pwm_level,
    output pwm_out
);

wire [7:0] duty;   // Porcentaje
wire [7:0] count;  // Contador
wire       reset;  // Reset activo alto (counter_pwm usa activo alto)
assign reset = ~rst_n;

decoder_pwm    d0  (pwm_level, duty);
counter_pwm    c0  (.clk(clk), .reset(reset), .count(count));
comparator_pwm cmp (count, duty, pwm_out);

endmodule