// ALU: controlador estructural
// op = 0 --> subir (usa ALU_Adder)
// op = 1 --> bajar (usa ALU_Substractor)
// El timer interno genera un tick cada 1 segundo. En ese momento, A y B se actualizan

module ALU #(
    parameter integer CLK_FREQ = 50_000_000  // Hz (ESTO HAY QUE AJUSTARLO PARA LA IMPLENTACION REAL AL RELOJ DE LA FPGA)
)(
    input        clk,
    input        rst_n,
    input  [3:0] piso_init,
    input  [3:0] pisos_delta,  // pisos a subir o bajar
    input        load,
    input        op,           // 0 = subir, 1 = bajar
    output [3:0] piso_actual,
    output [2:0] pwm_level,
    output [6:0] seg,
    output       done          // 1 cuando se completo el ultimo ciclo
);

    // TIMER: cuenta ciclos de clk hasta CLK_FREQ para generar un tick cada 1 segundo
    localparam integer TIMER_MAX  = CLK_FREQ - 1;
    localparam integer TIMER_BITS = $clog2(CLK_FREQ);

    reg [TIMER_BITS-1:0] timer;

    // tick = 1 exactamente un ciclo cuando timer llega a TIMER_MAX
    wire tick;
    assign tick = (timer == TIMER_MAX);

    // timer + 1: sumador combinacional
    wire [TIMER_BITS-1:0] timer_inc;
    assign timer_inc = timer + 1'b1;

    // reset_timer = 1 cuando load o tick --> el timer vuelve a 0
    wire reset_timer;
    assign reset_timer = load | tick;

    // next_timer:
    //   Si reset_timer = 1  -->  next_timer = 0   (AND con 0 en cada bit)
    //   Si reset_timer = 0  -->  next_timer = timer_inc (AND con 1 en cada bit)
    wire [TIMER_BITS-1:0] next_timer;
    assign next_timer = {TIMER_BITS{~reset_timer}} & timer_inc;

    // Flip-flop del timer 
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) timer <= {TIMER_BITS{1'b0}};
        else        timer <= next_timer;
    end

    // ================================================================
    // REGISTROS A (piso actual) y B (pasos restantes)
    // ================================================================

    reg [3:0] A;
    reg [3:0] B;

    assign piso_actual = A;

    // ================================================================
    // INSTANCIAS ALU_Adder y ALU_Substractor
    // ================================================================

    wire [3:0] A_plus1;
    wire       A_eq_max;
    wire [3:0] B_ef_add;

    ALU_Adder adder (
        .piso_init   (piso_init),
        .pisos_subir (pisos_delta),
        .A_reg       (A),
        .A_plus1     (A_plus1),
        .A_eq_max    (A_eq_max),
        .B_restantes (B_ef_add)
    );

    wire [3:0] A_minus1;
    wire       A_eq_min;
    wire [3:0] B_ef_sub;

    ALU_Substractor substractor (
        .piso_init   (piso_init),
        .pisos_bajar (pisos_delta),
        .A_reg       (A),
        .A_minus1    (A_minus1),
        .A_eq_min    (A_eq_min),
        .B_restantes (B_ef_sub)
    );

    // ================================================================
    // MUX op: selecciona operacion subir/bajar
    // step_A    = A+1 si op=0, A-1 si op=1
    // B_restantes = B efectivos segun direccion
    // ================================================================

    wire [3:0] step_A;
    assign step_A[0] = (~op & A_plus1[0]) | (op & A_minus1[0]);
    assign step_A[1] = (~op & A_plus1[1]) | (op & A_minus1[1]);
    assign step_A[2] = (~op & A_plus1[2]) | (op & A_minus1[2]);
    assign step_A[3] = (~op & A_plus1[3]) | (op & A_minus1[3]);

    wire [3:0] B_restantes;
    assign B_restantes[0] = (~op & B_ef_add[0]) | (op & B_ef_sub[0]);
    assign B_restantes[1] = (~op & B_ef_add[1]) | (op & B_ef_sub[1]);
    assign B_restantes[2] = (~op & B_ef_add[2]) | (op & B_ef_sub[2]);
    assign B_restantes[3] = (~op & B_ef_add[3]) | (op & B_ef_sub[3]);

    // ================================================================
    // enable: B != 0   (el ascensor aun tiene pasos por dar)
    // hold_A: A no debe moverse (B agotado o saturacion de piso)
    // ================================================================

    wire enable;
    assign enable = B[3] | B[2] | B[1] | B[0];

    wire hold_A;
    assign hold_A = (~enable)
                  | (~op & enable & A_eq_max)
                  | ( op & enable & A_eq_min);

    // ================================================================
    // B - 1: restador combinacional (ripple borrow)
    // ================================================================

    wire [3:0] B_minus1;
    wire bw0, bw1, bw2;
    assign B_minus1[0] = B[0] ^ 1'b1;
    assign bw0          = ~B[0];
    assign B_minus1[1] = B[1] ^ bw0;
    assign bw1          = ~B[1] & bw0;
    assign B_minus1[2] = B[2] ^ bw1;
    assign bw2          = ~B[2] & bw1;
    assign B_minus1[3] = B[3] ^ bw2;


    // update: A y B solo cambian cuando hay tick o load (Ecuacion booleana: update = load | tick)
    wire update;
    assign update = load | tick;

    // ================================================================
    // A_comb: valor de A si ocurre una actualizacion (load o tick)
    //
    // Tabla de verdad del MUX:
    //   load=1              --> A_comb = piso_init
    //   load=0, hold_A=1    --> A_comb = A  (saturacion o B==0)
    //   load=0, hold_A=0    --> A_comb = step_A  (avanza un piso)
    // ================================================================

    wire [3:0] A_comb;
    assign A_comb[0] = (load & piso_init[0])
                     | (~load & ~hold_A & step_A[0])
                     | (~load &  hold_A & A[0]);
    assign A_comb[1] = (load & piso_init[1])
                     | (~load & ~hold_A & step_A[1])
                     | (~load &  hold_A & A[1]);
    assign A_comb[2] = (load & piso_init[2])
                     | (~load & ~hold_A & step_A[2])
                     | (~load &  hold_A & A[2]);
    assign A_comb[3] = (load & piso_init[3])
                     | (~load & ~hold_A & step_A[3])
                     | (~load &  hold_A & A[3]);

    // next_A: A_comb si hay actualizacion; A sin cambio si no next_A[i] = (update & A_comb[i]) | (~update & A[i])
    wire [3:0] next_A;
    assign next_A[0] = (update & A_comb[0]) | (~update & A[0]);
    assign next_A[1] = (update & A_comb[1]) | (~update & A[1]);
    assign next_A[2] = (update & A_comb[2]) | (~update & A[2]);
    assign next_A[3] = (update & A_comb[3]) | (~update & A[3]);

    // ================================================================
    // B_comb: valor de B si ocurre una actualizacion (load o tick)
    //
    //   load=1              --> B_comb = B_restantes  (carga el delta)
    //   load=0, enable=1    --> B_comb = B - 1
    //   load=0, enable=0    --> B_comb = B  (ya es 0, no cambia)
    // ================================================================

    wire [3:0] B_comb;
    assign B_comb[0] = (load  &  B_restantes[0])
                     | (~load &  enable  & B_minus1[0])
                     | (~load & ~enable  & B[0]);
    assign B_comb[1] = (load  &  B_restantes[1])
                     | (~load &  enable  & B_minus1[1])
                     | (~load & ~enable  & B[1]);
    assign B_comb[2] = (load  &  B_restantes[2])
                     | (~load &  enable  & B_minus1[2])
                     | (~load & ~enable  & B[2]);
    assign B_comb[3] = (load  &  B_restantes[3])
                     | (~load &  enable  & B_minus1[3])
                     | (~load & ~enable  & B[3]);

    // next_B: B_comb si hay actualizacion; B sin cambio si no next_B[i] = (update & B_comb[i]) | (~update & B[i])
    wire [3:0] next_B;
    assign next_B[0] = (update & B_comb[0]) | (~update & B[0]);
    assign next_B[1] = (update & B_comb[1]) | (~update & B[1]);
    assign next_B[2] = (update & B_comb[2]) | (~update & B[2]);
    assign next_B[3] = (update & B_comb[3]) | (~update & B[3]);

    // Flip-flops de A y B — template minimo estructural
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            A <= 4'b0001;
            B <= 4'b0000;
        end else begin
            A <= next_A;
            B <= next_B;
        end
    end

    // ================================================================
    // FLAG active y OUTPUT done
    //
    // active: se activa con load y se mantiene hasta reset next_active = load | active
    // done = 1 cuando hubo al menos un load y B == 0 done = active & ~enable
    // ================================================================

    reg  active;
    wire next_active;
    assign next_active = load | active;

    // Flip-flop de active — template minimo estructural
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) active <= 1'b0;
        else        active <= next_active;
    end

    assign done = active & ~enable;

    // ================================================================
    // PWM LEVEL — 3 bits, ecuaciones booleanas
    // Tabla: B=0→000(0%) B=1→001(25%) B=2,3→010(50%)
    //        B=4→011(75%) B>=5→100(100%)
    // ================================================================

    wire B_ge5;
    assign B_ge5 = B[3] | (B[2] & B[1]) | (B[2] & B[0]);

    assign pwm_level[2] = B_ge5;
    assign pwm_level[1] = (~B[3] & ~B[2] &  B[1])
                        | (~B[3] &  B[2] & ~B[1] & ~B[0]);
    assign pwm_level[0] = (~B[3] & ~B[2] &  B[0])
                        | (~B[3] &  B[2] & ~B[1] & ~B[0]);

    // ================================================================
    // DECODER 7 SEGMENTOS {g,f,e,d,c,b,a} — ecuaciones booleanas
    // Muestra piso_actual (A) en hexadecimal: 0–F
    // ================================================================

    wire [6:0] seg_out;

    // Segmento a (seg_out[0]): apagado en 1 y 4
    assign seg_out[0] = ~(~A[3] & ~A[2] & ~A[1] &  A[0]) &
                        ~(~A[3] &  A[2] & ~A[1] & ~A[0]);

    // Segmento b (seg_out[1]): apagado en 5, 6, B, D
    assign seg_out[1] = ~(~A[3] & ~A[2] &  A[1] &  A[0]) &
                        ~(~A[3] &  A[2] &  A[1] & ~A[0]) &
                        ~( A[3] & ~A[2] &  A[1] &  A[0]) &
                        ~( A[3] &  A[2] &  A[1] & ~A[0]);

    // Segmento c (seg_out[2]): apagado en 2
    assign seg_out[2] = ~(~A[3] & ~A[2] &  A[1] & ~A[0]);

    // Segmento d (seg_out[3]): apagado en 1, 4, 7, A, F
    assign seg_out[3] = ~(~A[3] & ~A[2] & ~A[1] &  A[0]) &
                        ~(~A[3] &  A[2] & ~A[1] & ~A[0]) &
                        ~(~A[3] &  A[2] &  A[1] &  A[0]) &
                        ~( A[3] & ~A[2] &  A[1] & ~A[0]) &
                        ~( A[3] &  A[2] &  A[1] &  A[0]);

    // Segmento e (seg_out[4]): apagado en 1, 3, 4, 5, 7, 9
    assign seg_out[4] = ~(~A[3] & ~A[2] & ~A[1] &  A[0]) &
                        ~(~A[3] & ~A[2] &  A[1] &  A[0]) &
                        ~(~A[3] &  A[2] & ~A[1] & ~A[0]) &
                        ~(~A[3] &  A[2] & ~A[1] &  A[0]) &
                        ~(~A[3] &  A[2] &  A[1] &  A[0]) &
                        ~( A[3] & ~A[2] & ~A[1] &  A[0]);

    // Segmento f (seg_out[5]): apagado en 1, 2, 3, 7
    assign seg_out[5] = ~(~A[3] & ~A[2] & ~A[1] &  A[0]) &
                        ~(~A[3] & ~A[2] &  A[1] & ~A[0]) &
                        ~(~A[3] & ~A[2] &  A[1] &  A[0]) &
                        ~(~A[3] &  A[2] &  A[1] &  A[0]);

    // Segmento g (seg_out[6]): apagado en 0, 1, 7
    assign seg_out[6] = ~(~A[3] & ~A[2] & ~A[1] & ~A[0]) &
                        ~(~A[3] & ~A[2] & ~A[1] &  A[0]) &
                        ~(~A[3] &  A[2] &  A[1] &  A[0]);

    // Display de anodo comun: segmento activo = 0
    assign seg = ~seg_out;

endmodule
