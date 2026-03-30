// ALU_Adder: modulo de suma para el ascensor
// Entradas: piso_init (piso actual), pisos_subir (cuantos subir)
// Salidas:  A_next (siguiente piso), B_efectivo (pisos reales a recorrer)
//
// Saturacion superior: si piso_init + pisos_subir > 15
//   B_efectivo = 15 - piso_init  (solo sube lo que puede)
// A_next = piso_init + 1 por ciclo mientras B != 0
// Saturacion de A: si A == 1111 no incrementa

module ALU_Adder (
    input  [3:0] piso_init,
    input  [3:0] pisos_subir,
    input  [3:0] A_reg,        // piso actual del registro
    output [3:0] A_plus1,      // A + 1 para el registro
    output       A_eq_max,     // A == 1111
    output [3:0] B_efectivo    // pisos reales a recorrer (con saturacion)
);

    // ----------------------------------------------------------------
    // A + 1 (ripple-carry de 4 bits)
    // ----------------------------------------------------------------
    wire c0, c1, c2;
    assign A_plus1[0] = A_reg[0] ^ 1'b1;
    assign c0         = A_reg[0] & 1'b1;
    assign A_plus1[1] = A_reg[1] ^ c0;
    assign c1         = A_reg[1] & c0;
    assign A_plus1[2] = A_reg[2] ^ c1;
    assign c2         = A_reg[2] & c1;
    assign A_plus1[3] = A_reg[3] ^ c2;

    // ----------------------------------------------------------------
    // Saturacion A == 1111
    // ----------------------------------------------------------------
    assign A_eq_max = A_reg[3] & A_reg[2] & A_reg[1] & A_reg[0];

    // ----------------------------------------------------------------
    // Saturacion de entrada: piso_init + pisos_subir > 15?
    // pisos_disp = ~piso_init = 15 - piso_init
    // Si carry_up → desbordamiento → B_efectivo = pisos_disp
    // ----------------------------------------------------------------
    wire [3:0] pisos_disp;
    assign pisos_disp[0] = ~piso_init[0];
    assign pisos_disp[1] = ~piso_init[1];
    assign pisos_disp[2] = ~piso_init[2];
    assign pisos_disp[3] = ~piso_init[3];

    wire [3:0] sum_check;
    wire       carry_up;
    wire       c_ab0, c_ab1, c_ab2;
    assign sum_check[0] = piso_init[0] ^ pisos_subir[0];
    assign c_ab0         = piso_init[0] & pisos_subir[0];
    assign sum_check[1] = piso_init[1] ^ pisos_subir[1] ^ c_ab0;
    assign c_ab1         = (piso_init[1] & pisos_subir[1])
                         | (piso_init[1] & c_ab0)
                         | (pisos_subir[1] & c_ab0);
    assign sum_check[2] = piso_init[2] ^ pisos_subir[2] ^ c_ab1;
    assign c_ab2         = (piso_init[2] & pisos_subir[2])
                         | (piso_init[2] & c_ab1)
                         | (pisos_subir[2] & c_ab1);
    assign sum_check[3] = piso_init[3] ^ pisos_subir[3] ^ c_ab2;
    assign carry_up      = (piso_init[3] & pisos_subir[3])
                         | (piso_init[3] & c_ab2)
                         | (pisos_subir[3] & c_ab2);

    assign B_efectivo[0] = (carry_up & pisos_disp[0]) | (~carry_up & pisos_subir[0]);
    assign B_efectivo[1] = (carry_up & pisos_disp[1]) | (~carry_up & pisos_subir[1]);
    assign B_efectivo[2] = (carry_up & pisos_disp[2]) | (~carry_up & pisos_subir[2]);
    assign B_efectivo[3] = (carry_up & pisos_disp[3]) | (~carry_up & pisos_subir[3]);

endmodule
