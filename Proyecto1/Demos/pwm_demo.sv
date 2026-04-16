// Demo de prueba manual del módulo PWM
// Aquí se controla con switches físicos para verificar funcionamiento

module pwm_demo (
    input        clk,
    input        rst_n,           // KEY[0], activo-bajo
    input  [2:0] pwm_level,       // SW[2:0], simula salida de la ALU
    output       led_pwm,         // LEDR[0], salida PWM observable
    output       led_dir          // LEDR[1], indicador visual del nivel sw[0]
);

pwm_top pwm (
    .clk       (clk),
    .rst_n     (rst_n),
    .pwm_level (pwm_level),
    .pwm_out   (led_pwm)
);

assign led_dir = pwm_level[0];

endmodule