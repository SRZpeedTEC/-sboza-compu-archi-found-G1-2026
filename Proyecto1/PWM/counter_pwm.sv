// =============================================================================
// counter_pwm — Contador para generación de PWM (estructural)
//
// Genera un contador 'count' de 0 a 99 con un prescaler de 0 a 999.
// El prescaler divide el reloj para que count avance a la frecuencia correcta.
//
// Reset activo alto, consistente con el resto del proyecto.
//
// Implementación:
//   - incrementer  para prescaler+1 y count+1
//   - eq_comparator para prescaler==999 y count==99
//   - Lógica de next value con AND/OR (mascara de bits), igual que ALU.sv
//   - always_ff para los registros
// =============================================================================

module counter_pwm (
    input        clk,
    input        reset,
    output [7:0] count
);

    // -------------------------------------------------------------------------
    // Registros
    // -------------------------------------------------------------------------
    reg [9:0] prescaler;
    reg [7:0] count_reg;
    assign count = count_reg;

    // -------------------------------------------------------------------------
    // Constantes como vectores para eq_comparator
    // -------------------------------------------------------------------------
    localparam [9:0] PRESCALER_MAX = 10'd999;
    localparam [7:0] COUNT_MAX     = 8'd99;

    // -------------------------------------------------------------------------
    // Prescaler: incrementer + comparador
    // -------------------------------------------------------------------------
    wire [9:0] prescaler_inc;
    incrementer #(.WIDTH(10)) u_pre_inc (
        .in  (prescaler),
        .out (prescaler_inc)
    );

    wire prescaler_done;
    eq_comparator #(.WIDTH(10)) u_pre_cmp (
        .a  (prescaler),
        .b  (PRESCALER_MAX),
        .eq (prescaler_done)
    );

    // next_prescaler: 0 cuando done, prescaler_inc en caso contrario
    // {10{~prescaler_done}} crea una mascara de ANDs de 1 bit replicado
    wire [9:0] next_prescaler;
    assign next_prescaler = {10{~prescaler_done}} & prescaler_inc;

    // -------------------------------------------------------------------------
    // Count: incrementer + comparador
    // -------------------------------------------------------------------------
    wire [7:0] count_inc;
    incrementer #(.WIDTH(8)) u_cnt_inc (
        .in  (count_reg),
        .out (count_inc)
    );

    wire count_done;
    eq_comparator #(.WIDTH(8)) u_cnt_cmp (
        .a  (count_reg),
        .b  (COUNT_MAX),
        .eq (count_done)
    );

    // next_count:
    //   ~prescaler_done           → hold (count_reg)
    //   prescaler_done & count_done  → 0
    //   prescaler_done & ~count_done → count_inc
    wire [7:0] next_count;
    assign next_count = ({8{~prescaler_done}}          & count_reg)
                      | ({8{prescaler_done & ~count_done}} & count_inc);

    // -------------------------------------------------------------------------
    // Flip-flops (reset activo alto)
    // -------------------------------------------------------------------------
    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            prescaler <= 10'd0;
            count_reg <= 8'd0;
        end else begin
            prescaler <= next_prescaler;
            count_reg <= next_count;
        end
    end

endmodule
