from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import *

from src.UI.pages.comparison_page import ComparisonPage
from src.UI.pages.processor_page import ProcessorPage
from src.UI.styles.theme import STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Simulador RISCV Comparativo")
        self.resize(1600, 900)
        self.setMinimumSize(1200, 800)

        self.setStyleSheet(STYLE)

        central = QWidget()
        central.setObjectName("centralBackground")

        # SCROLL AREA
        scroll = QScrollArea()
        scroll.setObjectName("mainScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.viewport().setObjectName("mainScrollViewport")

        # CONTENIDO
        content = QWidget()
        content.setObjectName("mainScrollContent")
        main_layout = QVBoxLayout(content)

        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignTop)

        # TOP CARD
        top_card = QFrame()
        top_card.setObjectName("topCard")

        top_layout = QHBoxLayout()

        left = QVBoxLayout()

        title = QLabel("Simulador RISC-V Comparativo")
        title.setObjectName("mainTitle")

        subtitle = QLabel(
            "Fundamentos de Arquitectura de Computadores"
        )
        subtitle.setObjectName("subtitle")

        left.addWidget(title)
        left.addWidget(subtitle)

        top_layout.addLayout(left)
        top_layout.addStretch()

        self.mode = QComboBox()
        self.mode.setMinimumHeight(55)
        self.mode.addItems([
            "Step by Step",
            "Automático",
            "Completo"
        ])

        self.mode.setFixedWidth(250)
        self.mode.currentIndexChanged.connect(
            self.execution_mode_changed
        )
        top_layout.addWidget(self.mode)

        top_card.setLayout(top_layout)

        # TABS PRINCIPALES
        self.main_tabs = QTabWidget()

        self.proc_a = ProcessorPage(
            "Procesador A",
            "#ff5ca8"
        )

        self.proc_b = ProcessorPage(
            "Procesador B",
            "#25bdb0"
        )

        self.comparison = ComparisonPage(
            self.proc_a,
            self.proc_b
        )
        
        self.main_tabs.addTab(self.proc_a, "Procesador A")
        self.main_tabs.addTab(self.proc_b, "Procesador B")
        self.main_tabs.addTab(self.comparison, "Comparación")
        self.main_tabs.currentChanged.connect(
            self._resize_tabs_to_current_page
        )
        self.proc_a.selector.currentIndexChanged.connect(
            self._resize_tabs_to_current_page
        )
        self.proc_b.selector.currentIndexChanged.connect(
            self._resize_tabs_to_current_page
        )

        # HISTORIAL
        history_card = QFrame()
        history_card.setObjectName("mainCard")

        history_layout = QVBoxLayout()
        history_layout.setContentsMargins(16, 14, 16, 14)
        history_layout.setSpacing(10)

        history_title = QLabel("Historial de Ejecuciones")
        history_title.setObjectName("sectionTitle")

        # Scroll area que contiene las tarjetas de cada ejecucion
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.NoFrame)
        self.history_scroll.setMinimumHeight(180)
        self.history_scroll.setMaximumHeight(240)

        self.history_container = QWidget()
        self.history_inner = QVBoxLayout(self.history_container)
        self.history_inner.setContentsMargins(0, 0, 0, 0)
        self.history_inner.setSpacing(6)
        self.history_inner.addStretch()   # empuja las tarjetas hacia arriba

        self.history_scroll.setWidget(self.history_container)

        history_layout.addWidget(history_title)
        history_layout.addWidget(self.history_scroll)
        history_card.setLayout(history_layout)

        # MAIN
        main_layout.addWidget(top_card)
        main_layout.addSpacing(15)
        main_layout.addWidget(self.main_tabs)
        main_layout.addWidget(history_card)

        content.setLayout(main_layout)

        scroll.setWidget(content)

        layout_central = QVBoxLayout(central)
        layout_central.setContentsMargins(0, 0, 0, 0)
        layout_central.addWidget(scroll)

        self.setCentralWidget(central)
        self.execution_mode_changed()
        self.proc_a.comparison_page = self.comparison
        self.proc_b.comparison_page = self.comparison
        self.proc_a.main_window = self
        self.proc_b.main_window = self
        QTimer.singleShot(0, self._resize_tabs_to_current_page)

    # Badge por arquitectura: (texto_corto, color_hex)
    _ARCH_BADGE = {
        "Procesador Uniciclo":      ("UC", "#ff9f7a"),
        "Procesador Multiciclo":    ("MC", "#78a9ff"),
        "Pipeline con Forwarding":  ("PF", "#8f7cff"),
        "Pipeline con Stalls":      ("PS", "#5fd4be"),
    }

    def add_history(self, entry: dict) -> None:
        """Inserta una tarjeta al principio del historial (max 10 entradas).

        entry debe tener las claves:
            processor    – nombre del procesador ("Procesador A")
            architecture – arquitectura seleccionada
            cycles       – ciclos totales (int)
            instructions – instrucciones ejecutadas (int)
            cpi          – CPI calculado (float)
            total_time   – tiempo total formateado ("12.1 ns")
        """
        arch = entry.get("architecture", "?")
        badge_text, badge_color = self._ARCH_BADGE.get(arch, ("?", "#aaaaaa"))

        # ---- Tarjeta ----
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {badge_color}66;
                border-left: 5px solid {badge_color};
                border-radius: 10px;
            }}
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 14, 8)
        card_layout.setSpacing(14)

        # Badge de arquitectura
        badge = QLabel(badge_text)
        badge.setFixedSize(42, 42)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            background: {badge_color};
            color: white;
            font-weight: bold;
            font-size: 11pt;
            border-radius: 8px;
            border: none;
        """)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(3)

        name_lbl = QLabel(
            f"<b>{entry.get('processor', '?')}</b>"
            f"  —  {arch}"
        )
        name_lbl.setStyleSheet("font-size: 10pt; color: #22264a; border: none;")

        metrics_lbl = QLabel(
            f"Ciclos: <b>{entry.get('cycles', 0)}</b>"
            f"   |   Instrucciones: <b>{entry.get('instructions', 0)}</b>"
            f"   |   CPI: <b>{entry.get('cpi', '—')}</b>"
            f"   |   Tiempo total: <b>{entry.get('total_time', '—')}</b>"
        )
        metrics_lbl.setStyleSheet("font-size: 9pt; color: #556699; border: none;")
        metrics_lbl.setTextFormat(Qt.RichText)

        info_col.addWidget(name_lbl)
        info_col.addWidget(metrics_lbl)

        card_layout.addWidget(badge)
        card_layout.addLayout(info_col)
        card_layout.addStretch()

        # Insertar la tarjeta nueva al principio (indice 0)
        self.history_inner.insertWidget(0, card)

        # Limitar a 10 entradas: eliminar la mas antigua (justo antes del stretch)
        while (self.history_inner.count() - 1) > 10:
            oldest_idx = self.history_inner.count() - 2
            item = self.history_inner.takeAt(oldest_idx)
            if item and item.widget():
                item.widget().deleteLater()

    def _resize_tabs_to_current_page(self, _index=None) -> None:
        """Ajusta el alto del tab activo para evitar espacio vacio innecesario."""
        if not hasattr(self, "main_tabs"):
            return

        current_page = self.main_tabs.currentWidget()

        if current_page is None:
            return

        current_page.updateGeometry()

        # QTabWidget toma como referencia el tab mas alto. Para comparacion,
        # esto dejaba el historial separado por un bloque vacio.
        page_height = max(
            current_page.sizeHint().height(),
            current_page.minimumSizeHint().height()
        )
        tab_height = self.main_tabs.tabBar().sizeHint().height()
        frame_width = self.main_tabs.style().pixelMetric(
            QStyle.PM_DefaultFrameWidth
        )
        target_height = page_height + tab_height + (frame_width * 2)

        self.main_tabs.setMinimumHeight(target_height)
        self.main_tabs.setMaximumHeight(target_height)
    
    def execution_mode_changed(self):

        mode = self.mode.currentText()

        processors = [
            self.proc_a,
            self.proc_b
        ]

        for proc in processors:

            if mode == "Step by Step":

                proc.step_btn.setEnabled(True)
                proc.run_btn.setEnabled(False)
                proc.stop_btn.setEnabled(False)

            elif mode == "Automático":

                proc.step_btn.setEnabled(False)
                proc.run_btn.setEnabled(True)
                proc.stop_btn.setEnabled(True)

                proc.timer.setInterval(400)

            elif mode == "Completo":

                proc.step_btn.setEnabled(False)
                proc.run_btn.setEnabled(True)
                proc.stop_btn.setEnabled(False)

                proc.timer.setInterval(1)

        # BOTONES DE COMPARACION
        if mode == "Step by Step":

            self.comparison.step_btn.setEnabled(True)
            self.comparison.run_btn.setEnabled(False)
            self.comparison.stop_btn.setEnabled(False)

        elif mode == "Automático":

            self.comparison.step_btn.setEnabled(False)
            self.comparison.run_btn.setEnabled(True)
            self.comparison.stop_btn.setEnabled(True)

        elif mode == "Completo":

            self.comparison.step_btn.setEnabled(False)
            self.comparison.run_btn.setEnabled(True)
            self.comparison.stop_btn.setEnabled(False)
