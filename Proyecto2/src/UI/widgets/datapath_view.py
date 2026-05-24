from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget


class DatapathWidget(QWidget):

    def __init__(self, accent, scale=1.4):
        super().__init__()

        self.accent = accent
        self.scale = scale

        self.active_blocks = set()

        self.setMaximumHeight(260)
        self.setMinimumHeight(260)

        self.setStyleSheet("""
            background: transparent;
            border: none;
        """)

    # ACTIVAR BLOQUES
    def set_active_blocks(self, blocks):

        self.active_blocks = set(blocks)

        self.update()

    # DIBUJAR
    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        content_width = 850
        content_height = 260

        scaled_width = content_width * self.scale
        scaled_height = content_height * self.scale

        offset_x = (self.width() - scaled_width) / 2
        offset_y = ((self.height() - scaled_height) / 2) + 12

        painter.translate(offset_x, offset_y)
        painter.scale(self.scale, self.scale)

        # DEFINICION DE BLOQUES
        blocks = {

            "pc":
            QRect(20, 110, 60, 40),

            "imem":
            QRect(100, 90, 85, 70),

            "control":
            QRect(220, 35, 85, 50),

            "registers":
            QRect(220, 120, 100, 65),

            "mux_alu":
            QRect(360, 126, 36, 54),

            "mux_wb":
            QRect(690, 126, 36, 54),

            "alu":
            QRect(420, 120, 85, 65),

            "dmem":
            QRect(560, 120, 85, 65),

            "wb":
            QRect(740, 120, 90, 65),
        }

        # PC -> Instruction Memory
        self.draw_path(
            painter,
            [
                (80, 130),
                (100, 130)
            ],
            "pc" in self.active_blocks
        )

        # Instruction Memory -> IF/ID
        self.draw_path(
            painter,
            [
                (185, 130),
                (195, 130)
            ],
            "imem" in self.active_blocks
        )

        # IF/ID -> Registers
        self.draw_path(
            painter,
            [
                (203, 152),
                (220, 152)
            ],
            "registers" in self.active_blocks
        )

        # Registers -> MUX
        self.draw_path(
            painter,
            [
                (320, 152),
                (360, 152)
            ],
            "registers" in self.active_blocks
        )

        # MUX -> ALU
        self.draw_path(
            painter,
            [
                (396, 152),
                (420, 152)
            ],
            "alu" in self.active_blocks
        )

        # ALU -> EX/MEM
        self.draw_path(
            painter,
            [
                (505, 152),
                (530, 152)
            ],
            "alu" in self.active_blocks
        )

        # EX/MEM -> Data Memory
        self.draw_path(
            painter,
            [
                (538, 152),
                (560, 152)
            ],
            "dmem" in self.active_blocks
        )

        # Data Memory -> MEM/WB
        self.draw_path(
            painter,
            [
                (645, 152),
                (690, 152)
            ],
            "dmem" in self.active_blocks
        )

        # MEM/WB -> WriteBack
        self.draw_path(
            painter,
            [
                (726, 152),
                (740, 152)
            ],
            "wb" in self.active_blocks
        )

        # SEÑALES DE CONTROL

        # CONTROL -> REGISTERS
        self.draw_path(
            painter,
            [
                (262, 85),
                (262, 120)
            ],
            "control" in self.active_blocks
        )

        # CONTROL -> ALU
        self.draw_path(
            painter,
            [
                (305, 60),
                (390, 60),
                (390, 120),
                (455, 120)
            ],
            "control" in self.active_blocks
        )

        # CONTROL -> MEMORY
        self.draw_path(
            painter,
            [
                (305, 50),
                (602, 50),
                (602, 120)
            ],
            "control" in self.active_blocks
        )

        # PIPELINE REGISTERS
        pipeline_regs = [

            QRect(195, 90, 8, 105),
            QRect(340, 90, 8, 105),
            QRect(530, 90, 8, 105),
            QRect(670, 90, 8, 105),
        ]

        labels = ["IF/ID", "ID/EX", "EX/MEM", "MEM/WB"]

        for i, preg in enumerate(pipeline_regs):

            painter.setBrush(QColor("#aab4d6"))
            painter.setPen(Qt.NoPen)

            painter.drawRoundedRect(preg, 6, 6)

            painter.setPen(QColor("#7a84a6"))

            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))

            painter.drawText(
                preg.x() - 10,
                preg.y() - 8,
                labels[i]
            )
        
        # LABELS DE SEÑALES
        painter.setPen(QColor("#7f8db3"))
        painter.setFont(QFont("Segoe UI", 6, QFont.Bold))

        painter.drawText(344, 112, "ALUSrc")
        painter.drawText(528, 112, "MemRead")
        painter.drawText(694, 112, "WriteBack")

        # DIBUJAR BLOQUES
        for name, rect in blocks.items():

            active = name in self.active_blocks

            # COLOR
            if active:

                fill = QColor(self.accent)

                fill.setAlpha(255)

                border = QColor(self.accent)

                pen = QPen(border, 4)

            else:

                fill = QColor("#f8f9ff")

                border = QColor("#d9e2ff")

                pen = QPen(border, 3)

            painter.setPen(pen)

            painter.setBrush(QBrush(fill))

            if active:

                glow = QColor(self.accent)
                glow.setAlpha(40)

                painter.setBrush(QBrush(glow))
                painter.setPen(Qt.NoPen)

                glow_rect = rect.adjusted(-8, -8, 8, 8)

                painter.drawRoundedRect(glow_rect, 26, 26)

                painter.setPen(pen)
                painter.setBrush(QBrush(fill))

            if name == "alu":

                alu_poly = QPolygon([
                    QPoint(rect.left() + 20, rect.top()),
                    QPoint(rect.right() - 10, rect.top()),
                    QPoint(rect.right(), rect.center().y()),
                    QPoint(rect.right() - 10, rect.bottom()),
                    QPoint(rect.left() + 20, rect.bottom()),
                    QPoint(rect.left(), rect.center().y())
                ])
                painter.drawPolygon(alu_poly)

            elif "mux" in name:
                mux_poly = QPolygon([
                    QPoint(rect.left(), rect.top()),
                    QPoint(rect.right(), rect.top() + 15),
                    QPoint(rect.right(), rect.bottom() - 15),
                    QPoint(rect.left(), rect.bottom())
                ])
                painter.drawPolygon(mux_poly)

            elif name in ["imem", "dmem"]:
                painter.drawRect(rect)

            else:
                painter.drawRoundedRect(rect, 20, 20)

            # TEXTO
            painter.setPen(QColor("#44506b"))

            if "mux" in name:
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            else:
                painter.setFont(QFont("Segoe UI", 10, QFont.Bold))

            text_map = {

                "pc": "PC",
                "imem": "Instruction\nMemory",
                "control": "Control",
                "registers": "Registers",
                "alu": "ALU",
                "dmem": "Data\nMemory",
                "wb": "Write Back",
                "mux_alu": "MUX",
                "mux_wb": "MUX"
            }

            painter.drawText(
                rect,
                Qt.AlignCenter,
                text_map[name]
            )

    def draw_arrow(self, painter, x1, y1, x2, y2):

        arrow = 5

        if x2 > x1:

            painter.drawLine(x2, y2, x2 - arrow, y2 - arrow)
            painter.drawLine(x2, y2, x2 - arrow, y2 + arrow)

        elif y2 > y1:

            painter.drawLine(x2, y2, x2 - arrow, y2 - arrow)
            painter.drawLine(x2, y2, x2 + arrow, y2 - arrow)
    
    def draw_path(self, painter, points, active=False):

        color = self.accent if active else "#b8c4e8"

        if active:

            glow_color = QColor(self.accent)
            glow_color.setAlpha(35)

            glow_pen = QPen(glow_color, 4)

            painter.setPen(glow_pen)

            for i in range(len(points) - 1):

                x1, y1 = points[i]
                x2, y2 = points[i + 1]

                painter.drawLine(x1, y1, x2, y2)

        pen = QPen(QColor(color), 3)

        painter.setPen(pen)

        # Dibujar segmentos
        for i in range(len(points) - 1):

            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            painter.drawLine(x1, y1, x2, y2)

        # Flecha final
        x1, y1 = points[-2]
        x2, y2 = points[-1]

        self.draw_arrow(painter, x1, y1, x2, y2)

