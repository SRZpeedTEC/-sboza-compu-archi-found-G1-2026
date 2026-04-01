// Traducción de la ALU para el PWM

module decoder_pwm(
    input [2:0] pwm_level,
    output [7:0] duty
);

// valores
assign duty =
    (pwm_level == 3'b000) ? 8'd0   : //Si pwm_level = 000 entonces duty = 0%
    (pwm_level == 3'b001) ? 8'd25  : //Si pwm_level = 001 entonces duty = 25%
    (pwm_level == 3'b010) ? 8'd50  : //Si pwm_level = 010 entonces duty = 50%
    (pwm_level == 3'b011) ? 8'd75  : //Si pwm_level = 011 entonces duty = 75%
    (pwm_level == 3'b100) ? 8'd100 : //Si pwm_level = 100 entonces duty = 100%
    8'd0;

endmodule