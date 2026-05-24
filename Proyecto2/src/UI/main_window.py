from PySide6.QtCore import Qt
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

        # SCROLL AREA
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # CONTENIDO
        content = QWidget()
        main_layout = QVBoxLayout(content)

        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

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
        main_tabs = QTabWidget()

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
        
        main_tabs.addTab(self.proc_a, "Procesador A")
        main_tabs.addTab(self.proc_b, "Procesador B")
        main_tabs.addTab(self.comparison, "Comparación")

        # HISTORIAL
        history_card = QFrame()
        history_card.setObjectName("mainCard")

        history_layout = QVBoxLayout()

        history_title = QLabel("Historial de Ejecuciones")
        history_title.setObjectName("sectionTitle")

        self.history = QListWidget()

        self.history.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        self.history.setFocusPolicy(Qt.NoFocus)

        # Historial inicialmente vacío
        self.history.clear()
        self.history.setMinimumHeight(180)

        history_layout.addWidget(history_title)
        history_layout.addWidget(self.history)
        history_card.setLayout(history_layout)

        # MAIN
        main_layout.addWidget(top_card)
        main_layout.addSpacing(15)
        main_layout.addWidget(main_tabs)
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

    def add_history(self, text):
        self.history.insertItem(0, text)
        # Mantener máximo 20
        while self.history.count() > 20:
            self.history.takeItem(20)
    
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
