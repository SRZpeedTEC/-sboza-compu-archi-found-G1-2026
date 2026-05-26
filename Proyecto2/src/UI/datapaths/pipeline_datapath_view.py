from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from src.UI.datapaths.datapath_theme import (
    DatapathTheme,
    PIPELINE_ABSTRACT_LAYOUT,
    PIPELINE_CONTENT_HEIGHT,
    PIPELINE_CONTENT_WIDTH,
    color_with_alpha,
)
from src.UI.datapaths.pipeline_state_mapper import (
    MODULE_ORDER,
    PIPE_REGISTER_ORDER,
    STAGE_ORDER,
    STAGE_TITLES,
    UNIT_ORDER,
    map_pipeline_datapath_state,
)

NO_FORWARD = "ID/EX"


class PipelineDatapathView(QWidget):
    """Datapath del Pipeline (Forwarding / Stalls), espejo del Uniciclo.

    Pinta cinco etapas, cuatro barreras de registro con contenido, las dos
    unidades de control de riesgos, la instruccion en vuelo por etapa y los
    riesgos (forwarding / stall / flush). Solo consume ``self.state``.
    """

    def __init__(self, accent: str, parent=None, min_scale: float = 0.45, min_height: int = 400):
        super().__init__(parent)

        self.accent = accent
        self.min_scale = min_scale
        self.theme = DatapathTheme()
        self.state = map_pipeline_datapath_state(None)

        self.setMinimumHeight(min_height)
        self.setStyleSheet("""
            background: transparent;
            border: none;
        """)

    def set_snapshot(self, snapshot) -> None:
        self.state = map_pipeline_datapath_state(snapshot)
        self.update()

    def clear(self) -> None:
        self.state = map_pipeline_datapath_state(None)
        self.update()

    # ----------------------------------------------------------------- paint
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        scale = min(
            self.width() / PIPELINE_CONTENT_WIDTH,
            self.height() / PIPELINE_CONTENT_HEIGHT,
        )
        scale = max(self.min_scale, min(scale, 1.0))

        scaled_width = PIPELINE_CONTENT_WIDTH * scale
        scaled_height = PIPELINE_CONTENT_HEIGHT * scale
        offset_x = (self.width() - scaled_width) / 2
        offset_y = (self.height() - scaled_height) / 2

        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)

        active_modules = self.state.get("active_modules", set())

        self._draw_main_paths(painter, active_modules)
        self._draw_unit_paths(painter)
        self._draw_pipe_registers(painter)
        self._draw_datapath_modules(painter)
        self._draw_units(painter)
        self._draw_stage_instructions(painter)
        self._draw_forwarding(painter)
        self._draw_overlays(painter)

    # -------------------------------------------------------------- geometry
    def _rect(self, key: str) -> QRectF:
        data = PIPELINE_ABSTRACT_LAYOUT[key]
        return QRectF(data["x"], data["y"], data["w"], data["h"])

    def _lit(self, key: str) -> bool:
        """Un elemento esta encendido si su etapa esta activa o su barrera presente."""
        if key in MODULE_ORDER:
            return key in self.state.get("active_modules", set())
        if key in PIPE_REGISTER_ORDER:
            return bool(self.state.get("pipe_registers", {}).get(key, {}).get("present"))
        if key in UNIT_ORDER:
            return bool(self.state.get("units", {}).get(key, {}).get("active"))
        return False

    # ----------------------------------------------------------------- paths
    def _draw_main_paths(self, painter: QPainter, active_modules: set[str]) -> None:
        # Flujo de datos por componentes, con tramos cortos como Uniciclo/Multiciclo.
        paths = [
            ("pc_src_mux", "pc", [(95, 245), (109, 245)]),
            ("pc", "instruction_memory", [(187, 245), (201, 245)]),
            ("instruction_memory", "if_id", [(321, 245), (335, 245)]),
            ("if_id", "register_file", [(381, 225), (455, 225)]),
            # rs1/rs2 leidos del banco de registros -> ID/EX (bus principal).
            ("register_file", "id_ex", [(595, 225), (667, 225)]),
            # La instruccion de IF/ID alimenta el sign-extend (en paralelo al
            # banco de registros), y el inmediato se latchea en ID/EX.
            ("if_id", "immediate", [(372, 334), (372, 348), (455, 348)]),
            ("immediate", "id_ex", [(595, 320), (667, 320)]),
            ("id_ex", "alu_src_mux", [(713, 245), (727, 245)]),
            ("alu_src_mux", "alu", [(791, 245), (805, 245)]),
            ("alu", "ex_mem", [(945, 245), (959, 245)]),
            ("ex_mem", "data_memory", [(1005, 245), (1019, 245)]),
            ("data_memory", "mem_wb", [(1159, 245), (1173, 245)]),
            ("mem_wb", "result_src_mux", [(1219, 245), (1233, 245)]),
            # Writeback: ResultSrc MUX -> Register File, baja por debajo del
            # bloque ID y entra al banco por la izquierda.
            ("result_src_mux", "register_file", [(1281, 301), (1281, 405), (418, 405), (418, 262), (455, 262)]),
            # Senales de control: salen de la Unidad de Control, viajan por la banda
            # libre (y 108-132, sobre las pills) y bajan por huecos sin pill; las que
            # caen sobre un modulo con pill entran por el costado a media altura.
            ("control_unit", "pc_src_mux", [(395, 56), (63, 56), (63, 189)]),
            ("control_unit", "register_file", [(448, 108), (448, 204), (455, 204)]),
            ("control_unit", "alu_src_mux", [(759, 108), (759, 189)]),
            ("control_unit", "alu", [(798, 108), (798, 200), (820, 200)]),
            ("control_unit", "data_memory", [(861, 64), (1012, 64), (1012, 200), (1019, 200)]),
            ("control_unit", "result_src_mux", [(861, 48), (1226, 48), (1226, 200), (1233, 200)]),
        ]
        for source, target, points in paths:
            source_active = self._lit(source) or source in active_modules
            target_active = self._lit(target) or target in active_modules
            self._draw_path(painter, points, source_active and target_active)

    def _draw_unit_paths(self, painter: QPainter) -> None:
        units = self.state.get("units", {})
        risk_active = bool(units.get("risk_unit", {}).get("active"))
        forwarding_active = (
            self.state.get("forward_a", NO_FORWARD) != NO_FORWARD
            or self.state.get("forward_b", NO_FORWARD) != NO_FORWARD
        )
        hazard_active = bool(self.state.get("stalled")) or bool(self.state.get("flushed"))

        # Risk Control Unit -> ID/EX (bubble/control gating).
        self._draw_path(
            painter,
            [(690, 420), (690, 334)],
            risk_active,
        )
        # Risk Control Unit -> ALUSrc MUX (seleccion de operandos).
        self._draw_path(
            painter,
            [(759, 420), (759, 301)],
            forwarding_active,
        )
        # Risk Control Unit -> PC (PCWrite) y -> IF/ID (IF_IDWrite).
        self._draw_path(
            painter,
            [(300, 420), (300, 360), (148, 360), (148, 292)],
            hazard_active,
        )
        self._draw_path(
            painter,
            [(358, 420), (358, 334)],
            hazard_active,
        )

    def _draw_path(self, painter: QPainter, points, active: bool) -> None:
        color = QColor(self.accent if active else self.theme.path)
        width = 3 if active else 2

        if active:
            painter.setPen(QPen(color_with_alpha(self.accent, 36), 7))
            for index in range(len(points) - 1):
                painter.drawLine(QPointF(*points[index]), QPointF(*points[index + 1]))

        painter.setPen(QPen(color, width))
        for index in range(len(points) - 1):
            painter.drawLine(QPointF(*points[index]), QPointF(*points[index + 1]))

    # --------------------------------------------------------- pipe registers
    def _draw_pipe_registers(self, painter: QPainter) -> None:
        registers = self.state.get("pipe_registers", {})
        for key in PIPE_REGISTER_ORDER:
            data = registers.get(key, {"title": key, "lines": [], "present": False})
            self._draw_pipe_register(
                painter,
                self._rect(key),
                data["title"],
                data["lines"],
                data.get("present", False),
            )

    def _draw_pipe_register(self, painter, rect, title, lines, present) -> None:
        if present:
            fill = QColor(self.theme.pipe_register_fill)
            border = QColor(self.accent)
            title_color = QColor(self.accent)
            text_color = QColor(self.theme.pipe_register_text)
            border_width = 2.5
        else:
            fill = QColor(self.theme.inactive_fill)
            border = QColor(self.theme.inactive_border)
            title_color = QColor(self.theme.muted_text)
            text_color = QColor(self.theme.muted_text)
            border_width = 2.0

        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, border_width))
        painter.drawRoundedRect(rect, 8, 8)

        painter.setPen(title_color)
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(
            QRectF(rect.left() + 2, rect.top() + 4, rect.width() - 4, 16),
            Qt.AlignCenter,
            title,
        )

        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 7))
        line_top = rect.top() + 24
        line_height = min(16, (rect.height() - 30) / max(len(lines), 1))
        for index, line in enumerate(lines):
            line_rect = QRectF(
                rect.left() + 4,
                line_top + index * line_height,
                rect.width() - 8,
                line_height + 1,
            )
            painter.drawText(
                line_rect,
                Qt.AlignCenter,
                self._fit_text(painter, line, line_rect.width()),
            )

    # ------------------------------------------------------------- modules
    def _draw_datapath_modules(self, painter: QPainter) -> None:
        modules = self.state.get("modules", {})
        active_modules = self.state.get("active_modules", set())
        for key in MODULE_ORDER:
            module = modules.get(key, {"title": key, "lines": []})
            self._draw_module(
                painter,
                self._rect(key),
                module["title"],
                module["lines"],
                key in active_modules,
                key,
            )

    def _draw_units(self, painter: QPainter) -> None:
        units = self.state.get("units", {})
        for key in UNIT_ORDER:
            unit = units.get(key, {"title": key, "lines": [], "active": False})
            self._draw_module(
                painter,
                self._rect(key),
                unit["title"],
                unit["lines"],
                bool(unit.get("active")),
                key,
            )

    def _draw_module(self, painter, rect, title, lines, active, key) -> None:
        is_unit = key in UNIT_ORDER
        is_mux = self._is_mux(key)

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

        # Titulo.
        painter.setPen(title_text)
        if is_unit:
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            title_rect = QRectF(rect.left() + 6, rect.top() + 8, rect.width() - 12, 32)
            painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, title)
        else:
            title_size = 8 if is_mux else 9
            painter.setFont(QFont("Segoe UI", title_size, QFont.Bold))
            title_height = 38 if is_mux or key in {"instruction_memory", "data_memory"} else 24
            painter.drawText(
                QRectF(rect.left() + 8, rect.top() + 8, rect.width() - 16, title_height),
                Qt.AlignCenter,
                self._display_title(title, key),
            )

        # La Unidad de Control reparte sus senales en dos columnas (mas legible).
        if key == "control_unit":
            self._draw_control_lines(painter, rect, lines, text)
            return

        # Lineas label: value.
        painter.setPen(text)
        font_size = 8 if len(lines) >= 5 or is_mux or is_unit else 9
        painter.setFont(QFont("Segoe UI", font_size))

        if is_mux:
            line_top = rect.top() + 58
            available_height = rect.height() - 74
        elif is_unit:
            line_top = rect.top() + 44
            available_height = rect.height() - 52
        elif key in {"instruction_memory", "data_memory"}:
            line_top = rect.top() + 56
            available_height = rect.height() - 66
        else:
            line_top = rect.top() + 38
            available_height = rect.height() - 48
        line_height = min(15, available_height / max(len(lines), 1))

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

    def _draw_control_lines(self, painter, rect, lines, text) -> None:
        painter.setPen(text)
        painter.setFont(QFont("Segoe UI", 8))

        midpoint = (len(lines) + 1) // 2
        columns = [lines[:midpoint], lines[midpoint:]]
        column_width = (rect.width() - 28) / 2
        line_height = 16

        for column_index, column_lines in enumerate(columns):
            x = rect.left() + 12 + column_index * (column_width + 4)
            for row_index, line in enumerate(column_lines):
                line_rect = QRectF(
                    x,
                    rect.top() + 34 + row_index * line_height,
                    column_width,
                    line_height + 1,
                )
                self._draw_info_line(painter, line_rect, line, "control_unit")

    def _draw_info_line(self, painter, rect, line, key) -> None:
        if ": " not in line:
            painter.drawText(rect, Qt.AlignCenter, self._fit_text(painter, line, rect.width()))
            return

        label, value = line.split(": ", 1)

        if self._is_mux(key) or key in UNIT_ORDER or key == "control_unit":
            compact = self._compact_line(label, value)
            painter.drawText(rect, Qt.AlignCenter, self._fit_text(painter, compact, rect.width()))
            return

        label_width = rect.width() * 0.5
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

    def _draw_shape(self, painter, rect, key) -> None:
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

        if self._is_mux(key):
            polygon = QPolygonF([
                QPointF(rect.left(), rect.top()),
                QPointF(rect.right(), rect.top() + 22),
                QPointF(rect.right(), rect.bottom() - 22),
                QPointF(rect.left(), rect.bottom()),
            ])
            painter.drawPolygon(polygon)
            return

        if key in {"instruction_memory", "data_memory"}:
            painter.drawRect(rect)
            return

        radius = 26 if key in {"pc", "control_unit"} else 16
        painter.drawRoundedRect(rect, radius, radius)

    # ------------------------------------------------- in-flight instructions
    def _draw_stage_instructions(self, painter: QPainter) -> None:
        instructions = self.state.get("stage_instructions", {})
        stage_rects = {
            "if": self._rect("instruction_memory"),
            "id": self._rect("register_file"),
            "ex": self._rect("alu"),
            "mem": self._rect("data_memory"),
            "wb": self._rect("result_src_mux"),
        }
        for key in STAGE_ORDER:
            rect = stage_rects[key]
            text = instructions.get(STAGE_TITLES[key], "-")
            pill = QRectF(rect.left(), rect.top() - 38, rect.width(), 26)

            if text == "STALL":
                fill = QColor(self.theme.stall_fill)
                border = QColor(self.theme.stall_fill).darker(135)
                text_color = QColor("#b23b3b")
            elif text == "-":
                fill = QColor(self.theme.inactive_fill)
                border = QColor(self.theme.inactive_border)
                text_color = QColor(self.theme.muted_text)
            else:
                fill = QColor("#ffffff")
                border = QColor(self.accent)
                text_color = QColor(self.theme.title_text)

            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(border, 1.5))
            painter.drawRoundedRect(pill, 9, 9)

            painter.setPen(text_color)
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(
                pill.adjusted(6, 0, -6, 0),
                Qt.AlignCenter,
                self._fit_text(painter, text, pill.width() - 12),
            )

    # ---------------------------------------------------------- forwarding
    def _draw_forwarding(self, painter: QPainter) -> None:
        forward_a = self.state.get("forward_a", NO_FORWARD)
        forward_b = self.state.get("forward_b", NO_FORWARD)

        # x del centro de cada barrera fuente.
        ex_mem_x = self._rect("ex_mem").center().x()
        mem_wb_x = self._rect("mem_wb").center().x()

        if forward_a in ("EX/MEM", "MEM/WB"):
            source_x = (ex_mem_x if forward_a == "EX/MEM" else mem_wb_x) - 10
            # Tap por debajo de la barrera fuente -> ALUSrc MUX.
            points = [(source_x, 334), (source_x, 370), (747, 370), (747, 306)]
            self._draw_forward_arrow(painter, points, "fwd A")

        if forward_b in ("EX/MEM", "MEM/WB"):
            source_x = (ex_mem_x if forward_b == "EX/MEM" else mem_wb_x) + 10
            points = [(source_x, 334), (source_x, 386), (771, 386), (771, 297)]
            self._draw_forward_arrow(painter, points, "fwd B")

    def _draw_forward_arrow(self, painter, points, label) -> None:
        color = QColor(self.theme.forward_path)

        painter.setPen(QPen(color_with_alpha(self.theme.forward_path, 50), 7))
        for index in range(len(points) - 1):
            painter.drawLine(QPointF(*points[index]), QPointF(*points[index + 1]))

        painter.setPen(QPen(color, 3))
        for index in range(len(points) - 1):
            painter.drawLine(QPointF(*points[index]), QPointF(*points[index + 1]))

        self._draw_arrow_head(painter, points[-2], points[-1], color)

        # Etiqueta sobre el tramo horizontal superior.
        x1, _ = points[1]
        x2, run_y = points[2]
        painter.setPen(color)
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.drawText(
            QRectF((x1 + x2) / 2 - 26, run_y - 15, 52, 12),
            Qt.AlignCenter,
            label,
        )

    def _draw_arrow_head(self, painter, prev_point, end_point, color) -> None:
        x1, y1 = prev_point
        x2, y2 = end_point
        size = 6

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 1))

        if y2 > y1:      # hacia abajo
            head = QPolygonF([
                QPointF(x2, y2),
                QPointF(x2 - size, y2 - size - 1),
                QPointF(x2 + size, y2 - size - 1),
            ])
        elif y2 < y1:    # hacia arriba
            head = QPolygonF([
                QPointF(x2, y2),
                QPointF(x2 - size, y2 + size + 1),
                QPointF(x2 + size, y2 + size + 1),
            ])
        elif x2 > x1:    # hacia la derecha
            head = QPolygonF([
                QPointF(x2, y2),
                QPointF(x2 - size - 1, y2 - size),
                QPointF(x2 - size - 1, y2 + size),
            ])
        else:            # hacia la izquierda
            head = QPolygonF([
                QPointF(x2, y2),
                QPointF(x2 + size + 1, y2 - size),
                QPointF(x2 + size + 1, y2 + size),
            ])
        painter.drawPolygon(head)

    # -------------------------------------------------------- stall / flush
    def _draw_overlays(self, painter: QPainter) -> None:
        if self.state.get("flushed"):
            self._draw_flush(painter)
        if self.state.get("stalled"):
            self._draw_stall(painter)

    def _draw_flush(self, painter: QPainter) -> None:
        fill = color_with_alpha(self.theme.flush_fill, 165)
        border = QColor(self.theme.flush_fill).darker(150)
        for key in ("if_id", "id_ex"):
            rect = self._rect(key)
            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(border, 2))
            painter.drawRoundedRect(rect, 8, 8)

            painter.setPen(QColor("#9a6b14"))
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            painter.drawText(
                QRectF(rect.left(), rect.bottom() - 16, rect.width(), 14),
                Qt.AlignCenter,
                "flush",
            )

    def _draw_stall(self, painter: QPainter) -> None:
        rect = self._rect("id_ex")
        badge = QRectF(rect.center().x() - 44, rect.top() - 30, 88, 22)

        painter.setBrush(QBrush(QColor(self.theme.stall_fill)))
        painter.setPen(QPen(QColor(self.theme.stall_fill).darker(140), 1.5))
        painter.drawRoundedRect(badge, 10, 10)

        painter.setPen(QColor("#b23b3b"))
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.drawText(badge, Qt.AlignCenter, "bubble")

    # ------------------------------------------------------------- helpers
    def _fit_text(self, painter, text, max_width) -> str:
        metrics = painter.fontMetrics()
        if metrics.horizontalAdvance(text) <= max_width:
            return text
        return metrics.elidedText(text, Qt.ElideRight, int(max_width))

    def _display_title(self, title: str, key: str) -> str:
        if self._is_mux(key):
            return title.replace(" MUX", "\nMUX")
        if key in {"instruction_memory", "data_memory"}:
            return title.replace(" ", "\n")
        return title

    def _compact_line(self, label: str, value: str) -> str:
        label_map = {
            "PCSrc": "PCSrc",
            "ALUSrc": "ALUSrc",
            "ResultSrc": "ResultSrc",
            "ForwardA": "FwdA",
            "ForwardB": "FwdB",
        }
        return f"{label_map.get(label, label)}: {self._compact_value(value)}"

    def _compact_value(self, value: str) -> str:
        value_map = {
            "branch_target": "branch",
            "pc_plus_4": "PC+4",
            "memory": "mem",
        }
        return value_map.get(value, value)

    def _is_mux(self, key: str) -> bool:
        return key in {"pc_src_mux", "alu_src_mux", "result_src_mux"}

    def _active_fill(self) -> str:
        if QColor(self.accent).hue() in range(150, 190):
            return "#e5fbf7"
        return self.theme.active_fill
