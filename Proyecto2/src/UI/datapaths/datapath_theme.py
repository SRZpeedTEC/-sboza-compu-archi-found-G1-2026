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
