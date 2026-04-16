// =============================================================================
// mic_demo — Wrapper de mic_top para demo en FPGA
//
// Reemplaza el microfono fisico con un boton con debounce.
//
// Instancias:
//   u_debounce : debounce  — filtra rebote del boton
//   u_mic_top  : mic_top   — logica original sin modificar
//
// Puertos externos:
//   btn_clap     : boton fisico que simula aplauso
//   clap_led     : LED[2] — pulso visible al registrar aplauso
//   listening_led: LED[1] — encendido durante ventana de escucha
// =============================================================================
module mic_demo #(
    parameter int unsigned CLK_FREQ_HZ   = 50_000_000,
    parameter int unsigned LISTEN_TIME_MS = 4000,
    parameter int unsigned DEBOUNCE_MS    = 20
)(
    input  logic        clk,
    input  logic        reset,
    input  logic        activate_mic,
    input  logic [2:0]  mode_mic,
    input  logic        btn_clap,
    output logic        mic_done,
    output logic        init_system,
    output logic        listening_led,
    output logic        clap_led,
    output logic        dir_reg,
    output logic [3:0]  num_reg
);

    // -------------------------------------------------------------------------
    // Wire interno: salida limpia del debounce hacia clap_event de mic_top
    // -------------------------------------------------------------------------
    logic clap_clean;

    // -------------------------------------------------------------------------
    // Debounce del boton
    // -------------------------------------------------------------------------
    debounce #(
        .CLK_FREQ   (CLK_FREQ_HZ),
        .DEBOUNCE_MS(DEBOUNCE_MS)
    ) u_debounce (
        .clk    (clk),
        .reset  (reset),
        .btn_in (btn_clap),
        .btn_out(clap_clean)
    );

    // -------------------------------------------------------------------------
    // mic_top original sin modificar
    // -------------------------------------------------------------------------
    mic_top #(
        .CLK_FREQ_HZ   (CLK_FREQ_HZ),
        .LISTEN_TIME_MS(LISTEN_TIME_MS)
    ) u_mic_top (
        .clk         (clk),
        .reset       (reset),
        .activate_mic(activate_mic),
        .clap_event  (clap_clean),
        .mode_mic    (mode_mic),
        .mic_done    (mic_done),
        .init_system (init_system),
        .listening_led(listening_led),
        .dir_reg     (dir_reg),
        .num_reg     (num_reg)
    );

    // -------------------------------------------------------------------------
    // clap_led: refleja la señal limpia del boton
    // -------------------------------------------------------------------------
    assign clap_led = clap_clean;

endmodule