// ALU: controller
// op = 0 → subir (usa Adder)
// op = 1 → bajar (usa Substractor)

module ALU (
    input        clk,
    input        rst_n,
    input  [3:0] piso_init,
    input  [3:0] pisos_delta,  // pisos a subir o bajar
    input        load,
    input        op,           // 0 = subir, 1 = bajar
    output [3:0] piso_actual,
    output [2:0] pwm_level,
    output [6:0] seg
);

    reg [3:0] A;
    reg [3:0] B;

    assign piso_actual = A;

    // ----------------------------------------------------------------
    // Instancia ALU_Adder
    // ----------------------------------------------------------------
    wire [3:0] A_plus1;
    wire       A_eq_max;
    wire [3:0] B_ef_add;

    ALU_Adder adder (
        .piso_init   (piso_init),
        .pisos_subir (pisos_delta),
        .A_reg       (A),
        .A_plus1     (A_plus1),
        .A_eq_max    (A_eq_max),
        .B_efectivo  (B_ef_add)
    );

    // ----------------------------------------------------------------
    // Instancia ALU_Substractor
    // ----------------------------------------------------------------
    wire [3:0] A_minus1;
    wire       A_eq_min;
    wire [3:0] B_ef_sub;

    ALU_Substractor substractor (
        .piso_init   (piso_init),
        .pisos_bajar (pisos_delta),
        .A_reg       (A),
        .A_minus1    (A_minus1),
        .A_eq_min    (A_eq_min),
        .B_efectivo  (B_ef_sub)
    );

    // ----------------------------------------------------------------
    // step_A  = A+1 si op=0, A-1 si op=1
    // B_efectivo = B_ef_add si op=0, B_ef_sub si op=1
    // hold_A = 1 si no debe moverse
    // ----------------------------------------------------------------
    wire [3:0] step_A;
    assign step_A[0] = (~op & A_plus1[0])  | (op & A_minus1[0]);
    assign step_A[1] = (~op & A_plus1[1])  | (op & A_minus1[1]);
    assign step_A[2] = (~op & A_plus1[2])  | (op & A_minus1[2]);
    assign step_A[3] = (~op & A_plus1[3])  | (op & A_minus1[3]);

    wire [3:0] B_efectivo;
    assign B_efectivo[0] = (~op & B_ef_add[0]) | (op & B_ef_sub[0]);
    assign B_efectivo[1] = (~op & B_ef_add[1]) | (op & B_ef_sub[1]);
    assign B_efectivo[2] = (~op & B_ef_add[2]) | (op & B_ef_sub[2]);
    assign B_efectivo[3] = (~op & B_ef_add[3]) | (op & B_ef_sub[3]);

    // enable: B != 0
    wire enable;
    assign enable = B[3] | B[2] | B[1] | B[0];

    // hold_A: satura segun direccion
    wire hold_A;
    assign hold_A = (~enable)
                  | (~op & enable & A_eq_max)
                  | ( op & enable & A_eq_min);

    // ----------------------------------------------------------------
    // next_A
    // ----------------------------------------------------------------
    wire [3:0] next_A;
    assign next_A[0] = (load & piso_init[0])
                     | (~load & enable & ~hold_A & step_A[0])
                     | (~load & hold_A & A[0]);
    assign next_A[1] = (load & piso_init[1])
                     | (~load & enable & ~hold_A & step_A[1])
                     | (~load & hold_A & A[1]);
    assign next_A[2] = (load & piso_init[2])
                     | (~load & enable & ~hold_A & step_A[2])
                     | (~load & hold_A & A[2]);
    assign next_A[3] = (load & piso_init[3])
                     | (~load & enable & ~hold_A & step_A[3])
                     | (~load & hold_A & A[3]);

    // ----------------------------------------------------------------
    // B - 1 
    // ----------------------------------------------------------------
    wire [3:0] B_minus1;
    wire b0, b1, b2;
    assign B_minus1[0] = B[0] ^ 1'b1;
    assign b0           = ~B[0];
    assign B_minus1[1] = B[1] ^ b0;
    assign b1           = ~B[1] & b0;
    assign B_minus1[2] = B[2] ^ b1;
    assign b2           = ~B[2] & b1;
    assign B_minus1[3] = B[3] ^ b2;

    // ----------------------------------------------------------------
    // next_B
    // ----------------------------------------------------------------
    wire [3:0] next_B;
    assign next_B[0] = (load & B_efectivo[0])
                     | (~load & enable  & B_minus1[0])
                     | (~load & ~enable & B[0]);
    assign next_B[1] = (load & B_efectivo[1])
                     | (~load & enable  & B_minus1[1])
                     | (~load & ~enable & B[1]);
    assign next_B[2] = (load & B_efectivo[2])
                     | (~load & enable  & B_minus1[2])
                     | (~load & ~enable & B[2]);
    assign next_B[3] = (load & B_efectivo[3])
                     | (~load & enable  & B_minus1[3])
                     | (~load & ~enable & B[3]);

    // ----------------------------------------------------------------
    // Registros secuenciales
    // ----------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            A <= 4'b0001;
            B <= 4'b0000;
        end else begin
            A <= next_A;
            B <= next_B;
        end
    end

    // ----------------------------------------------------------------
    // PWM level: 3 bits 
    // 000=0%  001=25%  010=50%  011=75%  100=100%
    // ----------------------------------------------------------------
    wire B_ge5;
    assign B_ge5 = B[3] | (B[2] & B[1]) | (B[2] & B[0]);

    assign pwm_level[2] = B_ge5;
    assign pwm_level[1] = (~B[3] & ~B[2] &  B[1])
                        | (~B[3] &  B[2] & ~B[1] & ~B[0]);
    assign pwm_level[0] = (~B[3] & ~B[2] &  B[0])
                        | (~B[3] &  B[2] & ~B[1] & ~B[0]);

    // ----------------------------------------------------------------
    // Decoder 7 segmentos {g,f,e,d,c,b,a} 
    // ----------------------------------------------------------------
    wire [6:0] seg_out;

    assign seg_out[0] = ~(~A[3]&~A[2]&~A[1]& A[0]) &
                        ~(~A[3]& A[2]&~A[1]&~A[0]);
    assign seg_out[1] = ~(~A[3]&~A[2]& A[1]& A[0]) &
                        ~(~A[3]& A[2]& A[1]&~A[0]) &
                        ~( A[3]&~A[2]& A[1]& A[0]) &
                        ~( A[3]& A[2]& A[1]&~A[0]);
    assign seg_out[2] = ~(~A[3]&~A[2]& A[1]&~A[0]);
    assign seg_out[3] = ~(~A[3]&~A[2]&~A[1]& A[0]) &
                        ~(~A[3]& A[2]&~A[1]&~A[0]) &
                        ~(~A[3]& A[2]& A[1]& A[0]) &
                        ~( A[3]&~A[2]& A[1]&~A[0]) &
                        ~( A[3]& A[2]& A[1]& A[0]);
    assign seg_out[4] = ~(~A[3]&~A[2]&~A[1]& A[0]) &
                        ~(~A[3]&~A[2]& A[1]& A[0]) &
                        ~(~A[3]& A[2]&~A[1]&~A[0]) &
                        ~(~A[3]& A[2]&~A[1]& A[0]) &
                        ~(~A[3]& A[2]& A[1]& A[0]) &
                        ~( A[3]&~A[2]&~A[1]& A[0]);
    assign seg_out[5] = ~(~A[3]&~A[2]&~A[1]& A[0]) &
                        ~(~A[3]&~A[2]& A[1]&~A[0]) &
                        ~(~A[3]&~A[2]& A[1]& A[0]) &
                        ~(~A[3]& A[2]& A[1]& A[0]);
    assign seg_out[6] = ~(~A[3]&~A[2]&~A[1]&~A[0]) &
                        ~(~A[3]&~A[2]&~A[1]& A[0]) &
                        ~(~A[3]& A[2]& A[1]& A[0]);

    assign seg = ~seg_out;

endmodule
