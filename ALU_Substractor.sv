// ALU_Substractor
// Entradas: piso_init (piso actual), pisos_bajar
// Salidas:  A_minus1, A_eq_min, B_efectivo

// Saturacion inferior: si pisos_bajar > piso_init
//   B_efectivo = piso_init  (solo baja lo que puede)

module ALU_Substractor (
    input  [3:0] piso_init,
    input  [3:0] pisos_bajar,
    input  [3:0] A_reg,
    output [3:0] A_minus1,
    output       A_eq_min,
    output [3:0] B_efectivo
);

    // ----------------------------------------------------------------
    // A - 1 (borrow propagado)
    // ----------------------------------------------------------------
    wire d0, d1, d2;
    assign A_minus1[0] = A_reg[0] ^ 1'b1;
    assign d0           = ~A_reg[0];
    assign A_minus1[1] = A_reg[1] ^ d0;
    assign d1           = ~A_reg[1] & d0;
    assign A_minus1[2] = A_reg[2] ^ d1;
    assign d2           = ~A_reg[2] & d1;
    assign A_minus1[3] = A_reg[3] ^ d2;

    // ----------------------------------------------------------------
    // Saturacion A == 0000
    // ----------------------------------------------------------------
    assign A_eq_min = ~A_reg[3] & ~A_reg[2] & ~A_reg[1] & ~A_reg[0];

    // ----------------------------------------------------------------
    // Deteccion de underflow: piso_init - pisos_bajar
    // borrow propagado desde bit 0 hasta bit 3
    // Si borrow_3 sale del bit 3 → pisos_bajar > piso_init
    // ----------------------------------------------------------------
    wire [3:0] diff;
    wire       br0, br1, br2, br3;

    assign diff[0] = piso_init[0] ^ pisos_bajar[0];
    assign br0      = (~piso_init[0] & pisos_bajar[0]);

    assign diff[1] = piso_init[1] ^ pisos_bajar[1] ^ br0;
    assign br1      = (~piso_init[1] & pisos_bajar[1])
                    | (~piso_init[1] & br0)
                    | ( pisos_bajar[1] & br0);

    assign diff[2] = piso_init[2] ^ pisos_bajar[2] ^ br1;
    assign br2      = (~piso_init[2] & pisos_bajar[2])
                    | (~piso_init[2] & br1)
                    | ( pisos_bajar[2] & br1);

    assign diff[3] = piso_init[3] ^ pisos_bajar[3] ^ br2;
    assign br3      = (~piso_init[3] & pisos_bajar[3])
                    | (~piso_init[3] & br2)
                    | ( pisos_bajar[3] & br2);

    // br3 = 1 → underflow → B_efectivo = piso_init
    // br3 = 0 → normal    → B_efectivo = pisos_bajar
    assign B_efectivo[0] = (br3 & piso_init[0]) | (~br3 & pisos_bajar[0]);
    assign B_efectivo[1] = (br3 & piso_init[1]) | (~br3 & pisos_bajar[1]);
    assign B_efectivo[2] = (br3 & piso_init[2]) | (~br3 & pisos_bajar[2]);
    assign B_efectivo[3] = (br3 & piso_init[3]) | (~br3 & pisos_bajar[3]);

endmodule