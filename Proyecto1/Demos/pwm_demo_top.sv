// =============================================================================
// pwm_demo_top — Demo standalone del módulo PWM
//
// Demuestra los 5 niveles de duty cycle en un LED usando 3 switches.
// Un switch adicional indica dirección y enciende un LED indicador.
//
// Puertos físicos (DE10-Lite):
//   clk      : reloj 50 MHz
//   rst_n    : reset activo bajo (KEY0)
//   sw[2:0]  : switches que seleccionan el nivel PWM
//              000=0%  001=25%  010=50%  011=75%  100=100%
//   sw_dir   : switch de dirección (0=baja, 1=sube)
//   pwm_led  : LED que muestra el duty cycle (brillo variable)
//   dir_led  : LED que se enciende cuando sw_dir=1 (subiendo)
// =============================================================================
module pwm_demo_top (
    input  logic       clk,
    input  logic       reset,
    input  logic [2:0] sw,
    input  logic       sw_dir,
    output logic       pwm_led,
    output logic       dir_led
);

    pwm_top u_pwm (
        .clk      (clk),
        .rst_n    (reset),
        .pwm_level(sw),
        .pwm_out  (pwm_led)
    );

    assign dir_led = sw_dir;

endmodule
