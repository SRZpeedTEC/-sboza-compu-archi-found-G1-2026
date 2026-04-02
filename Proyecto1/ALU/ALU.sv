// =============================================================================
// ALU — Controlador estructural de movimiento del elevador
//
// Flujo de operacion:
//   1. FSM pulsa 'load' 1 ciclo con piso_init, pisos_delta y op
//   2. ALU calcula B_restantes (saturado si delta desborda rango 0-F)
//   3. Cada segundo (tick), el elevador avanza un piso y B decrementa
//   4. Al llegar B=0, 'done' pulsa exactamente 1 ciclo
//
// Interfaz:
//   load        — pulso de 1 ciclo. Ignorado si ALU esta en movimiento.
//   op          — 0=subir, 1=bajar. Debe mantenerse estable hasta done.
//   piso_init   — piso de partida. Debe mantenerse estable hasta done.
//   pisos_delta — pisos a recorrer. Saturado internamente si desborda.
//   done        — pulso de 1 ciclo al completar el movimiento.
//
// =============================================================================

module ALU #(
    parameter integer CLK_FREQ = 50_000_000
)(
    input        clk,
    input        reset,
    input  [3:0] piso_init,
    input  [3:0] pisos_delta,
    input        load,
    input        op,
    output [3:0] piso_actual,
    output [2:0] pwm_level,
    output [6:0] seg,
    output       done
);

    // -------------------------------------------------------------------------
    // Parametros internos
    // -------------------------------------------------------------------------
    localparam integer TIMER_MAX  = CLK_FREQ - 1;
    localparam integer TIMER_BITS = $clog2(CLK_FREQ);

    // -------------------------------------------------------------------------
    // Registros
    // -------------------------------------------------------------------------
    reg [TIMER_BITS-1:0] timer;   // Contador para generar tick cada 1 segundo
    reg [3:0]            A;       // Piso actual
    reg [3:0]            B;       // Pasos restantes
    reg                  active;  // 1 mientras hay movimiento en curso

    assign piso_actual = A;

    // -------------------------------------------------------------------------
    // Flags de estado
    // enable: B != 0 (hay pasos pendientes)
    // hold_A: A no debe avanzar (saturacion de piso alcanzada)
    // -------------------------------------------------------------------------
    wire enable;
    assign enable = B[3] | B[2] | B[1] | B[0];

    wire A_eq_max, A_eq_min;  // Vienen de ALU_Adder y ALU_Substractor

    wire hold_A;
    assign hold_A = (~enable)
                  | (~op & enable & A_eq_max)   // Subiendo, techo alcanzado
                  | ( op & enable & A_eq_min);  // Bajando, piso minimo alcanzado

    // -------------------------------------------------------------------------
    // load_safe: descarta load si la ALU esta activa (active & enable)
    // -------------------------------------------------------------------------
    wire load_safe;
    assign load_safe = load & ~(active & enable);

    // -------------------------------------------------------------------------
    // Timer: genera tick cada CLK_FREQ ciclos (1 segundo)
    // reset_timer: se reinicia en load_safe o al completar 1 segundo
    // next_timer:  mascareo con {~reset_timer} para forzar 0 sin mux explicito
    // -------------------------------------------------------------------------
    wire tick;
    assign tick = (timer == TIMER_MAX);

    wire [TIMER_BITS-1:0] timer_inc;
    assign timer_inc = timer + 1'b1;

    wire reset_timer;
    assign reset_timer = load_safe | tick;

    wire [TIMER_BITS-1:0] next_timer;
    assign next_timer = {TIMER_BITS{~reset_timer}} & timer_inc;

    always @(posedge clk or posedge reset)
        if (reset) timer <= {TIMER_BITS{1'b0}};
        else       timer <= next_timer;

    // -------------------------------------------------------------------------
    // Instancias: calculo de A+-1, B_restantes y flags de saturacion
    // -------------------------------------------------------------------------
    wire [3:0] A_plus1,  B_ef_add;
    wire [3:0] A_minus1, B_ef_sub;

    ALU_Adder adder (
        .piso_init   (piso_init),
        .pisos_subir (pisos_delta),
        .A_reg       (A),
        .A_plus1     (A_plus1),
        .A_eq_max    (A_eq_max),
        .B_restantes (B_ef_add)
    );

    ALU_Substractor substractor (
        .piso_init   (piso_init),
        .pisos_bajar (pisos_delta),
        .A_reg       (A),
        .A_minus1    (A_minus1),
        .A_eq_min    (A_eq_min),
        .B_restantes (B_ef_sub)
    );

    // -------------------------------------------------------------------------
    // MUX op: selecciona resultado de Adder (op=0) o Substractor (op=1)
    // -------------------------------------------------------------------------
    wire [3:0] step_A;
    assign step_A[0] = (~op & A_plus1[0]) | (op & A_minus1[0]);
    assign step_A[1] = (~op & A_plus1[1]) | (op & A_minus1[1]);
    assign step_A[2] = (~op & A_plus1[2]) | (op & A_minus1[2]);
    assign step_A[3] = (~op & A_plus1[3]) | (op & A_minus1[3]);

    wire [3:0] B_restantes;  // Pasos efectivos tras saturacion de entrada
    assign B_restantes[0] = (~op & B_ef_add[0]) | (op & B_ef_sub[0]);
    assign B_restantes[1] = (~op & B_ef_add[1]) | (op & B_ef_sub[1]);
    assign B_restantes[2] = (~op & B_ef_add[2]) | (op & B_ef_sub[2]);
    assign B_restantes[3] = (~op & B_ef_add[3]) | (op & B_ef_sub[3]);

    // -------------------------------------------------------------------------
    // B - 1: restador ripple-borrow
    // -------------------------------------------------------------------------
    wire [3:0] B_minus1;
    wire       bw0, bw1, bw2;
    assign B_minus1[0] = B[0] ^ 1'b1;
    assign bw0          = ~B[0];
    assign B_minus1[1] = B[1] ^ bw0;
    assign bw1          = ~B[1] & bw0;
    assign B_minus1[2] = B[2] ^ bw1;
    assign bw2          = ~B[2] & bw1;
    assign B_minus1[3] = B[3] ^ bw2;

    // -------------------------------------------------------------------------
    // Logica combinacional de A — MUX 3:1
    //   load_safe=1 -> piso_init  (nuevo arranque)
    //   hold_A=1    -> A          (red de seguridad ante saturacion)
    //   else        -> step_A     (avanza un piso)
    // update: A y B solo cambian en load_safe o tick
    // -------------------------------------------------------------------------
    wire update;
    assign update = load_safe | tick;

    wire [3:0] A_comb;
    assign A_comb[0] = ( load_safe & piso_init[0])
                     | (~load_safe & ~hold_A & step_A[0])
                     | (~load_safe &  hold_A & A[0]);
    assign A_comb[1] = ( load_safe & piso_init[1])
                     | (~load_safe & ~hold_A & step_A[1])
                     | (~load_safe &  hold_A & A[1]);
    assign A_comb[2] = ( load_safe & piso_init[2])
                     | (~load_safe & ~hold_A & step_A[2])
                     | (~load_safe &  hold_A & A[2]);
    assign A_comb[3] = ( load_safe & piso_init[3])
                     | (~load_safe & ~hold_A & step_A[3])
                     | (~load_safe &  hold_A & A[3]);

    wire [3:0] next_A;
    assign next_A[0] = (update & A_comb[0]) | (~update & A[0]);
    assign next_A[1] = (update & A_comb[1]) | (~update & A[1]);
    assign next_A[2] = (update & A_comb[2]) | (~update & A[2]);
    assign next_A[3] = (update & A_comb[3]) | (~update & A[3]);

    // -------------------------------------------------------------------------
    // Logica combinacional de B — MUX 3:1
    //   load_safe=1 -> B_restantes  (nuevo arranque, valor ya saturado)
    //   enable=1    -> B-1          (decrementa cada tick)
    //   else        -> B            (B=0, sin cambio)
    // B decrementa con enable independientemente de hold_A.
    // La saturacion de entrada garantiza que B se agota cuando A llega al limite.
    // -------------------------------------------------------------------------
    wire [3:0] B_comb;
    assign B_comb[0] = ( load_safe &  B_restantes[0])
                     | (~load_safe &  enable & B_minus1[0])
                     | (~load_safe & ~enable & B[0]);
    assign B_comb[1] = ( load_safe &  B_restantes[1])
                     | (~load_safe &  enable & B_minus1[1])
                     | (~load_safe & ~enable & B[1]);
    assign B_comb[2] = ( load_safe &  B_restantes[2])
                     | (~load_safe &  enable & B_minus1[2])
                     | (~load_safe & ~enable & B[2]);
    assign B_comb[3] = ( load_safe &  B_restantes[3])
                     | (~load_safe &  enable & B_minus1[3])
                     | (~load_safe & ~enable & B[3]);

    wire [3:0] next_B;
    assign next_B[0] = (update & B_comb[0]) | (~update & B[0]);
    assign next_B[1] = (update & B_comb[1]) | (~update & B[1]);
    assign next_B[2] = (update & B_comb[2]) | (~update & B[2]);
    assign next_B[3] = (update & B_comb[3]) | (~update & B[3]);

    always @(posedge clk or posedge reset)
        if (reset) begin
            A <= 4'b0001;
            B <= 4'b0000;
        end else begin
            A <= next_A;
            B <= next_B;
        end

    // -------------------------------------------------------------------------
    // Flag active y salida done
    // active: sube con load_safe, cae cuando B llega a 0 (enable=0)
    // done:   pulsa exactamente 1 ciclo cuando active=1 y enable=0
    // -------------------------------------------------------------------------
    wire next_active;
    assign next_active = load_safe | (active & enable);

    always @(posedge clk or posedge reset)
        if (reset) active <= 1'b0;
        else       active <= next_active;

    assign done = active & ~enable;

    // -------------------------------------------------------------------------
    // PWM level — 3 bits proporcionales a B
    //   B=0 -> 000  B=1 -> 001  B=2,3 -> 010  B=4 -> 011  B>=5 -> 100
    // -------------------------------------------------------------------------
    wire B_ge5;
    assign B_ge5 = B[3] | (B[2] & B[1]) | (B[2] & B[0]);

    assign pwm_level[2] = B_ge5;
    assign pwm_level[1] = (~B[3] & ~B[2] &  B[1])
                        | (~B[3] &  B[2] & ~B[1] & ~B[0]);
    assign pwm_level[0] = (~B[3] & ~B[2] & ~B[1] &  B[0])   // B=1
                        | (~B[3] &  B[2] & ~B[1] & ~B[0]);   // B=4

    // -------------------------------------------------------------------------
    // Decoder 7 segmentos — anodo comun, muestra A en hex (0-F)
    // seg_out en logica positiva (1=encendido), invertido al final para anodo comun
    // -------------------------------------------------------------------------
    wire [6:0] seg_out;

    assign seg_out[0] = ~(~A[3] & ~A[2] & ~A[1] &  A[0])    // 1
                      & ~(~A[3] &  A[2] & ~A[1] & ~A[0]);   // 4

    assign seg_out[1] = ~(~A[3] & ~A[2] &  A[1] &  A[0])    // 3
                      & ~(~A[3] &  A[2] &  A[1] & ~A[0])    // 6
                      & ~( A[3] & ~A[2] &  A[1] &  A[0])    // B
                      & ~( A[3] &  A[2] &  A[1] & ~A[0]);   // E

    assign seg_out[2] = ~(~A[3] & ~A[2] &  A[1] & ~A[0]);   // 2

    assign seg_out[3] = ~(~A[3] & ~A[2] & ~A[1] &  A[0])    // 1
                      & ~(~A[3] &  A[2] & ~A[1] & ~A[0])    // 4
                      & ~(~A[3] &  A[2] &  A[1] &  A[0])    // 7
                      & ~( A[3] & ~A[2] &  A[1] & ~A[0])    // A
                      & ~( A[3] &  A[2] &  A[1] &  A[0]);   // F

    assign seg_out[4] = ~(~A[3] & ~A[2] & ~A[1] &  A[0])    // 1
                      & ~(~A[3] & ~A[2] &  A[1] &  A[0])    // 3
                      & ~(~A[3] &  A[2] & ~A[1] & ~A[0])    // 4
                      & ~(~A[3] &  A[2] & ~A[1] &  A[0])    // 5
                      & ~(~A[3] &  A[2] &  A[1] &  A[0])    // 7
                      & ~( A[3] & ~A[2] & ~A[1] &  A[0]);   // 9

    assign seg_out[5] = ~(~A[3] & ~A[2] & ~A[1] &  A[0])    // 1
                      & ~(~A[3] & ~A[2] &  A[1] & ~A[0])    // 2
                      & ~(~A[3] & ~A[2] &  A[1] &  A[0])    // 3
                      & ~(~A[3] &  A[2] &  A[1] &  A[0]);   // 7

    assign seg_out[6] = ~(~A[3] & ~A[2] & ~A[1] & ~A[0])    // 0
                      & ~(~A[3] & ~A[2] & ~A[1] &  A[0])    // 1
                      & ~(~A[3] &  A[2] &  A[1] &  A[0]);   // 7

    assign seg = ~seg_out;

endmodule