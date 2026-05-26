"""Widget que dibuja la FSM del procesador multiciclo – v2.

Mejoras respecto a v1:
  • Corrige el relleno incorrecto de flechas curvas (Qt.NoBrush antes de drawPath)
  • Cuadro de anotacion junto al estado activo con senales de control y
    valores dinamicos (PC, A, B, ALUOut, MDR)
  • Anillo de brillo exterior en el estado activo
  • Texto de instruccion integrado en el cuadro de anotacion

Estados y transiciones:
  S0 FETCH     -> S1 DECODE     (siempre)
  S1 DECODE    -> S2 EXECUTE    (siempre)
  S2 EXECUTE   -> S3 MEMORY     (lw / sw)
  S2 EXECUTE   -> S4 WRITEBACK  (R-type / addi)
  S2 EXECUTE   -> S0 FETCH      (beq / bne)
  S3 MEMORY    -> S4 WRITEBACK  (lw)
  S3 MEMORY    -> S0 FETCH      (sw)
  S4 WRITEBACK -> S0 FETCH      (siempre)
"""

import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget


# ---------------------------------------------------------------------------
# Colores, etiquetas y senales de control estaticas por estado
# ---------------------------------------------------------------------------

_COLORS = {
    "FETCH":     "#78a9ff",
    "DECODE":    "#8f7cff",
    "EXECUTE":   "#ff9f7a",
    "MEMORY":    "#5fd4be",
    "WRITEBACK": "#ff7fa8",
}

_LABELS = {
    "FETCH":     ("S0", "FETCH"),
    "DECODE":    ("S1", "DECODE"),
    "EXECUTE":   ("S2", "EXECUTE"),
    "MEMORY":    ("S3", "MEMORY"),
    "WRITEBACK": ("S4", "WRITEBACK"),
}

# Senales estaticas que se muestran en el cuadro de anotacion de cada estado
_STATIC_SIGNALS = {
    "FETCH":     ["PCWrite = 1", "IRWrite = 1", "AdrSrc = PC", "ALUSrcB = 4"],
    "DECODE":    ["A  ←  reg[rs1]", "B  ←  reg[rs2]"],
    "EXECUTE":   ["ALUSrcA = A", "ALUSrcB = B / imm", "ALU opera"],
    "MEMORY":    ["AdrSrc = ALUOut", "MemRead / MemWrite"],
    "WRITEBACK": ["RegWrite = 1", "rd  ←  Result"],
}

# El cuadro de anotacion aparece a la derecha del circulo, salvo WRITEBACK
# (que esta en el extremo derecho) donde aparece a la izquierda.
_ANNOT_RIGHT = {
    "FETCH":     True,
    "DECODE":    True,
    "EXECUTE":   True,
    "MEMORY":    True,
    "WRITEBACK": False,
}


class MultiCycleFSMWidget(QWidget):
    """Diagrama FSM multiciclo con estado activo resaltado y cuadro de anotacion."""

    def __init__(self):
        super().__init__()
        self._current_state: str | None = None
        self._active_instruction: str = ""
        self._stage_data: dict = {}
        self.setMinimumSize(400, 520)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def set_current_state(self, state_name: str | None) -> None:
        """state_name: 'FETCH'|'DECODE'|'EXECUTE'|'MEMORY'|'WRITEBACK'|None"""
        self._current_state = state_name
        self.update()

    def set_active_instruction(self, text: str) -> None:
        self._active_instruction = text or ""
        self.update()

    def set_stage_data(self, data: dict) -> None:
        """Valores dinamicos del ciclo actual.

        Claves reconocidas: 'pc' (int), 'a' (int), 'b' (int),
                            'alu_out' (int), 'mdr' (int).
        """
        self._stage_data = data or {}
        self.update()

    def clear(self) -> None:
        self._current_state = None
        self._active_instruction = ""
        self._stage_data = {}
        self.update()

    # ------------------------------------------------------------------
    # Geometria
    # ------------------------------------------------------------------

    def _positions(self) -> dict[str, QPointF]:
        W, H = self.width(), self.height()
        return {
            "FETCH":     QPointF(W * 0.50, H * 0.10),
            "DECODE":    QPointF(W * 0.50, H * 0.30),
            "EXECUTE":   QPointF(W * 0.50, H * 0.52),
            "MEMORY":    QPointF(W * 0.26, H * 0.74),
            "WRITEBACK": QPointF(W * 0.74, H * 0.74),
        }

    def _radius(self) -> float:
        return min(self.width(), self.height()) * 0.095

    # ------------------------------------------------------------------
    # paintEvent
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        pos = self._positions()
        r   = self._radius()
        W   = self.width()
        arrow_col = QColor("#8899cc")

        # ---- Flechas (detras de los circulos) ----
        self._straight(painter, pos["FETCH"],   pos["DECODE"],    r, "",         arrow_col)
        self._straight(painter, pos["DECODE"],  pos["EXECUTE"],   r, "",         arrow_col)
        self._straight(painter, pos["EXECUTE"], pos["MEMORY"],    r, "lw / sw",  arrow_col, label_left=True)
        self._straight(painter, pos["EXECUTE"], pos["WRITEBACK"], r, "R / addi", arrow_col, label_left=False)
        self._straight(painter, pos["MEMORY"],  pos["WRITEBACK"], r, "lw",       arrow_col)

        self._curved(painter, pos["EXECUTE"],   pos["FETCH"], r, "beq / bne", arrow_col, cx_offset= W * 0.36)
        self._curved(painter, pos["MEMORY"],    pos["FETCH"], r, "sw",        arrow_col, cx_offset=-W * 0.30)
        self._curved(painter, pos["WRITEBACK"], pos["FETCH"], r, "siempre",   arrow_col, cx_offset= W * 0.42)

        # ---- Circulos de estado ----
        for name, center in pos.items():
            self._draw_state(painter, center, r, name)

        # ---- Cuadro de anotacion para el estado activo ----
        if self._current_state and self._current_state in pos:
            self._draw_annotation(
                painter, pos[self._current_state], r, self._current_state
            )

    # ------------------------------------------------------------------
    # Helpers de dibujo
    # ------------------------------------------------------------------

    def _draw_state(self, painter: QPainter, center: QPointF, r: float, name: str) -> None:
        color  = QColor(_COLORS[name])
        active = (name == self._current_state)
        tag, lbl = _LABELS[name]

        if active:
            # Anillo exterior de brillo
            glow_pen = QPen(color.darker(150), 5)
            painter.setPen(glow_pen)
            painter.setBrush(QBrush(color))
        else:
            painter.setPen(QPen(color.darker(115), 2))
            painter.setBrush(QBrush(color.lighter(170)))

        painter.drawEllipse(center, r, r)

        # Etiquetas interiores (dos lineas)
        text_color = QColor("white") if active else QColor("#2d3561")
        for i, text in enumerate([tag, lbl]):
            font = QFont()
            font.setPointSize(7 if i == 1 else 9)
            font.setBold(i == 0 or active)
            painter.setFont(font)
            painter.setPen(text_color)
            y_off = -6 if i == 0 else 7
            painter.drawText(
                QRectF(center.x() - r, center.y() + y_off - 7, r * 2, 14),
                Qt.AlignCenter, text,
            )

    def _draw_annotation(
        self,
        painter: QPainter,
        center: QPointF,
        r: float,
        state: str,
    ) -> None:
        """Cuadro de anotacion con senales de control y valores dinamicos."""
        color = QColor(_COLORS[state])
        W = self.width()
        right = _ANNOT_RIGHT[state]

        # --- Construir lineas de contenido ---
        lines: list[tuple[str, str]] = []  # (kind, text)

        # Instruccion activa
        if self._active_instruction:
            instr = self._active_instruction
            if len(instr) > 24:
                instr = instr[:24] + "…"
            lines.append(("instr", instr))

        # Senales estaticas
        for sig in _STATIC_SIGNALS.get(state, []):
            lines.append(("signal", sig))

        # Valores dinamicos segun etapa
        d = self._stage_data
        if state == "FETCH":
            if "pc" in d:
                lines.append(("value", f"PC  =  {d['pc']}"))
                lines.append(("value", f"→   PC+4  =  {d['pc'] + 4}"))
        elif state == "DECODE":
            if "a" in d:
                lines.append(("value", f"A  =  {d['a']}"))
            if "b" in d:
                lines.append(("value", f"B  =  {d['b']}"))
        elif state == "EXECUTE":
            if "a" in d:
                lines.append(("value", f"A  =  {d['a']}"))
            if "b" in d:
                lines.append(("value", f"B  =  {d['b']}"))
            if "alu_out" in d:
                lines.append(("value", f"ALUOut  =  {d['alu_out']}"))
        elif state == "MEMORY":
            if "alu_out" in d:
                lines.append(("value", f"Addr  =  {d['alu_out']}"))
            if "mdr" in d:
                lines.append(("value", f"MDR  =  {d['mdr']}"))
        elif state == "WRITEBACK":
            if "alu_out" in d:
                lines.append(("value", f"Result  =  {d['alu_out']}"))
            if "mdr" in d and d.get("mdr", 0) != 0:
                lines.append(("value", f"MDR  =  {d['mdr']}"))

        if not lines:
            return

        # --- Dimensiones del cuadro ---
        line_h = 17
        pad_x, pad_y = 12, 8
        box_w = 185
        box_h = len(lines) * line_h + pad_y * 2 + 2

        # Posicion horizontal
        if right:
            bx = center.x() + r + 16
        else:
            bx = center.x() - r - 16 - box_w

        by = center.y() - box_h / 2

        # Mantener dentro del widget
        bx = max(4, min(bx, W - box_w - 4))
        by = max(4, by)

        box_rect = QRectF(bx, by, box_w, box_h)

        # --- Fondo del cuadro ---
        painter.setPen(QPen(color.darker(130), 1.5))
        painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
        painter.drawRoundedRect(box_rect, 8, 8)

        # Barra de acento lateral
        if right:
            accent_rect = QRectF(bx, by + 1, 5, box_h - 2)
        else:
            accent_rect = QRectF(bx + box_w - 5, by + 1, 5, box_h - 2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(accent_rect, 3, 3)

        # Conector punteado entre circulo y cuadro
        cx_edge = center.x() + (r if right else -r)
        bx_edge = bx if right else bx + box_w
        conn_pen = QPen(color.darker(120), 1.2, Qt.DashLine)
        painter.setPen(conn_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(QPointF(cx_edge, center.y()), QPointF(bx_edge, center.y()))

        # --- Texto del cuadro ---
        text_x = bx + (13 if right else 10)
        for i, (kind, text) in enumerate(lines):
            ty = by + pad_y + i * line_h

            font = QFont()
            if kind == "instr":
                font.setPointSize(8)
                font.setBold(True)
                painter.setPen(QColor("#1a1a4e"))
            elif kind == "signal":
                font.setPointSize(7)
                font.setItalic(True)
                painter.setPen(QColor("#445599"))
            else:  # "value"
                font.setPointSize(7)
                font.setBold(True)
                painter.setPen(color.darker(160))

            painter.setFont(font)
            painter.setBrush(Qt.NoBrush)
            painter.drawText(
                QRectF(text_x, ty, box_w - 18, line_h),
                Qt.AlignVCenter | Qt.AlignLeft,
                text,
            )

    # ------------------------------------------------------------------
    # Primitivas de flecha
    # ------------------------------------------------------------------

    def _edge(self, center: QPointF, r: float, toward: QPointF) -> QPointF:
        dx = toward.x() - center.x()
        dy = toward.y() - center.y()
        dist = math.hypot(dx, dy) or 1.0
        return QPointF(center.x() + dx / dist * r, center.y() + dy / dist * r)

    def _set_arrow_pen(self, painter: QPainter, color: QColor) -> None:
        """Lapiz para lineas/curvas SIN relleno (evita el bug de triangulos)."""
        pen = QPen(color, 1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)   # <-- clave: sin relleno

    def _arrowhead(
        self,
        painter: QPainter,
        tip: QPointF,
        angle: float,
        color: QColor,
        size: float = 9,
    ) -> None:
        """Cabeza de flecha rellena; maneja su propio estado de pincel."""
        a1 = angle + math.radians(145)
        a2 = angle - math.radians(145)
        p1 = QPointF(tip.x() + size * math.cos(a1), tip.y() + size * math.sin(a1))
        p2 = QPointF(tip.x() + size * math.cos(a2), tip.y() + size * math.sin(a2))
        path = QPainterPath()
        path.moveTo(tip)
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)

    def _label(
        self,
        painter: QPainter,
        p: QPointF,
        text: str,
        dx: float = 0,
        dy: float = -11,
    ) -> None:
        if not text:
            return
        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QColor("#4a5580"))
        painter.setBrush(Qt.NoBrush)
        painter.drawText(
            QRectF(p.x() - 44 + dx, p.y() + dy - 7, 88, 14),
            Qt.AlignCenter,
            text,
        )

    def _straight(
        self,
        painter: QPainter,
        src: QPointF,
        dst: QPointF,
        r: float,
        label: str,
        color: QColor,
        label_left: bool | None = None,
    ) -> None:
        start = self._edge(src, r, dst)
        end   = self._edge(dst, r, src)

        self._set_arrow_pen(painter, color)
        painter.drawLine(start, end)

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)
        self._arrowhead(painter, end, angle, color)
        self._set_arrow_pen(painter, color)   # restaurar tras arrowhead

        mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
        dist = math.hypot(dx, dy) or 1.0
        perp_x = -dy / dist * 14
        perp_y =  dx / dist * 14
        if label_left is False:
            perp_x, perp_y = -perp_x, -perp_y
        self._label(painter, mid, label, perp_x, perp_y - 11)

    def _curved(
        self,
        painter: QPainter,
        src: QPointF,
        dst: QPointF,
        r: float,
        label: str,
        color: QColor,
        cx_offset: float = 100,
    ) -> None:
        mx   = (src.x() + dst.x()) / 2 + cx_offset
        my   = (src.y() + dst.y()) / 2
        ctrl = QPointF(mx, my)

        start = self._edge(src, r, ctrl)
        end   = self._edge(dst, r, ctrl)

        self._set_arrow_pen(painter, color)   # NoBrush activo aqui

        path = QPainterPath()
        path.moveTo(start)
        path.quadTo(ctrl, end)
        painter.drawPath(path)                # no se rellena gracias a NoBrush

        # Tangente al final de la curva de Bezier cuadratica
        tdx = end.x() - ctrl.x()
        tdy = end.y() - ctrl.y()
        self._arrowhead(painter, end, math.atan2(tdy, tdx), color)
        self._set_arrow_pen(painter, color)   # restaurar tras arrowhead

        # Etiqueta en t=0.5 de la curva
        lx = 0.25 * start.x() + 0.5 * ctrl.x() + 0.25 * end.x()
        ly = 0.25 * start.y() + 0.5 * ctrl.y() + 0.25 * end.y()
        self._label(painter, QPointF(lx, ly), label)
