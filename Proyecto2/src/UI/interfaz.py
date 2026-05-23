import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import *
from src.processors import (
    SingleCycleEngine,
    MultiCycleEngine,
    PipelineForwardingEngine,
    PipelineStallEngine
)

# ESTILO GENERAL
STYLE = """
QMainWindow {
    background-color: #f4f7ff;
}

QWidget {
    font-family: Segoe UI;
    color: #44506b;
    font-size: 11pt;
}

QFrame#topCard {
    background:qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8cff,
        stop:0.5 #b07cff,
        stop:1 #ff88b7
    );
    border-radius: 28px;
}

QFrame#mainCard {
    background-color: white;
    border-radius: 28px;
    border: 2px solid #edf0ff;
}

QFrame#metricCard {
    border-radius: 22px;
}

QLabel#mainTitle {
    color: white;
    font-size: 30pt;
    font-weight: bold;
}

QLabel#subtitle {
    color: rgba(255,255,255,0.85);
    font-size: 12pt;
}

QLabel#sectionTitle {
    font-size: 14pt;
    font-weight: bold;
    color: #5a67a5;
}

QPushButton {
    border: none;
    border-radius: 16px;
    padding: 12px;
    color: white;
    font-weight: bold;
    font-size: 11pt;
}

QPushButton:hover {
    opacity: 0.8;
}

QComboBox {
    background-color: rgba(255,255,255,0.95);
    border: 2px solid #e4e8ff;
    border-radius: 18px;
    padding: 14px;
    padding-left: 18px;
    font-size: 11pt;
    font-weight: bold;
    color: #5865a5;
    min-height: 24px;
}

QComboBox:hover {
    border: 2px solid #cfd8ff;
    background-color: white;
}

QComboBox::drop-down {
    border: none;
    width: 40px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid #7c88c9;
    margin-right: 14px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 2px solid #e4e8ff;
    border-radius: 18px;
    padding: 10px;
    selection-background-color: #eef2ff;
    selection-color: #5a67a5;
    outline: none;
}

QTabWidget::pane {
    border: none;
}

QTabBar::tab {
    background-color: #eef1ff;
    padding: 14px 24px;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    margin-right: 10px;
    font-weight: bold;
    color: #6975b4;
}

QTabBar::tab:selected {
    background-color: white;
}

QPlainTextEdit {
    background-color: #fbfcff;
    border-radius: 20px;
    border: 2px solid #e5e9ff;
    padding: 14px;
    font-size: 11pt;
}

QTableWidget {
    background-color: white;
    border-radius: 20px;
    border: 2px solid #e5e9ff;
    gridline-color: #edf0ff;
}

QHeaderView::section {
    background-color: #e5eeff;
    border: none;
    padding: 10px;
    font-weight: bold;
    color: #55639a;
}

QListWidget {
    background-color: white;
    border-radius: 20px;
    border: 2px solid #e5e9ff;
    padding: 10px;
}

QScrollBar:vertical {
    background: rgba(255,255,255,0.7);
    width: 22px;
    margin: 12px 6px 12px 6px;
    border-radius: 11px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #8f7cff,
        stop:1 #ff7eb6
    );

    min-height: 80px;
    border-radius: 10px;
    border: 4px solid rgba(255,255,255,0.7);
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #7a68ff,
        stop:1 #ff63a6
    );
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    height: 0px;
    max-height: 0px;
    background: transparent;
}

QScrollBar:horizontal {
    background: rgba(255,255,255,0.7);
    height: 20px;
    margin: 6px 12px 6px 12px;
    border-radius: 10px;
}

"""

# METRIC CARD
class MetricCard(QFrame):

    def __init__(self, title, value, color):
        super().__init__()

        self.setObjectName("metricCard")

        self.setStyleSheet(f"""
        QFrame#metricCard {{
            background-color: {color};
        }}
        """)

        self.setMinimumHeight(120)

        layout = QVBoxLayout()

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.title_label.setStyleSheet("""
            font-size: 11pt;
            font-weight: bold;
            color: #5a6484;
        """)

        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignCenter)

        self.value_label.setStyleSheet("""
            font-size: 24pt;
            font-weight: bold;
            color: #33415c;
        """)

        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

        self.setLayout(layout)

    def set_value(self, value):
        self.value_label.setText(str(value))

# PANEL PROCESADOR
class ProcessorPage(QWidget):

    def __init__(self, name, accent):
        super().__init__()
        self.current_cycle = 0
        self.running = False
        self.processor_name = name

        self.snapshots = []

        self.engine = None

        self.pipeline_data = []
        self.pipeline = QTableWidget(0, 5)

        self.pipeline_states = [
            ("IF",  "lw x1, 0(x0)",  "#78a9ff"),
            ("ID",  "add x2, x1, x3", "#8f7cff"),
            ("EX",  "stall", "#ff9f7a"),
            ("MEM", "sw x4, 0(x5)", "#5fd4be"),
            ("WB",  "addi x6, x0, 1", "#ff7fa8")
        ]

        self.timer = QTimer()
        self.timer.timeout.connect(self.step_execution)

        main_layout = QVBoxLayout()

        # CARD PRINCIPAL
        main_card = QFrame()
        main_card.setObjectName("mainCard")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(30, 20, 30, 20)
        card_layout.setSpacing(14)

        # TITULO
        title_layout = QHBoxLayout()

        badge = QLabel(name[-1])
        badge.setFixedSize(50, 50)
        badge.setAlignment(Qt.AlignCenter)

        badge.setStyleSheet(f"""
            background-color: {accent};
            color: white;
            border-radius: 25px;
            font-size: 18pt;
            font-weight: bold;
        """)

        title = QLabel(name)

        title.setStyleSheet(f"""
            font-size: 24pt;
            font-weight: bold;
            color: {accent};
        """)

        title_layout.addWidget(badge)
        title_layout.addWidget(title)
        title_layout.addStretch()

        # SELECTOR
        self.selector = QComboBox()
        self.selector.setMinimumHeight(55)

        self.selector.addItems([
            "Pipeline con Forwarding",
            "Pipeline con Stalls",
            "Procesador Multiciclo",
            "Procesador Uniciclo"
        ])

        self.selector.setCurrentText("Procesador Uniciclo")

        self.selector.currentIndexChanged.connect(
            self.architecture_changed
        )

        # BOTONES
        buttons_layout = QHBoxLayout()

        self.step_btn = QPushButton("▶ Step")
        self.run_btn = QPushButton("⏵ Run")
        self.reset_btn = QPushButton("⟳ Reset")
        self.stop_btn = QPushButton("■ Stop")

        self.step_btn.setStyleSheet("""
            background-color: #78a9ff;
        """)

        self.run_btn.setStyleSheet("""
            background-color: #8f7cff;
        """)

        self.reset_btn.setStyleSheet("""
            background-color: #5fd4be;
        """)

        self.stop_btn.setStyleSheet("""
            background-color: #ff7fa8;
        """)

        buttons_layout.addWidget(self.step_btn)
        buttons_layout.addWidget(self.run_btn)
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addWidget(self.stop_btn)

        self.step_btn.clicked.connect(
            self.step_execution
        )

        self.run_btn.clicked.connect(
            self.run_execution
        )

        self.reset_btn.clicked.connect(
            self.reset_execution
        )

        self.stop_btn.clicked.connect(
            self.stop_execution
        )

        # TABS INTERNOS
        inner_tabs = QTabWidget()

        # TAB EJECUCION
        execution_tab = QWidget()
        execution_layout = QVBoxLayout()

        top_split = QHBoxLayout()

        top_split.setStretch(0, 1)
        top_split.setStretch(1, 0)

        # EDITOR
        editor_container = QVBoxLayout()

        editor_title = QLabel("Editor de Código RISCV")
        editor_title.setObjectName("sectionTitle")

        self.editor = QPlainTextEdit()

        self.editor.setPlaceholderText(
        """Escriba aquí su programa RISC-V..."""
        )

        self.editor.setMinimumHeight(320)

        editor_container.addWidget(editor_title)
        editor_container.addWidget(self.editor)

        # PIPELINE
        pipeline_container = QVBoxLayout()

        pipeline_title = QLabel("Pipeline")
        pipeline_title.setObjectName("sectionTitle")

        self.pipeline = QTableWidget(0, 5)

        self.pipeline.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.pipeline.setHorizontalHeaderLabels([
            "IF", "ID", "EX", "MEM", "WB"
        ])

        self.pipeline.verticalHeader().setVisible(False)

        # CONFIGURACION PIPELINE
        self.pipeline.setMinimumWidth(0)
        self.pipeline.setMaximumWidth(700)
        self.pipeline.setFixedWidth(700)

        self.pipeline.setMinimumHeight(320)

        self.pipeline.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding
        )

        # Scroll horizontal desactivado
        self.pipeline.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        # Solo vertical
        self.pipeline.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        # Texto cortado
        self.pipeline.setWordWrap(False)
        self.pipeline.setTextElideMode(Qt.ElideRight)

        # Columnas fijas
        header = self.pipeline.horizontalHeader()

        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
            self.pipeline.setColumnWidth(i, 135)

        # Filas
        self.pipeline.verticalHeader().setDefaultSectionSize(58)

        self.pipeline.verticalHeader().setSectionResizeMode(
            QHeaderView.Fixed
        )

        # TEXTO
        self.pipeline.setWordWrap(False)

        self.pipeline.setTextElideMode(Qt.ElideRight)

        # ESTILO EXTRA
        self.pipeline.setShowGrid(True)

        self.pipeline.setCornerButtonEnabled(False)

        self.update_pipeline_table()

        pipeline_container.addWidget(pipeline_title)
        pipeline_container.addWidget(self.pipeline)

        # ESTADO ACTUAL DEL PIPELINE
        pipeline_state_title = QLabel("Estado Actual")
        pipeline_state_title.setObjectName("sectionTitle")

        state_container = QFrame()

        state_container.setStyleSheet("""
            background-color: #f8f9ff;
            border: 2px solid #e5e9ff;
            border-radius: 22px;
        """)

        state_layout = QVBoxLayout()
        state_layout.setContentsMargins(14, 14, 14, 14)
        state_layout.setSpacing(10)

        stages = [
            ("IF", "", "#78a9ff"),
            ("ID", "", "#8f7cff"),
            ("EX", "", "#ff9f7a"),
            ("MEM", "", "#5fd4be"),
            ("WB", "", "#ff7fa8")
        ]

        self.pipeline_stage_labels = {}

        for stage, instruction, color in stages:

            row = QFrame()

            row.setMaximumHeight(56)

            row.setStyleSheet(f"""
                background-color: white;
                border-radius: 16px;
                border: 2px solid {color};
            """)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(12, 10, 12, 10)

            stage_label = QLabel(stage)

            stage_label.setFixedSize(60, 34)

            stage_label.setSizePolicy(
                QSizePolicy.Fixed,
                QSizePolicy.Fixed
            )

            stage_label.setStyleSheet(f"""
                background-color: {color};
                color: white;
                font-weight: bold;
                font-size: 11pt;

                border-radius: 10px;

                padding-left: 6px;
                padding-right: 6px;

                min-width: 60px;
                max-width: 60px;

                qproperty-alignment: AlignCenter;
            """)

            instruction_label = QLabel(instruction)

            instruction_label.setFixedHeight(24)

            instruction_label.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Preferred
            )

            instruction_label.setWordWrap(False)

            instruction_label.setTextInteractionFlags(Qt.NoTextInteraction)

            instruction_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            instruction_label.setStyleSheet("""
                color: #55639a;
                font-weight: bold;
                font-size: 11pt;
                border: none;
            """)

            self.pipeline_stage_labels[stage] = instruction_label

            row_layout.addWidget(stage_label)
            row_layout.addSpacing(10)
            row_layout.addWidget(instruction_label)
            row_layout.addStretch()

            row.setLayout(row_layout)

            state_layout.addWidget(row)

        state_container.setLayout(state_layout)

        pipeline_container.addSpacing(12)
        pipeline_container.addWidget(pipeline_state_title)
        pipeline_container.addWidget(state_container)

        top_split.addLayout(editor_container, 1)
        pipeline_widget = QWidget()
        pipeline_widget.setLayout(pipeline_container)

        pipeline_widget.setMinimumWidth(720)
        pipeline_widget.setMaximumWidth(720)

        top_split.addWidget(pipeline_widget)

        # DATAPATH
        circuit_title = QLabel("Datapath")
        circuit_title.setObjectName("sectionTitle")

        circuit_frame = QFrame()

        circuit_frame.setMinimumHeight(340)

        circuit_frame.setStyleSheet(f"""
            background: qlineargradient(
                x1:0,
                y1:0,
                x2:1,
                y2:1,
                stop:0 #fcfcff,
                stop:1 #f3f5ff
            );

            border: 4px solid {accent};
            border-radius: 34px;
        """)

        # METRICAS
        metrics_title = QLabel("Métricas")
        metrics_title.setObjectName("sectionTitle")

        metrics_layout = QHBoxLayout()

        self.metric_cycles = MetricCard(
            "Ciclos",
            "0",
            "#dff8f1"
        )

        self.metric_instructions = MetricCard(
            "Instrucciones",
            "0",
            "#eee5ff"
        )

        self.metric_cpi = MetricCard(
            "CPI",
            "0",
            "#fff1d9"
        )

        self.metric_time = MetricCard(
            "Tiempo",
            "0 ns",
            "#dff5ff"
        )

        self.metric_pc = MetricCard(
            "PC",
            "0x0000",
            "#ffe5ec"
        )

        self.metric_total = MetricCard(
            "Tiempo Total",
            "0 ns",
            "#e4f0ff"
        )

        metrics_layout.addWidget(self.metric_cycles)
        metrics_layout.addWidget(self.metric_instructions)
        metrics_layout.addWidget(self.metric_cpi)
        metrics_layout.addWidget(self.metric_time)
        metrics_layout.addWidget(self.metric_pc)
        metrics_layout.addWidget(self.metric_total)

        # HAZARDS
        hazard_title = QLabel("Hazards Detectados")
        hazard_title.setObjectName("sectionTitle")

        self.hazard_box = QListWidget()

        # BLOQUEAR INTERACCION
        self.hazard_box.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        self.hazard_box.setFocusPolicy(Qt.NoFocus)

        self.hazard_box.setMaximumHeight(140)

        # ARMAR TAB
        execution_layout.addLayout(top_split)
        execution_layout.addSpacing(20)

        execution_layout.addWidget(circuit_title)
        execution_layout.addWidget(circuit_frame)

        execution_layout.addSpacing(20)

        execution_layout.addWidget(metrics_title)
        execution_layout.addLayout(metrics_layout)

        execution_layout.addSpacing(20)

        execution_layout.addWidget(hazard_title)
        execution_layout.addWidget(self.hazard_box)

        execution_tab.setLayout(execution_layout)

        # TAB HARDWARE
        hardware_tab = QWidget()
        hardware_layout = QHBoxLayout()

        # REGISTROS
        reg_layout = QVBoxLayout()
        reg_title = QLabel("Registros")
        reg_title.setObjectName("sectionTitle")

        self.registers = QTableWidget(32, 2)

        self.registers.setAlternatingRowColors(True)

        self.registers.setHorizontalHeaderLabels([
            "Registro",
            "Valor"
        ])

        self.registers.verticalHeader().setVisible(False)

        self.registers.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.registers.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.registers.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        for i in range(32):

            self.registers.setItem(
                i,
                0,
                QTableWidgetItem(f"x{i}")
            )

            self.registers.setItem(
                i,
                1,
                QTableWidgetItem("0")
            )

        reg_layout.addWidget(reg_title)
        reg_layout.addWidget(self.registers, 1)

        # MEMORIA
        mem_layout = QVBoxLayout()

        mem_title = QLabel("Memoria")
        mem_title.setObjectName("sectionTitle")

        self.memory = QTableWidget(64, 2)

        self.memory.setAlternatingRowColors(True)

        self.memory.setHorizontalHeaderLabels([
            "Dirección",
            "Valor"
        ])

        self.memory.verticalHeader().setVisible(False)

        self.memory.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.memory.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.memory.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        for i in range(64):

            self.memory.setItem(
                i,
                0,
                QTableWidgetItem(hex(i * 4))
            )

            self.memory.setItem(
                i,
                1,
                QTableWidgetItem("0")
            )

        mem_layout.addWidget(mem_title)
        mem_layout.addWidget(self.memory, 1)

        hardware_layout.addLayout(reg_layout, 1)
        hardware_layout.addLayout(mem_layout, 1)

        hardware_tab.setLayout(hardware_layout)

        # AGREGAR TABS
        inner_tabs.addTab(execution_tab, "Código")
        inner_tabs.addTab(hardware_tab, "Hardware")

        # ARMAR CARD
        card_layout.addLayout(title_layout)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.selector)
        card_layout.addSpacing(10)
        card_layout.addLayout(buttons_layout)
        card_layout.addSpacing(20)
        card_layout.addWidget(inner_tabs)

        main_card.setLayout(card_layout)

        main_layout.addWidget(main_card)
        main_layout.addStretch()
        main_card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.setLayout(main_layout)

    # CAMBIO DE ARQUITECTURA
    def architecture_changed(self):

        self.reset_execution()

        if hasattr(self, "comparison_page"):
            self.comparison_page.update_comparison()

    # FORMATEAR INSTRUCCION
    def format_instruction(self, instruction):

        if instruction is None:
            return "-"

        if hasattr(instruction, "complete_instruction"):
            return instruction.complete_instruction

        # Convertir a string
        text = str(instruction)

        # Cortar texto muy largo
        if len(text) > 35:
            text = text[:35] + "..."

        return text
            
    # ACTUALIZAR PIPELINE
    def update_pipeline_table(self):

        self.pipeline.setRowCount(len(self.pipeline_data))

        for row in range(len(self.pipeline_data)):

            for col in range(len(self.pipeline_data[row])):

                value = self.pipeline_data[row][col]

                # Extraer solo instrucción
                if hasattr(value, "instruction"):

                    text = self.format_instruction(
                        value.instruction
                    )

                else:

                    text = self.format_instruction(value)

                item = QTableWidgetItem(text)

                item.setTextAlignment(Qt.AlignCenter)

                # Stall / burbuja
                if (
                    text.lower() == "stall"
                    or text == "-"
                ):
                    item.setBackground(QColor("#ffe0e0"))

                # Flush
                elif "flush" in text.lower():
                    item.setBackground(QColor("#fff0c9"))

                # Instrucción normal
                else:
                    item.setBackground(QColor("#e8f0ff"))

                self.pipeline.setItem(row, col, item)

    # ACTUALIZAR ESTADO PIPELINE
    def update_pipeline_state(self, snapshot):

        # MULTICICLO
        if hasattr(snapshot, "stage") and snapshot.stage is not None:

            # Limpiar labels
            for stage in ["IF", "ID", "EX", "MEM", "WB"]:
                self.pipeline_stage_labels[stage].setText("")

            stage_map = {
                "FETCH": "IF",
                "DECODE": "ID",
                "EXECUTE": "EX",
                "MEMORY": "MEM",
                "WRITEBACK": "WB"
            }

            current_stage = stage_map.get(snapshot.stage)

            if current_stage:

                instruction_text = self.format_instruction(snapshot.ir)

                extra = ""

                if snapshot.stage == "DECODE":
                    extra = f"\nA={snapshot.a} B={snapshot.b}"

                elif snapshot.stage == "EXECUTE":
                    extra = f"\nALU_OUT={snapshot.alu_out}"

                elif snapshot.stage == "MEMORY":
                    extra = f"\nMDR={snapshot.mdr}"

                text = f"{instruction_text}{extra}"

                self.pipeline_stage_labels[current_stage].setText(text)

            return

        # UNICICLO
        if not hasattr(snapshot, "if_id"):

            instruction_text = "-"

            if hasattr(snapshot, "current_instruction"):

                instruction = snapshot.current_instruction

                if instruction is not None:

                    if hasattr(instruction, "complete_instruction"):
                        instruction_text = instruction.complete_instruction
                    else:
                        instruction_text = str(instruction)

            for stage in ["IF", "ID", "EX", "MEM", "WB"]:
                self.pipeline_stage_labels[stage].setText(instruction_text)

            return

        # PIPELINE FORWARDING / STALLS
        stage_data = {
            "IF": snapshot.if_id,
            "ID": snapshot.id_ex,
            "EX": snapshot.ex_mem,
            "MEM": snapshot.mem_wb,
            "WB": None
        }

        for stage, pipe_reg in stage_data.items():

            text = "-"

            if pipe_reg is not None:

                instruction = getattr(pipe_reg, "instruction", None)

                # Burbuja / stall
                if instruction is None:

                    if stage == "EX" and hasattr(snapshot, "stalled") and snapshot.stalled:
                        text = "STALL"

                    else:
                        text = "-"

                else:

                    text = self.format_instruction(instruction)

            self.pipeline_stage_labels[stage].setText(text)

            label = self.pipeline_stage_labels[stage]

            # Stall
            if text == "STALL":

                label.setStyleSheet("""
                    color: #d64545;
                    font-weight: bold;
                    font-size: 11pt;
                    border: none;
                """)

            # Vacío
            elif text == "-":

                label.setStyleSheet("""
                    color: #9aa3c7;
                    font-weight: bold;
                    font-size: 11pt;
                    border: none;
                """)

            # Normal
            else:

                label.setStyleSheet("""
                    color: #55639a;
                    font-weight: bold;
                    font-size: 11pt;
                    border: none;
                """)

        # HAZARDS Y FORWARDING
        if hasattr(snapshot, "stalled") and snapshot.stalled:
            self.hazard_box.addItem(
                "Stall detectado (load-use hazard)"
            )

        if hasattr(snapshot, "flushed") and snapshot.flushed:
            self.hazard_box.addItem(
                "Flush por branch tomado"
            )

        if hasattr(snapshot, "forward_a") and snapshot.forward_a != "ID/EX":
            self.hazard_box.addItem(
                f"Forward A desde {snapshot.forward_a}"
            )

        if hasattr(snapshot, "forward_b") and snapshot.forward_b != "ID/EX":
            self.hazard_box.addItem(
                f"Forward B desde {snapshot.forward_b}"
            )

    # ACTUALIZAR METRICAS
    def update_metrics(self, snapshot):

        metrics = snapshot.metrics.get_metrics()

        cycles = metrics.get("cycles", 0)
        instructions = metrics.get("instructions", 0)

        cpi = 0

        if instructions > 0:
            cpi = round(cycles / instructions, 2)

        self.metric_cycles.set_value(cycles)

        self.metric_instructions.set_value(
            instructions
        )

        self.metric_cpi.set_value(cpi)

        self.metric_time.set_value(
            f"{cycles * 4} ns"
        )

        self.metric_pc.set_value(
            hex(snapshot.pc)
        )

        self.metric_total.set_value(
            f"{cycles * 4} ns"
        )
    
    # ACTUALIZAR REGISTROS
    def update_registers(self, snapshot):

        for i in range(32):

            value = snapshot.registers[i]

            self.registers.setItem(
                i,
                1,
                QTableWidgetItem(str(value))
            )

    # ACTUALIZAR MEMORIA
    def update_memory(self, snapshot):

        for i in range(64):

            value = snapshot.memory.get(i * 4, 0)

            self.memory.setItem(
                i,
                1,
                QTableWidgetItem(str(value))
            )

    # STEP
    def step_execution(self):

        if self.engine is None:
            self.load_program_into_engine()

        if not self.engine.program_loaded:

            self.engine.load_program(
                self.editor.toPlainText()
            )

            self.engine.program_loaded = True

        executed = self.engine.step()

        if not executed:

            self.timer.stop()

            if self.hazard_box.count() == 0 or \
                self.hazard_box.item(self.hazard_box.count()-1).text() != "Programa finalizado":
                    self.hazard_box.addItem("Programa finalizado")

            return

        snapshot = self.engine.get_snapshot()
        self.hazard_box.clear()

        # Actualizar pipeline
        if (
            hasattr(snapshot, "pipeline")
            and snapshot.pipeline
        ):

            self.pipeline_data = snapshot.pipeline
            self.update_pipeline_table()

        self.update_pipeline_state(snapshot)

        # Actualizar métricas
        self.update_metrics(snapshot)

        # Actualizar registros
        self.update_registers(snapshot)

        # Actualizar memoria
        self.update_memory(snapshot)

        self.main_window.add_history(
            f"{self.processor_name} - Step ciclo {snapshot.metrics.get_metrics().get('cycles', 0)}"
        )

    # RUN
    def run_execution(self):

        if self.engine is None:
            self.load_program_into_engine()
        
        if not self.engine.program_loaded:

            self.engine.load_program(
                self.editor.toPlainText()
            )

            self.engine.program_loaded = True

        self.running = True
        mode = self.main_window.mode.currentText()

        # Ejecutar un ciclo cada 400 ms
        if mode == "Completo":

            while self.engine.step():

                snapshot = self.engine.get_snapshot()

                if (
                    hasattr(snapshot, "pipeline")
                    and snapshot.pipeline
                ):
                    self.pipeline_data = snapshot.pipeline

            snapshot = self.engine.get_snapshot()
            self.update_pipeline_table()
            self.pipeline.setRowCount(len(self.pipeline_data))
            self.update_metrics(snapshot)
            self.update_registers(snapshot)
            self.update_memory(snapshot)
            self.hazard_box.addItem(
                "Ejecución completa finalizada"
            )
            self.main_window.add_history(
                f"{self.processor_name} - Ejecución completa finalizada"
            )
            self.update_pipeline_state(snapshot)

            QApplication.processEvents()
        else:
            self.timer.start(400)

    # RESET
    def reset_execution(self):

        self.timer.stop()

        self.running = False

        self.current_cycle = 0

        self.metric_cycles.set_value("0")
        self.metric_instructions.set_value("0")
        self.metric_cpi.set_value("0")
        self.metric_time.set_value("0 ns")
        self.metric_pc.set_value("0x0000")
        self.metric_total.set_value("0 ns")

        self.hazard_box.clear()

        self.pipeline.clearContents()
        self.pipeline.setRowCount(0)
        self.pipeline_data = []

        for stage in self.pipeline_stage_labels:
            self.pipeline_stage_labels[stage].setText("")

        for i in range(32):

            self.registers.setItem(
                i,
                1,
                QTableWidgetItem("0")
            )

        for i in range(64):

            self.memory.setItem(
                i,
                1,
                QTableWidgetItem("0")
            )

        self.create_engine()

        self.engine.load_program(
            self.editor.toPlainText()
        )

    # STOP
    def stop_execution(self):

        self.running = False
        self.timer.stop()

    # SNAPSHOT
    def save_snapshot(self):

        snapshot = {

            "cycle": self.current_cycle,

            "architecture":
            self.selector.currentText(),

            "metrics": {

                "cycles":
                self.metric_cycles.value_label.text(),

                "instructions":
                self.metric_instructions.value_label.text(),

                "cpi":
                self.metric_cpi.value_label.text(),

                "time":
                self.metric_time.value_label.text(),

                "pc":
                self.metric_pc.value_label.text()
            },

            "pipeline":
            self.pipeline_data,

            "code":
            self.editor.toPlainText()
        }

        self.snapshots.append(snapshot)

    # CARGAR SNAPSHOT
    def load_snapshot(self, snapshot):

        self.current_cycle = snapshot["cycle"]

        self.editor.setPlainText(
            snapshot["code"]
        )

        self.update_metrics(snapshot)

        self.pipeline_data = snapshot["pipeline"]

        self.update_pipeline_table()

    # CREAR ENGINE
    def create_engine(self):

        architecture = self.selector.currentText()

        if architecture == "Procesador Uniciclo":

            self.engine = SingleCycleEngine()

        elif architecture == "Procesador Multiciclo":

            self.engine = MultiCycleEngine()

        elif architecture == "Pipeline con Forwarding":

            self.engine = PipelineForwardingEngine()

        elif architecture == "Pipeline con Stalls":

            self.engine = PipelineStallEngine()

        self.engine.program_loaded = False
    
    # CARGAR PROGRAMA EN ENGINE
    def load_program_into_engine(self):

        source_code = self.editor.toPlainText()

        self.create_engine()

        self.engine.load_program(source_code)

        self.running = False

# PAGINA COMPARACION
class ComparisonPage(QWidget):

    def __init__(self, proc_a, proc_b):
        super().__init__()

        self.proc_a = proc_a
        self.proc_b = proc_b

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)

        # CARD PRINCIPAL
        main_card = QFrame()
        main_card.setObjectName("mainCard")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(22, 16, 22, 16)
        card_layout.setSpacing(14)

        # TITULO
        title = QLabel("Comparación de Arquitecturas")
        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size: 20pt;
            font-weight: bold;
            color: #7078d6;

            padding: 0px;
            margin: 0px;
            min-height: 32px;
            max-height: 32px;
        """)

        card_layout.addWidget(title)

        # CONTENIDO CENTRAL
        compare_layout = QHBoxLayout()
        compare_layout.setSpacing(12)

        # PROCESADOR A
        left_card = QFrame()

        left_card.setStyleSheet("""
            background-color: #fff5fa;
            border: 2px solid #ffd9ea;
            border-radius: 34px;
        """)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(20)

        # HEADER
        left_header = QFrame()

        left_header.setStyleSheet("""
            background-color: white;
            border-radius: 24px;
            border: 2px solid #ffe4f0;
        """)

        left_header_layout = QVBoxLayout()
        left_header_layout.setContentsMargins(18, 18, 18, 18)

        left_title = QLabel("Procesador A")
        left_title.setAlignment(Qt.AlignCenter)

        left_title.setStyleSheet("""
            font-size: 20pt;
            font-weight: bold;
            color: #ff5ca8;
        """)

        self.left_type = QLabel(
            self.proc_a.selector.currentText()
        )
        self.left_type.setAlignment(Qt.AlignCenter)

        self.left_type.setStyleSheet("""
            color: #8b7c93;
            font-size: 11pt;
            font-weight: bold;
        """)

        left_header_layout.addWidget(left_title)
        left_header_layout.addWidget(self.left_type)

        left_header.setLayout(left_header_layout)

        # MINI DATAPATH
        datapath_a = QFrame()
        datapath_a.setMinimumHeight(180)

        datapath_a.setStyleSheet("""
            background-color: white;
            border-radius: 28px;
            border: 2px solid #ffe4f0;
        """)

        datapath_layout_a = QVBoxLayout()
        datapath_layout_a.setContentsMargins(18, 18, 18, 18)
        datapath_layout_a.setSpacing(16)

        datapath_title_a = QLabel("Vista del Datapath")
        datapath_title_a.setAlignment(Qt.AlignCenter)

        datapath_title_a.setStyleSheet("""
            font-size: 12pt;
            font-weight: bold;
            color: #ff5ca8;
        """)

        self.datapath_visual_a = QLabel(
            "Diagrama del procesador"
        )

        self.datapath_visual_a.setAlignment(Qt.AlignCenter)

        self.datapath_visual_a.setMinimumHeight(600)

        self.datapath_visual_a.setStyleSheet("""
            background-color: #fff7fb;
            border-radius: 22px;
            border: 2px dashed #ffd9ea;

            padding: 20px;

            font-size: 11pt;
            font-weight: bold;
            color: #c78bab;
        """)

        datapath_layout_a.addWidget(datapath_title_a)
        datapath_layout_a.addWidget(self.datapath_visual_a)

        datapath_a.setLayout(datapath_layout_a)

        # METRICAS
        metrics_a = QFrame()

        metrics_a.setStyleSheet("""
            background-color: white;
            border-radius: 28px;
            border: 2px solid #ffe4f0;
        """)

        metrics_layout_a = QVBoxLayout()
        metrics_layout_a.setContentsMargins(20, 20, 20, 20)
        metrics_layout_a.setSpacing(14)

        metrics_title_a = QLabel("Resumen")
        metrics_title_a.setAlignment(Qt.AlignCenter)

        metrics_title_a.setStyleSheet("""
            font-size: 13pt;
            font-weight: bold;
            color: #ff5ca8;
            padding-bottom: 6px;
        """)

        metrics_layout_a.addWidget(metrics_title_a)

        self.metric_labels_a = {}

        metric_names = [
            "CPI",
            "Ciclos",
            "Tiempo",
            "Estado"
        ]

        for name in metric_names:

            row_frame = QFrame()

            row_frame.setStyleSheet("""
                background-color: #fff9fc;
                border-radius: 16px;
                border: 1px solid #ffe9f2;
            """)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(14, 10, 14, 10)

            left = QLabel(name)

            left.setStyleSheet("""
                font-weight: bold;
                color: #727aa0;
                font-size: 11pt;
                border: none;
            """)

            right = QLabel("-")

            right.setStyleSheet("""
                font-weight: bold;
                color: #ff5ca8;
                font-size: 11pt;
                border: none;
            """)

            self.metric_labels_a[name] = right

            row_layout.addWidget(left)
            row_layout.addStretch()
            row_layout.addWidget(right)

            row_frame.setLayout(row_layout)

            metrics_layout_a.addWidget(row_frame)

        metrics_a.setLayout(metrics_layout_a)

        # ARMAR
        left_layout.addWidget(left_header)
        left_layout.addWidget(datapath_a)
        left_layout.addWidget(metrics_a)

        left_card.setLayout(left_layout)

        # PROCESADOR B
        right_card = QFrame()

        right_card.setStyleSheet("""
            background-color: #f3fcff;
            border: 2px solid #d6f1f7;
            border-radius: 34px;
        """)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(20)

        # HEADER
        right_header = QFrame()

        right_header.setStyleSheet("""
            background-color: white;
            border-radius: 24px;
            border: 2px solid #e1f7fb;
        """)

        right_header_layout = QVBoxLayout()
        right_header_layout.setContentsMargins(18, 18, 18, 18)

        right_title = QLabel("Procesador B")
        right_title.setAlignment(Qt.AlignCenter)

        right_title.setStyleSheet("""
            font-size: 20pt;
            font-weight: bold;
            color: #25bdb0;
        """)

        self.right_type = QLabel(
            self.proc_b.selector.currentText()
        )
        self.right_type.setAlignment(Qt.AlignCenter)

        self.right_type.setStyleSheet("""
            color: #758a91;
            font-size: 11pt;
            font-weight: bold;
        """)

        right_header_layout.addWidget(right_title)
        right_header_layout.addWidget(self.right_type)

        right_header.setLayout(right_header_layout)

        # MINI DATAPATH
        datapath_b = QFrame()
        datapath_b.setMinimumHeight(180)

        datapath_b.setStyleSheet("""
            background-color: white;
            border-radius: 28px;
            border: 2px solid #dff5f2;
        """)

        datapath_layout_b = QVBoxLayout()
        datapath_layout_b.setContentsMargins(18, 18, 18, 18)
        datapath_layout_b.setSpacing(16)

        datapath_title_b = QLabel("Vista del Datapath")
        datapath_title_b.setAlignment(Qt.AlignCenter)

        datapath_title_b.setStyleSheet("""
            font-size: 12pt;
            font-weight: bold;
            color: #25bdb0;
        """)

        self.datapath_visual_b = QLabel(
            "Diagrama del procesador"
        )

        self.datapath_visual_b.setAlignment(Qt.AlignCenter)

        self.datapath_visual_b.setMinimumHeight(600)

        self.datapath_visual_b.setStyleSheet("""
            background-color: #f5fffd;
            border-radius: 22px;
            border: 2px dashed #d7f4ef;

            padding: 20px;

            font-size: 11pt;
            font-weight: bold;
            color: #7db7af;
        """)

        datapath_layout_b.addWidget(datapath_title_b)
        datapath_layout_b.addWidget(self.datapath_visual_b)

        datapath_b.setLayout(datapath_layout_b)

        # METRICAS
        metrics_b = QFrame()

        metrics_b.setStyleSheet("""
            background-color: white;
            border-radius: 28px;
            border: 2px solid #dff5f2;
        """)

        metrics_layout_b = QVBoxLayout()
        metrics_layout_b.setContentsMargins(20, 20, 20, 20)
        metrics_layout_b.setSpacing(14)

        metrics_title_b = QLabel("Resumen")
        metrics_title_b.setAlignment(Qt.AlignCenter)

        metrics_title_b.setStyleSheet("""
            font-size: 13pt;
            font-weight: bold;
            color: #25bdb0;
            padding-bottom: 6px;
        """)

        metrics_layout_b.addWidget(metrics_title_b)

        self.metric_labels_b = {}

        metric_names = [
            "CPI",
            "Ciclos",
            "Tiempo",
            "Estado"
        ]

        for name in metric_names:

            row_frame = QFrame()

            row_frame.setStyleSheet("""
                background-color: #f8fffe;
                border-radius: 16px;
                border: 1px solid #e4f8f5;
            """)

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(14, 10, 14, 10)

            left = QLabel(name)

            left.setStyleSheet("""
                font-weight: bold;
                color: #727aa0;
                font-size: 11pt;
                border: none;
            """)

            right = QLabel("-")

            right.setStyleSheet("""
                font-weight: bold;
                color: #25bdb0;
                font-size: 11pt;
                border: none;
            """)

            self.metric_labels_b[name] = right

            row_layout.addWidget(left)
            row_layout.addStretch()
            row_layout.addWidget(right)

            row_frame.setLayout(row_layout)

            metrics_layout_b.addWidget(row_frame)

        metrics_b.setLayout(metrics_layout_b)

        # ARMAR
        right_layout.addWidget(right_header)
        right_layout.addWidget(datapath_b)
        right_layout.addWidget(metrics_b)

        right_card.setLayout(right_layout)

        # AGREGAR
        compare_layout.addWidget(left_card)
        compare_layout.addWidget(right_card)

        card_layout.addLayout(compare_layout)

        # RESULTADO FINAL
        summary = QFrame()
        
        summary.setStyleSheet("""
            background-color: #f7f5ff;
            border: 2px solid #e7e1ff;
            border-radius: 30px;
        """)

        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(22, 22, 22, 22)
        summary_layout.setSpacing(18)

        summary_title = QLabel(
            "Resultado de la Comparación"
        )

        summary_title.setAlignment(Qt.AlignCenter)

        summary_title.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: #7b69dc;

            padding: 0px;
            margin: 0px;

            min-height: 24px;
            max-height: 24px;
        """)

        self.summary_text = QLabel()

        self.summary_text.setAlignment(Qt.AlignCenter)
        self.summary_text.setWordWrap(True)
        self.summary_text.setMinimumHeight(120)

        self.summary_text.setStyleSheet("""
            font-size: 11pt;
            color: #69739c;
            font-weight: bold;

            padding-top: 12px;
            padding-bottom: 12px;
            padding-left: 8px;
            padding-right: 8px;

            margin: 0px;
        """)

        summary_layout.addWidget(summary_title)
        summary_layout.addWidget(self.summary_text)

        summary.setLayout(summary_layout)

        card_layout.addWidget(summary)

        main_card.setLayout(card_layout)

        main_layout.addWidget(main_card)

        self.setLayout(main_layout)

        # TIMER AUTO UPDATE
        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_comparison
        )

        self.timer.start(200)
    
    # ACTUALIZAR COMPARACION
    def update_comparison(self):

        # TIPOS
        self.left_type.setText(
            self.proc_a.selector.currentText()
        )

        self.right_type.setText(
            self.proc_b.selector.currentText()
        )

        # METRICAS A
        self.metric_labels_a["CPI"].setText(
            self.proc_a.metric_cpi.value_label.text()
        )

        self.metric_labels_a["Ciclos"].setText(
            self.proc_a.metric_cycles.value_label.text()
        )

        self.metric_labels_a["Tiempo"].setText(
            self.proc_a.metric_total.value_label.text()
        )

        self.metric_labels_a["Estado"].setText(
            f"PC {self.proc_a.metric_pc.value_label.text()}"
        )

        # METRICAS B
        self.metric_labels_b["CPI"].setText(
            self.proc_b.metric_cpi.value_label.text()
        )

        self.metric_labels_b["Ciclos"].setText(
            self.proc_b.metric_cycles.value_label.text()
        )

        self.metric_labels_b["Tiempo"].setText(
            self.proc_b.metric_total.value_label.text()
        )

        self.metric_labels_b["Estado"].setText(
            f"PC {self.proc_b.metric_pc.value_label.text()}"
        )

        # COMPARACION FINAL
        cpi_a = float(
            self.proc_a.metric_cpi.value_label.text()
        )

        cpi_b = float(
            self.proc_b.metric_cpi.value_label.text()
        )

        cycles_a = int(
            self.proc_a.metric_cycles.value_label.text()
        )

        cycles_b = int(
            self.proc_b.metric_cycles.value_label.text()
        )

        # GANADOR
        if cpi_a < cpi_b:

            result = (
                "Procesador A obtuvo el menor CPI.\n\n"

                "Esto significa que necesitó menos ciclos "
                "por instrucción para ejecutar el programa.\n\n"

                "El procesador A mostró una mayor eficiencia "
                "promedio durante la ejecución."
            )

        elif cpi_b < cpi_a:

            result = (
                "Procesador B obtuvo el menor CPI.\n\n"

                "Esto significa que necesitó menos ciclos "
                "por instrucción para ejecutar el programa.\n\n"

                "El procesador B mostró una mayor eficiencia "
                "promedio durante la ejecución."
            )

        else:

            result = (
                "Ambos procesadores obtuvieron el mismo CPI.\n\n"

                "Esto indica que el costo promedio "
                "por instrucción fue equivalente.\n\n"

                "Sin embargo, el rendimiento total todavía "
                "puede variar dependiendo de la cantidad "
                "de ciclos y del tiempo de ejecución."
            )

        # CICLOS
        if cycles_a < cycles_b:

            result += (
                "\n\nAdemás, el Procesador A necesitó "
                "menos ciclos totales para finalizar "
                "la ejecución."
            )

        elif cycles_b < cycles_a:

            result += (
                "\n\nAdemás, el Procesador B necesitó "
                "menos ciclos totales para finalizar "
                "la ejecución."
            )

        else:

            result += (
                "\n\nAmbos procesadores utilizaron "
                "la misma cantidad de ciclos."
            )
        self.summary_text.setText(result)
        self.summary_text.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

# MAIN WINDOW
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

        comparison = ComparisonPage(self.proc_a, self.proc_b)
        
        main_tabs.addTab(self.proc_a, "Procesador A")
        main_tabs.addTab(self.proc_b, "Procesador B")
        main_tabs.addTab(comparison, "Comparación")

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
        self.proc_a.comparison_page = comparison
        self.proc_b.comparison_page = comparison
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

# APP
app = QApplication(sys.argv)

font = QFont("Segoe UI", 10)
app.setFont(font)

window = MainWindow()
window.show()

sys.exit(app.exec())