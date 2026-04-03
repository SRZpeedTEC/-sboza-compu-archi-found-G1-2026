// =============================================================================
// eq_comparator — Comparador de igualdad estructural de N bits
//
// Reemplaza el operador == con logica booleana pura.
// Cada bit se compara con XNOR: resultado 1 si ambos bits son iguales.
// La cadena de ANDs produce 1 unicamente cuando todos los bits son iguales.
//
// =============================================================================

module eq_comparator #(
    parameter integer WIDTH = 26
)(
    input  logic [WIDTH-1:0] a,
    input  logic [WIDTH-1:0] b,
    output logic             eq
);

    // -------------------------------------------------------------------------
    // XNOR bit a bit — eq_bits[i]=1 cuando a[i]==b[i]
    // -------------------------------------------------------------------------
    wire [WIDTH-1:0] eq_bits;

    genvar i;
    generate
        for (i = 0; i < WIDTH; i++) begin : xnor_chain
            assign eq_bits[i] = a[i] ~^ b[i];
        end
    endgenerate

    // -------------------------------------------------------------------------
    // AND chain — reduce eq_bits a un solo bit
    // Implementado como cadena de ANDs de 2 entradas con generate for
    // -------------------------------------------------------------------------
    wire [WIDTH-1:0] and_chain;

    assign and_chain[0] = eq_bits[0];

    generate
        for (i = 1; i < WIDTH; i++) begin : and_reduction
            assign and_chain[i] = and_chain[i-1] & eq_bits[i];
        end
    endgenerate

    assign eq = and_chain[WIDTH-1];

endmodule