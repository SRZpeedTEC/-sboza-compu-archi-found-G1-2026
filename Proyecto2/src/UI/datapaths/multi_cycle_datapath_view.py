from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from src.UI.datapaths.datapath_theme import DatapathTheme, color_with_alpha
from src.UI.datapaths.multi_cycle_layout import (
    MULTI_CYCLE_CONTENT_HEIGHT,
    MULTI_CYCLE_CONTENT_WIDTH,
    MULTI_CYCLE_LAYOUT,
)
from src.UI.datapaths.multi_cycle_state_mapper import (
    MODULE_ORDER,
    map_multi_cycle_datapath_state,
)


class MultiCycleDatapathView(QWidget):
    def __init__(self, accent: str, parent=None, min_scale: float = 0.5, min_height: int = 470):
        super().__init__(parent)

        self.accent = accent
        self.min_scale = min_scale
        self.theme = DatapathTheme()
        self.state = map_multi_cycle_datapath_state(None)

        self.setMinimumHeight(min_height)
        self.setStyleSheet("""
            background: transparent;
            border: none;
        """)

    def set_snapshot(self, snapshot) -> None:
        self.state = map_multi_cycle_datapath_state(snapshot)
        self.update()

    def clear(self) -> None:
        self.state = map_multi_cycle_datapath_state(None)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        scale = min(
            self.width() / MULTI_CYCLE_CONTENT_WIDTH,
            self.height() / MULTI_CYCLE_CONTENT_HEIGHT,
        )
        scale = max(self.min_scale, min(scale, 1.0))

        scaled_width = MULTI_CYCLE_CONTENT_WIDTH * scale
        scaled_height = MULTI_CYCLE_CONTENT_HEIGHT * scale
        offset_x = (self.width() - scaled_width) / 2
        offset_y = (self.height() - scaled_height) / 2

        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)

        active_modules = self.state.get("active_modules", set())
        modules = self.state.get("modules", {})

        self._draw_paths(painter, active_modules)

        for key in MODULE_ORDER:
            rect_data = MULTI_CYCLE_LAYOUT[key]
            rect = QRectF(
                rect_data["x"],
                rect_data["y"],
                rect_data["w"],
                rect_data["h"],
            )
            module = modules.get(key, {"title": key, "lines": []})
            self._draw_module(
                painter,
                rect,
                module["title"],
                module["lines"],
                key in active_modules,
                key,
            )

    def _draw_paths(self, painter: QPainter, active_modules: set[str]) -> None:
        paths = [
            ("pc", "adr_src_mux", [(130, 270), (174, 270)]),
            ("adr_src_mux", "memory", [(278, 270), (330, 270)]),
            ("memory", "ir", [(500, 270), (575, 270)]),
            ("ir", "register_file", [(687, 270), (740, 270)]),
            ("register_file", "ab_register", [(912, 270), (958, 270)]),
            ("ab_register", "alu_src_a_mux", [(1076, 201), (1118, 201)]),
            ("ab_register", "alu_src_b_mux", [(1076, 329), (1118, 329)]),
            ("alu_src_a_mux", "alu", [(1230, 201), (1260, 201), (1260, 246), (1285, 246)]),
            ("alu_src_b_mux", "alu", [(1230, 329), (1260, 329), (1260, 301), (1285, 301)]),
            ("alu", "alu_out", [(1450, 273), (1512, 273)]),
            ("alu_out", "result_src_mux", [(1624, 282), (1682, 282)]),
            ("memory", "mdr", [(420, 342), (420, 396)]),
            ("ir", "immediate", [(631, 405), (631, 430), (760, 430)]),
            ("immediate", "alu_src_b_mux", [(898, 421), (1174, 421), (1174, 380)]),
            ("pc", "control_unit", [(74, 218), (74, 84), (235, 84)]),
            ("control_unit", "adr_src_mux", [(300, 138), (226, 138), (226, 204)]),
            ("memory", "control_unit", [(415, 174), (415, 138)]),
            ("control_unit", "ir", [(565, 58), (631, 58), (631, 110)]),
            ("control_unit", "register_file", [(565, 98), (826, 98), (826, 174)]),
            ("control_unit", "alu_src_a_mux", [(565, 44), (1174, 44), (1174, 150)]),
            ("control_unit", "alu_src_b_mux", [(565, 30), (1174, 30), (1174, 278)]),
            ("control_unit", "result_src_mux", [(565, 76), (1738, 76), (1738, 216)]),
        ]

        for source, target, points in paths:
            active = source in active_modules and target in active_modules
            self._draw_path(painter, points, active)

    def _draw_path(
        self,
        painter: QPainter,
        points: list[tuple[int, int]],
        active: bool,
    ) -> None:
        color = QColor(self.accent if active else self.theme.path)
        width = 3 if active else 2

        if active:
            painter.setPen(QPen(color_with_alpha(self.accent, 36), 7))
            for index in range(len(points) - 1):
                painter.drawLine(QPointF(*points[index]), QPointF(*points[index + 1]))

        painter.setPen(QPen(color, width))
        for index in range(len(points) - 1):
            painter.drawLine(QPointF(*points[index]), QPointF(*points[index + 1]))

    def _draw_module(
        self,
        painter: QPainter,
        rect: QRectF,
        title: str,
        lines: list[str],
        active: bool,
        key: str,
    ) -> None:
        if active:
            fill = QColor(self._active_fill())
            border = QColor(self.accent)
            text = QColor(self.theme.text)
            title_text = QColor(self.theme.title_text)
            border_width = 3.0
        else:
            fill = QColor(self.theme.inactive_fill)
            border = QColor(self.theme.inactive_border)
            text = QColor(self.theme.muted_text)
            title_text = QColor(self.theme.muted_text)
            border_width = 2.5

        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, border_width))
        self._draw_shape(painter, rect, key)

        title_height = 38 if key in {"memory", "adr_src_mux", "alu_src_a_mux", "alu_src_b_mux", "result_src_mux"} else 28
        title_rect = QRectF(
            rect.left() + 8,
            rect.top() + 8,
            rect.width() - 16,
            title_height,
        )
        painter.setPen(title_text)
        title_size = 8 if key in {"adr_src_mux", "alu_src_a_mux", "alu_src_b_mux", "result_src_mux"} else 9
        painter.setFont(QFont("Segoe UI", title_size, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignCenter, self._display_title(title, key))

        if key == "control_unit":
            self._draw_control_lines(painter, rect, lines, text)
            return

        painter.setPen(text)
        font_size = 8 if len(lines) >= 5 or self._is_mux(key) else 9
        painter.setFont(QFont("Segoe UI", font_size))

        if self._is_mux(key):
            line_top = rect.top() + 58
            available_height = rect.height() - 74
        elif key == "memory":
            line_top = rect.top() + 56
            available_height = rect.height() - 66
        elif key in {"ir", "alu_out"}:
            line_top = rect.top() + 78
            available_height = rect.height() - 122
        else:
            line_top = rect.top() + 38
            available_height = rect.height() - 48
        line_height = min(15, available_height / max(len(lines), 1))

        left_margin = 26 if key == "alu" else 8
        right_margin = 20 if key == "alu" else 8

        for index, line in enumerate(lines):
            line_rect = QRectF(
                rect.left() + left_margin,
                line_top + index * line_height,
                rect.width() - left_margin - right_margin,
                line_height + 2,
            )
            self._draw_info_line(painter, line_rect, line, key)

        if key in {"ir", "mdr", "ab_register", "alu_out", "pc"}:
            self._draw_clock_marker(painter, rect, border)

    def _draw_control_lines(
        self,
        painter: QPainter,
        rect: QRectF,
        lines: list[str],
        text: QColor,
    ) -> None:
        painter.setPen(text)
        painter.setFont(QFont("Segoe UI", 7))

        midpoint = (len(lines) + 1) // 2
        columns = [lines[:midpoint], lines[midpoint:]]
        column_width = (rect.width() - 26) / 2
        line_height = 12

        for column_index, column_lines in enumerate(columns):
            x = rect.left() + 10 + column_index * (column_width + 6)
            for row_index, line in enumerate(column_lines):
                line_rect = QRectF(
                    x,
                    rect.top() + 36 + row_index * line_height,
                    column_width,
                    line_height + 1,
                )
                self._draw_info_line(painter, line_rect, line, "control_unit")

    def _draw_info_line(
        self,
        painter: QPainter,
        rect: QRectF,
        line: str,
        key: str,
    ) -> None:
        if ": " not in line:
            painter.drawText(rect, Qt.AlignCenter, self._fit_text(painter, line, rect.width()))
            return

        label, value = line.split(": ", 1)

        if self._is_mux(key) or key == "control_unit":
            compact = self._compact_line(label, value)
            painter.drawText(
                rect,
                Qt.AlignCenter,
                self._fit_text(painter, compact, rect.width()),
            )
            return

        label_width = rect.width() * 0.48
        gap = rect.width() * 0.04
        value_width = rect.width() - label_width - gap
        label_rect = QRectF(rect.left(), rect.top(), label_width, rect.height())
        value_rect = QRectF(rect.left() + label_width + gap, rect.top(), value_width, rect.height())

        painter.drawText(
            label_rect,
            Qt.AlignRight | Qt.AlignVCenter,
            self._fit_text(painter, f"{label}:", label_rect.width()),
        )
        painter.drawText(
            value_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            self._fit_text(painter, self._compact_value(value), value_rect.width()),
        )

    def _draw_shape(self, painter: QPainter, rect: QRectF, key: str) -> None:
        if key == "alu":
            polygon = QPolygonF([
                QPointF(rect.left() + 28, rect.top()),
                QPointF(rect.right() - 16, rect.top()),
                QPointF(rect.right(), rect.center().y()),
                QPointF(rect.right() - 16, rect.bottom()),
                QPointF(rect.left() + 28, rect.bottom()),
                QPointF(rect.left(), rect.center().y()),
            ])
            painter.drawPolygon(polygon)
            return

        if self._is_mux(key):
            polygon = QPolygonF([
                QPointF(rect.left(), rect.top()),
                QPointF(rect.right(), rect.top() + 22),
                QPointF(rect.right(), rect.bottom() - 22),
                QPointF(rect.left(), rect.bottom()),
            ])
            painter.drawPolygon(polygon)
            return

        if key == "memory":
            painter.drawRect(rect)
            return

        radius = 26 if key in {"pc", "control_unit"} else 16
        painter.drawRoundedRect(rect, radius, radius)

    def _draw_clock_marker(self, painter: QPainter, rect: QRectF, color: QColor) -> None:
        marker = QPolygonF([
            QPointF(rect.left(), rect.bottom() - 22),
            QPointF(rect.left() + 12, rect.bottom() - 16),
            QPointF(rect.left(), rect.bottom() - 10),
        ])
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(color, 2))
        painter.drawPolygon(marker)
        painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
        painter.drawText(
            QRectF(rect.left() + 14, rect.bottom() - 24, 28, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            "CLK",
        )

    def _display_title(self, title: str, key: str) -> str:
        if self._is_mux(key):
            return title.replace(" MUX", "\nMUX")
        if key == "memory":
            return "Instruction\nMemory / Data Memory"
        if key == "mdr":
            return "Data"
        if key == "alu_out":
            return "ALUOut"
        return title

    def _compact_line(self, label: str, value: str) -> str:
        label_map = {
            "ResultSrc": "ResultSrc",
            "ALUSrcA": "SrcA",
            "ALUSrcB": "SrcB",
        }
        return f"{label_map.get(label, label)}: {self._compact_value(value)}"

    def _compact_value(self, value: str) -> str:
        value_map = {
            "pc_plus_4": "PC+4",
            "branch_target": "branch",
            "memory": "mem",
        }
        return value_map.get(value, value)

    def _is_mux(self, key: str) -> bool:
        return key in {
            "adr_src_mux",
            "alu_src_a_mux",
            "alu_src_b_mux",
            "result_src_mux",
        }

    def _fit_text(self, painter: QPainter, text: str, max_width: float) -> str:
        metrics = painter.fontMetrics()
        if metrics.horizontalAdvance(text) <= max_width:
            return text
        return metrics.elidedText(text, Qt.ElideRight, int(max_width))

    def _active_fill(self) -> str:
        if QColor(self.accent).hue() in range(150, 190):
            return "#e5fbf7"
        return self.theme.active_fill
