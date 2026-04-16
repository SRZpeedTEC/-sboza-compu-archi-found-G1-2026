// =============================================================================
// incrementer — Suma 1 a la entrada (estructural)
//
// Parámetros:
//   WIDTH : ancho del dato en bits (default 26)
//
// Puertos:
//   in  : valor actual
//   out : valor actual + 1
//
// Implementación:
//   Cadena de semi-sumadores ripple-carry contra la constante 1.
//   Bit 0 : out[0]   = in[0] ^ 1  =  ~in[0]
//           carry[0] = in[0] &  1  =   in[0]
//   Bit i : out[i]   = in[i] ^ carry[i-1]   (XOR)
//           carry[i] = in[i] & carry[i-1]   (AND)
// =============================================================================

module incrementer #(
    parameter integer WIDTH = 26
)(
    input  logic [WIDTH-1:0] in,
    output logic [WIDTH-1:0] out
);

    wire [WIDTH-1:0] carry;

    // Bit 0: XOR con 1 constante = NOT; carry = AND con 1 = in[0]
    assign out[0]   = ~in[0];
    assign carry[0] =  in[0];

    genvar i;
    generate
        for (i = 1; i < WIDTH; i++) begin : ripple_carry
            assign out[i]   = in[i] ^ carry[i-1]; // XOR
            assign carry[i] = in[i] & carry[i-1]; // AND
        end
    endgenerate

endmodule
