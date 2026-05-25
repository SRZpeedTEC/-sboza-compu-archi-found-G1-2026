from dataclasses import dataclass

from PySide6.QtGui import QColor


@dataclass(frozen=True)
class DatapathTheme:
    background: str = "transparent"
    module_fill: str = "#ffffff"
    inactive_fill: str = "#f8f9ff"
    active_fill: str = "#ffeaf4"
    inactive_border: str = "#d9e2ff"
    path: str = "#b8c4e8"
    text: str = "#44506b"
    muted_text: str = "#9aa3c7"
    title_text: str = "#2f3b5f"

    # --- Pipeline (aditivo): campos nuevos con default, no rompen al Uniciclo ---
    forward_path: str = "#f5a623"        # flechas de forwarding (ambar)
    stall_fill: str = "#ffd5d5"          # burbuja / stall (rojo suave)
    flush_fill: str = "#ffe3a8"          # etapas en flush (ambar suave)
    pipe_register_fill: str = "#e9eefc"  # relleno de las barreras de registro
    pipe_register_text: str = "#55639a"  # texto dentro de las barreras


def color_with_alpha(color: str, alpha: int) -> QColor:
    qcolor = QColor(color)
    qcolor.setAlpha(alpha)
    return qcolor


SINGLE_CYCLE_ABSTRACT_LAYOUT = {
    "control_unit": {"x": 345, "y": 12, "w": 250, "h": 118},
    "pc_src_mux": {"x": 16, "y": 148, "w": 96, "h": 122},
    "pc": {"x": 138, "y": 158, "w": 96, "h": 104},
    "instruction_memory": {"x": 260, "y": 146, "w": 150, "h": 126},
    "register_file": {"x": 444, "y": 146, "w": 160, "h": 126},
    "alu_src_mux": {"x": 650, "y": 148, "w": 100, "h": 122},
    "alu": {"x": 790, "y": 146, "w": 150, "h": 126},
    "data_memory": {"x": 980, "y": 146, "w": 150, "h": 126},
    "result_src_mux": {"x": 1170, "y": 148, "w": 104, "h": 122},
    "immediate": {"x": 632, "y": 282, "w": 170, "h": 66},
}

SINGLE_CYCLE_CONTENT_WIDTH = 1290
SINGLE_CYCLE_CONTENT_HEIGHT = 360


# === Pipeline (Forwarding / Stalls) =========================================
# Datapath a nivel de componente (como el Uniciclo) repartido en las 5 etapas,
# con la Unidad de Control arriba, las 4 barreras de registro entre etapas y las
# dos unidades de control de riesgos abajo. Componentes pegados (gaps cortos)
# para que los cables de datos sean tramos cortos.
#
#   pc_src_mux pc imem |IF/ID| regfile immediate |ID/EX| alu_src_mux alu |EX/MEM|
#                       data_memory |MEM/WB| result_src_mux
PIPELINE_CONTENT_WIDTH = 1360
PIPELINE_CONTENT_HEIGHT = 545

PIPELINE_ABSTRACT_LAYOUT = {
    # --- Unidad de control (arriba, reparte senales hacia abajo) ---
    "control_unit":       {"x": 395,  "y": 4,   "w": 466, "h": 104},
    # --- IF: PCSrc MUX + PC + Instruction Memory ---
    "pc_src_mux":         {"x": 31,   "y": 178, "w": 64,  "h": 134},
    "pc":                 {"x": 109,  "y": 188, "w": 78,  "h": 104},
    "instruction_memory": {"x": 201,  "y": 170, "w": 120, "h": 150},
    # --- IF/ID ---
    "if_id":              {"x": 335,  "y": 158, "w": 46,  "h": 176},
    # --- ID: Register File + Immediate/Extend apilados ---
    "register_file":      {"x": 455,  "y": 162, "w": 140, "h": 126},
    "immediate":          {"x": 455,  "y": 306, "w": 140, "h": 84},
    # --- ID/EX ---
    "id_ex":              {"x": 667,  "y": 158, "w": 46,  "h": 176},
    # --- EX: ALUSrc MUX + ALU ---
    "alu_src_mux":        {"x": 727,  "y": 178, "w": 64,  "h": 134},
    "alu":                {"x": 805,  "y": 170, "w": 140, "h": 150},
    # --- EX/MEM ---
    "ex_mem":             {"x": 959,  "y": 158, "w": 46,  "h": 176},
    # --- MEM: Data Memory ---
    "data_memory":        {"x": 1019, "y": 170, "w": 140, "h": 150},
    # --- MEM/WB ---
    "mem_wb":             {"x": 1173, "y": 158, "w": 46,  "h": 176},
    # --- WB: ResultSrc MUX -> Register File ---
    "result_src_mux":     {"x": 1233, "y": 178, "w": 96,  "h": 134},
    # --- Unidad combinada de control de riesgos (fila inferior) ---
    "risk_unit":          {"x": 200,  "y": 420, "w": 720, "h": 110},  # Hazard / Forwarding
}
