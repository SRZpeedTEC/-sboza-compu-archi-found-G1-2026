from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from src.UI.datapaths.datapath_theme import (
    DatapathTheme,
    SINGLE_CYCLE_ABSTRACT_LAYOUT,
    SINGLE_CYCLE_CONTENT_HEIGHT,
    SINGLE_CYCLE_CONTENT_WIDTH,
    color_with_alpha,
)
from src.UI.datapaths.single_cycle_state_mapper import (
    MODULE_ORDER,
    map_single_cycle_datapath_state,
)


class SingleCycleDatapathView(QWidget):
    def __init__(self, accent: str, parent=None):
        super().__init__(parent)

        self.accent = accent
        self.theme = DatapathTheme()
        self.state = map_single_cycle_datapath_state(None)

        self.setMinimumHeight(320)
        self.setStyleSheet("""
            background: transparent;
            border: none;
        """)

    def set_snapshot(self, snapshot) -> None:
        self.state = map_single_cycle_datapath_state(snapshot)
        self.update()

    def clear(self) -> None:
        self.state = map_single_cycle_datapath_state(None)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        scale = min(
            self.width() / SINGLE_CYCLE_CONTENT_WIDTH,
            self.height() / SINGLE_CYCLE_CONTENT_HEIGHT,
        )
        scale = max(0.55, min(scale, 1.0))

        scaled_width = SINGLE_CYCLE_CONTENT_WIDTH * scale
        scaled_height = SINGLE_CYCLE_CONTENT_HEIGHT * scale
        offset_x = (self.width() - scaled_width) / 2
        offset_y = (self.height() - scaled_height) / 2

        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)

        modules = self.state.get("modules", {})
        active_modules = self.state.get("active_modules", set())

        self._draw_paths(painter, active_modules)

        for key in MODULE_ORDER:
            rect_data = SINGLE_CYCLE_ABSTRACT_LAYOUT[key]
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
            ("pc_src_mux", "pc", [(112, 209), (138, 209)]),
            ("pc", "instruction_memory", [(234, 209), (260, 209)]),
            ("instruction_memory", "register_file", [(410, 209), (444, 209)]),
            ("register_file", "alu_src_mux", [(604, 209), (650, 209)]),
            ("alu_src_mux", "alu", [(750, 209), (790, 209)]),
            ("alu", "data_memory", [(940, 209), (980, 209)]),
            ("data_memory", "result_src_mux", [(1130, 209), (1170, 209)]),
            ("immediate", "alu_src_mux", [(717, 282), (717, 270)]),
            ("control_unit", "register_file", [(525, 130), (525, 146)]),
            ("control_unit", "alu_src_mux", [(595, 76), (700, 76), (700, 148)]),
            ("control_unit", "alu", [(595, 54), (865, 54), (865, 146)]),
            ("control_unit", "data_memory", [(595, 34), (1055, 34), (1055, 146)]),
            ("control_unit", "result_src_mux", [(595, 20), (1222, 20), (1222, 148)]),
            ("control_unit", "pc_src_mux", [(345, 64), (64, 64), (64, 148)]),
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
                painter.drawLine(
                    QPointF(*points[index]),
                    QPointF(*points[index + 1]),
                )

        painter.setPen(QPen(color, width))
        for index in range(len(points) - 1):
            painter.drawLine(
                QPointF(*points[index]),
                QPointF(*points[index + 1]),
            )

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
            fill = QColor(self.theme.active_fill)
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

        title_left_margin = 16 if key == "alu" else 8
        title_right_margin = 16 if key == "alu" else 8
        title_height = 34 if key in {"instruction_memory", "data_memory"} else 24
        title_y = rect.top() + (14 if key in {"pc_src_mux", "alu_src_mux", "result_src_mux"} else 6)
        title_rect = QRectF(
            rect.left() + title_left_margin,
            title_y,
            rect.width() - title_left_margin - title_right_margin,
            title_height,
        )
        painter.setPen(title_text)
        title_size = 9 if key in {"pc_src_mux", "alu_src_mux", "result_src_mux"} else 10
        painter.setFont(QFont("Segoe UI", title_size, QFont.Bold))
        display_title = title.replace(" MUX", "\nMUX")
        if key in {"instruction_memory", "data_memory"}:
            display_title = title.replace(" ", "\n")
        painter.drawText(
            title_rect,
            Qt.AlignCenter,
            display_title,
        )

        if key == "control_unit":
            self._draw_control_lines(painter, rect, lines, text)
            return

        line_count = max(len(lines), 1)
        font_size = 9
        if line_count >= 8:
            font_size = 8
        elif key in {"pc_src_mux", "alu_src_mux", "result_src_mux"}:
            font_size = 8

        painter.setPen(text)
        painter.setFont(QFont("Segoe UI", font_size))

        if key in {"pc_src_mux", "alu_src_mux", "result_src_mux"}:
            line_top = rect.top() + 52
            available_height = rect.height() - 64
        else:
            line_top = rect.top() + (46 if key in {"instruction_memory", "data_memory"} else 36)
            available_height = rect.height() - (54 if key in {"instruction_memory", "data_memory"} else 44)
        line_height = min(15, available_height / line_count)

        left_margin = 28 if key == "alu" else 8
        right_margin = 22 if key == "alu" else 8

        for index, line in enumerate(lines):
            line_rect = QRectF(
                rect.left() + left_margin,
                line_top + index * line_height,
                rect.width() - left_margin - right_margin,
                line_height + 2,
            )
            self._draw_info_line(painter, line_rect, line, key)

    def _draw_control_lines(
        self,
        painter: QPainter,
        rect: QRectF,
        lines: list[str],
        text: QColor,
    ) -> None:
        painter.setPen(text)
        painter.setFont(QFont("Segoe UI", 8))

        midpoint = (len(lines) + 1) // 2
        columns = [lines[:midpoint], lines[midpoint:]]
        column_width = (rect.width() - 24) / 2
        line_height = 14

        for column_index, column_lines in enumerate(columns):
            x = rect.left() + 10 + column_index * (column_width + 4)
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
            painter.drawText(
                rect,
                Qt.AlignCenter,
                self._fit_text(painter, line, rect.width()),
            )
            return

        label, value = line.split(": ", 1)

        if key == "instruction_memory":
            compact = f"{label}: {value}"
            painter.drawText(
                rect,
                Qt.AlignCenter,
                self._fit_text(painter, compact, rect.width()),
            )
            return

        if key in {"pc_src_mux", "alu_src_mux", "result_src_mux"}:
            compact = self._compact_mux_line(label, value)
            painter.drawText(
                rect,
                Qt.AlignCenter,
                self._fit_text(painter, compact, rect.width()),
            )
            return

        if key == "control_unit":
            compact = f"{label}: {value}"
            painter.drawText(
                rect,
                Qt.AlignCenter,
                self._fit_text(painter, compact, rect.width()),
            )
            return

        label_width = rect.width() * 0.48
        value_width = rect.width() * 0.48
        gap = rect.width() * 0.04

        label_rect = QRectF(
            rect.left(),
            rect.top(),
            label_width,
            rect.height(),
        )
        value_rect = QRectF(
            rect.left() + label_width + gap,
            rect.top(),
            value_width,
            rect.height(),
        )

        painter.drawText(
            label_rect,
            Qt.AlignRight | Qt.AlignVCenter,
            self._fit_text(painter, f"{label}:", label_rect.width()),
        )
        painter.drawText(
            value_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            self._fit_text(painter, value, value_rect.width()),
        )

    def _compact_mux_line(self, label: str, value: str) -> str:
        label_map = {
            "PCSrc": "PCSrc",
            "ALUSrc": "ALUSrc",
            "ResultSrc": "ResultSrc",
            "selected": "sel",
        }
        value_map = {
            "branch_target": "branch",
            "pc_plus_4": "PC+4",
            "memory": "mem",
        }
        return f"{label_map.get(label, label)}: {value_map.get(value, value)}"

    def _draw_shape(self, painter: QPainter, rect: QRectF, key: str) -> None:
        if key == "alu":
            polygon = QPolygonF([
                QPointF(rect.left() + 26, rect.top()),
                QPointF(rect.right() - 16, rect.top()),
                QPointF(rect.right(), rect.center().y()),
                QPointF(rect.right() - 16, rect.bottom()),
                QPointF(rect.left() + 26, rect.bottom()),
                QPointF(rect.left(), rect.center().y()),
            ])
            painter.drawPolygon(polygon)
            return

        if key in {"pc_src_mux", "alu_src_mux", "result_src_mux"}:
            polygon = QPolygonF([
                QPointF(rect.left(), rect.top()),
                QPointF(rect.right(), rect.top() + 20),
                QPointF(rect.right(), rect.bottom() - 20),
                QPointF(rect.left(), rect.bottom()),
            ])
            painter.drawPolygon(polygon)
            return

        if key in {"instruction_memory", "data_memory"}:
            painter.drawRect(rect)
            return

        radius = 26 if key in {"pc", "control_unit"} else 18
        painter.drawRoundedRect(rect, radius, radius)

    def _fit_text(self, painter: QPainter, text: str, max_width: float) -> str:
        metrics = painter.fontMetrics()
        if metrics.horizontalAdvance(text) <= max_width:
            return text

        return metrics.elidedText(text, Qt.ElideRight, int(max_width))
