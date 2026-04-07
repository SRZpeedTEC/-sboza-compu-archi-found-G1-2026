// =============================================================================
// elevator_fsm — FSM principal del sistema de elevador controlado por aplausos
//
// Flujo de estados:
//   IDLE -> BEEP1 -> READOP -> BEEP2 -> READBIT0 -> READBIT1 ->
//   READBIT2 -> READBIT3 -> BEEP3 -> START_MOVEMENT -> WAIT_MOVEMENT -> IDLE
//
// Interfaces externas:
//   mic_top  : activate_mic, mode_mic  (inputs: init_system, mic_done)
//   buzzer   : activate_buz, buzzer_mode (input: buzzer_done)
//   ALU      : load                    (input: done)
// =============================================================================

module elevator_fsm (
    input  logic        clk,
    input  logic        reset,
    // From mic_top
    input  logic        init_system,
    input  logic        mic_done,
    // From buzzer
    input  logic        buzzer_done,
    // From ALU
    input  logic        done,
    // To mic_top
    output logic        activate_mic,
    output logic [2:0]  mode_mic,
    // To buzzer
    output logic        activate_buz,
    output logic [1:0]  buzzer_mode,
    // To ALU
    output logic        load
);

    // -------------------------------------------------------------------------
    // Codificacion one-hot — 1 bit por estado
    // -------------------------------------------------------------------------
    localparam integer IDLE           = 0;
    localparam integer BEEP1          = 1;
    localparam integer READOP         = 2;
    localparam integer BEEP2          = 3;
    localparam integer READBIT0       = 4;
    localparam integer READBIT1       = 5;
    localparam integer READBIT2       = 6;
    localparam integer READBIT3       = 7;
    localparam integer BEEP3          = 8;
    localparam integer START_MOVEMENT = 9;
    localparam integer WAIT_MOVEMENT  = 10;

    // -------------------------------------------------------------------------
    // Vector de estado: 11 bits, uno por estado
    // Reset arranca en IDLE: state[0]=1, resto=0
    // -------------------------------------------------------------------------
    logic [10:0] state;
    logic [10:0] next_state;

    always_ff @(posedge clk or posedge reset)
        if (reset) state <= 11'b00000000001;
        else       state <= next_state;

    // -------------------------------------------------------------------------
    // Ecuaciones de next_state 
    // -------------------------------------------------------------------------

    // IDLE: se queda si init_system=0, regresa desde WAIT_MOVEMENT si done=1
    assign next_state[IDLE] = (state[IDLE] & ~init_system)
                            | (state[WAIT_MOVEMENT] & done);

    // BEEP1: llega desde IDLE cuando init_system=1
    assign next_state[BEEP1] = (state[IDLE] & init_system)
                          | (state[BEEP1] & ~buzzer_done);

    // READOP: llega desde BEEP1 cuando buzzer_done=1
    assign next_state[READOP] = (state[BEEP1] & buzzer_done)
                            | (state[READOP] & ~mic_done);

    assign next_state[BEEP2] = (state[READOP] & mic_done)
                            | (state[BEEP2] & ~buzzer_done);


    assign next_state[READBIT0] = (state[BEEP2] & buzzer_done)
                                | (state[READBIT0] & ~mic_done);

    assign next_state[READBIT1] = (state[READBIT0] & mic_done)
                                | (state[READBIT1] & ~mic_done);

    assign next_state[READBIT2] = (state[READBIT1] & mic_done)
                                | (state[READBIT2] & ~mic_done);

    assign next_state[READBIT3] = (state[READBIT2] & mic_done)
                                | (state[READBIT3] & ~mic_done);

    assign next_state[BEEP3] = (state[READBIT3] & mic_done)
                            | (state[BEEP3] & ~buzzer_done);

    // START_MOVEMENT: llega desde BEEP3 cuando buzzer_done=1
    assign next_state[START_MOVEMENT] = state[BEEP3] & buzzer_done;

    // WAIT_MOVEMENT: llega desde START_MOVEMENT siempre (1 ciclo),
    // se queda mientras done=0
    assign next_state[WAIT_MOVEMENT] = state[START_MOVEMENT]
                                     | (state[WAIT_MOVEMENT] & ~done);

    // -------------------------------------------------------------------------
    // Ecuaciones de salida 
    // -------------------------------------------------------------------------

    // activate_mic: activo en IDLE y todos los estados READ
    assign activate_mic = state[IDLE]
                        | state[READOP]
                        | state[READBIT0]
                        | state[READBIT1]
                        | state[READBIT2]
                        | state[READBIT3];

    // activate_buz: activo en los tres estados BEEP
    assign activate_buz = state[BEEP1]
                        | state[BEEP2]
                        | state[BEEP3];

    // load: activo unicamente en START_MOVEMENT, genera pulso de 1 ciclo
    // por la transicion incondicional a WAIT_MOVEMENT
    assign load = state[START_MOVEMENT];

    // mode_mic: codificacion de 3 bits segun estado READ activo
    //   READOP=001  READBIT0=010  READBIT1=011
    //   READBIT2=100  READBIT3=101
    assign mode_mic[0] = state[READOP]
                       | state[READBIT1]
                       | state[READBIT3];

    assign mode_mic[1] = state[READBIT0]
                       | state[READBIT1];

    assign mode_mic[2] = state[READBIT2]
                       | state[READBIT3];

    // buzzer_mode: codificacion de 2 bits segun estado BEEP activo
    //   BEEP1=01  BEEP2=10  BEEP3=11
    assign buzzer_mode[0] = state[BEEP1]
                          | state[BEEP3];

    assign buzzer_mode[1] = state[BEEP2]
                          | state[BEEP3];

endmodule