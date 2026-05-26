from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import *

from src.UI.datapaths.multi_cycle_datapath_view import MultiCycleDatapathView
from src.UI.datapaths.pipeline_datapath_view import PipelineDatapathView
from src.UI.datapaths.single_cycle_datapath_view import SingleCycleDatapathView


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

        # BOTONES GLOBALES DE COMPARACION
        compare_buttons = QHBoxLayout()

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

        compare_buttons.addWidget(self.step_btn)
        compare_buttons.addWidget(self.run_btn)
        compare_buttons.addWidget(self.reset_btn)
        compare_buttons.addWidget(self.stop_btn)

        card_layout.addLayout(compare_buttons)

        # CONEXIONES
        self.step_btn.clicked.connect(
            self.step_both
        )

        self.run_btn.clicked.connect(
            self.run_both
        )

        self.reset_btn.clicked.connect(
            self.reset_both
        )

        self.stop_btn.clicked.connect(
            self.stop_both
        )

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

        self.pipeline_visual_a = PipelineDatapathView("#ff5ca8", min_scale=0.34, min_height=250)
        self.single_cycle_visual_a = SingleCycleDatapathView("#ff5ca8", min_scale=0.42, min_height=220)
        self.multi_cycle_visual_a = MultiCycleDatapathView("#ff5ca8", min_scale=0.34, min_height=260)

        self.pipeline_visual_a.setMinimumHeight(250)
        self.single_cycle_visual_a.setMinimumHeight(220)
        self.multi_cycle_visual_a.setMinimumHeight(260)

        datapath_layout_a.addWidget(datapath_title_a)
        datapath_layout_a.addWidget(self.pipeline_visual_a)
        datapath_layout_a.addWidget(self.single_cycle_visual_a)
        datapath_layout_a.addWidget(self.multi_cycle_visual_a)

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

        # ARMAR HAZARDS A
        hazards_a = QFrame()

        hazards_a.setStyleSheet("""
            background-color: white;
            border-radius: 22px;
            border: 2px solid #ffe4f0;
        """)

        hazards_layout_a = QVBoxLayout()
        hazards_layout_a.setContentsMargins(14, 12, 14, 12)
        hazards_layout_a.setSpacing(6)

        hazards_title_a = QLabel("Hazards Detectados")
        hazards_title_a.setAlignment(Qt.AlignCenter)

        hazards_title_a.setStyleSheet("""
            font-size: 11pt;
            font-weight: bold;
            color: #ff5ca8;

            padding: 0px;
            margin: 0px;

            min-height: 18px;
            max-height: 18px;
        """)

        self.hazard_compare_a = QListWidget()

        self.hazard_compare_a.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        self.hazard_compare_a.setFocusPolicy(Qt.NoFocus)

        self.hazard_compare_a.setMaximumHeight(85)

        hazards_layout_a.addWidget(hazards_title_a)
        hazards_layout_a.addWidget(self.hazard_compare_a)

        hazards_a.setLayout(hazards_layout_a)

        hazards_a.setMaximumHeight(140)
        hazards_a.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )

        # ARMAR
        left_layout.addWidget(left_header)
        left_layout.addWidget(datapath_a)
        left_layout.addWidget(metrics_a)
        left_layout.addWidget(hazards_a)

        left_card.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Maximum
        )

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

        self.pipeline_visual_b = PipelineDatapathView("#25bdb0", min_scale=0.34, min_height=250)
        self.single_cycle_visual_b = SingleCycleDatapathView("#25bdb0", min_scale=0.42, min_height=220)
        self.multi_cycle_visual_b = MultiCycleDatapathView("#25bdb0", min_scale=0.34, min_height=260)

        self.pipeline_visual_b.setMinimumHeight(250)
        self.single_cycle_visual_b.setMinimumHeight(220)
        self.multi_cycle_visual_b.setMinimumHeight(260)

        datapath_layout_b.addWidget(datapath_title_b)
        datapath_layout_b.addWidget(self.pipeline_visual_b)
        datapath_layout_b.addWidget(self.single_cycle_visual_b)
        datapath_layout_b.addWidget(self.multi_cycle_visual_b)

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

        # ARMAR HAZARDS B
        hazards_b = QFrame()

        hazards_b.setStyleSheet("""
            background-color: white;
            border-radius: 22px;
            border: 2px solid #dff5f2;
        """)

        hazards_layout_b = QVBoxLayout()
        hazards_layout_b.setContentsMargins(14, 12, 14, 12)
        hazards_layout_b.setSpacing(6)

        hazards_title_b = QLabel("Hazards Detectados")
        hazards_title_b.setAlignment(Qt.AlignCenter)

        hazards_title_b.setStyleSheet("""
            font-size: 11pt;
            font-weight: bold;
            color: #25bdb0;

            padding: 0px;
            margin: 0px;

            min-height: 18px;
            max-height: 18px;
        """)

        self.hazard_compare_b = QListWidget()

        self.hazard_compare_b.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        self.hazard_compare_b.setFocusPolicy(Qt.NoFocus)

        self.hazard_compare_b.setMaximumHeight(85)

        hazards_layout_b.addWidget(hazards_title_b)
        hazards_layout_b.addWidget(self.hazard_compare_b)

        hazards_b.setLayout(hazards_layout_b)

        hazards_b.setMaximumHeight(140)
        hazards_b.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )

        # ARMAR
        right_layout.addWidget(right_header)
        right_layout.addWidget(datapath_b)
        right_layout.addWidget(metrics_b)
        right_layout.addWidget(hazards_b)

        right_card.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Maximum
        )

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
        self.update_comparison()
    
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

        self._update_datapath_preview(
            self.proc_a,
            self.pipeline_visual_a,
            self.single_cycle_visual_a,
            self.multi_cycle_visual_a
        )

        self._update_datapath_preview(
            self.proc_b,
            self.pipeline_visual_b,
            self.single_cycle_visual_b,
            self.multi_cycle_visual_b
        )

        # COPIAR HAZARDS
        self.hazard_compare_a.clear()

        for i in range(self.proc_a.hazard_box.count()):

            text = self.proc_a.hazard_box.item(i).text()

            self.hazard_compare_a.addItem(text)

        self.hazard_compare_b.clear()

        for i in range(self.proc_b.hazard_box.count()):

            text = self.proc_b.hazard_box.item(i).text()

            self.hazard_compare_b.addItem(text)

    # STEP AMBOS
    def step_both(self):

        if self.proc_a.editor.toPlainText().strip():
            self.proc_a.step_execution()

        if self.proc_b.editor.toPlainText().strip():
            self.proc_b.step_execution()

    # RUN AMBOS
    def run_both(self):

        if self.proc_a.editor.toPlainText().strip():
            self.proc_a.run_execution()

        if self.proc_b.editor.toPlainText().strip():
            self.proc_b.run_execution()

    # RESET AMBOS
    def reset_both(self):

        self.proc_a.reset_execution()
        self.proc_b.reset_execution()

    # STOP AMBOS
    def stop_both(self):

        self.proc_a.stop_execution()
        self.proc_b.stop_execution()

    def _update_datapath_preview(
        self,
        processor,
        pipeline_view,
        single_cycle_view,
        multi_cycle_view
    ):
        architecture = processor.selector.currentText()
        snapshot = (
            processor.engine.get_snapshot()
            if processor.engine is not None
            else None
        )

        is_single_cycle = architecture == "Procesador Uniciclo"
        is_multi_cycle = architecture == "Procesador Multiciclo"

        pipeline_view.setVisible(not is_single_cycle and not is_multi_cycle)
        single_cycle_view.setVisible(is_single_cycle)
        multi_cycle_view.setVisible(is_multi_cycle)

        if is_single_cycle:
            single_cycle_view.set_snapshot(snapshot)
        elif is_multi_cycle:
            multi_cycle_view.set_snapshot(snapshot)
        else:
            pipeline_view.set_snapshot(snapshot)
