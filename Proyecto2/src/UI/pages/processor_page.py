from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import *

from src.UI.controllers.processor_rendering import ProcessorRenderingMixin
from src.UI.controllers.simulation_controller import ProcessorSimulationMixin
from src.UI.datapaths.multi_cycle_datapath_view import MultiCycleDatapathView
from src.UI.datapaths.pipeline_datapath_view import PipelineDatapathView
from src.UI.datapaths.single_cycle_datapath_view import SingleCycleDatapathView
from src.UI.widgets.datapath_view import DatapathWidget
from src.UI.widgets.fsm_widget import MultiCycleFSMWidget
from src.UI.widgets.metric_card import MetricCard


class ProcessorPage(ProcessorSimulationMixin, ProcessorRenderingMixin, QWidget):

    def __init__(self, name, accent):
        super().__init__()
        self.current_cycle = 0
        self.running = False
        self._continuous_cycle_count = 0
        self.execution_finalized = False
        self.history_saved_for_current_run = False
        self._loaded_source_code = None
        self._hazard_history = []
        self._hazard_keys = set()
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

        # Panel derecho: pipeline (pág 0) ó FSM multiciclo (pág 1)
        pipeline_widget = QWidget()
        pipeline_widget.setLayout(pipeline_container)

        self.fsm_widget = MultiCycleFSMWidget()

        self.right_stacked = QStackedWidget()
        self.right_stacked.addWidget(pipeline_widget)   # índice 0
        self.right_stacked.addWidget(self.fsm_widget)   # índice 1
        self.right_stacked.setMinimumWidth(720)
        self.right_stacked.setMaximumWidth(720)

        top_split.addWidget(self.right_stacked)

        # DATAPATH
        circuit_title = QLabel("Datapath")
        circuit_title.setObjectName("sectionTitle")

        circuit_frame = QFrame()

        circuit_frame.setMinimumHeight(520)

        # BORDE
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

        # LAYOUT INTERNO
        circuit_layout = QVBoxLayout()

        circuit_layout.setContentsMargins(20, 20, 20, 20)

        # WIDGET VISUAL
        self.datapath_widget = DatapathWidget(accent)
        self.single_cycle_datapath_widget = SingleCycleDatapathView(accent)
        self.multi_cycle_datapath_widget = MultiCycleDatapathView(accent)
        self.pipeline_datapath_widget = PipelineDatapathView(accent)

        circuit_layout.addWidget(self.datapath_widget)
        circuit_layout.addWidget(self.single_cycle_datapath_widget)
        circuit_layout.addWidget(self.multi_cycle_datapath_widget)
        circuit_layout.addWidget(self.pipeline_datapath_widget)

        circuit_frame.setLayout(circuit_layout)

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

        self.metric_ipc = MetricCard(
            "IPC",
            "0",
            "#f0ecff"
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
        metrics_layout.addWidget(self.metric_ipc)
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
        self._reset_hazard_history()

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
        self.update_datapath_visibility()

    # CAMBIO DE ARQUITECTURA
    def update_datapath_visibility(self):
        architecture = self.selector.currentText()

        is_single_cycle = architecture == "Procesador Uniciclo"
        is_multi_cycle = architecture == "Procesador Multiciclo"
        is_pipeline = architecture in (
            "Pipeline con Forwarding",
            "Pipeline con Stalls",
        )

        # Exactamente uno visible a la vez. El DatapathWidget viejo queda
        # oculto (se conserva porque la pagina de comparacion lo consulta).
        self.single_cycle_datapath_widget.setVisible(is_single_cycle)
        self.multi_cycle_datapath_widget.setVisible(is_multi_cycle)
        self.pipeline_datapath_widget.setVisible(is_pipeline)
        self.datapath_widget.setVisible(False)

        # Panel derecho: FSM para multiciclo, tabla pipeline para el resto
        if hasattr(self, "right_stacked"):
            self.right_stacked.setCurrentIndex(1 if is_multi_cycle else 0)
            if is_multi_cycle:
                self.fsm_widget.clear()
