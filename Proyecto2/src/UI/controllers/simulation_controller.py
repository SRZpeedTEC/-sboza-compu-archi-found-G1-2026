from PySide6.QtWidgets import QApplication, QTableWidgetItem

from src.assembler import AssemblyValidationError
from src.processors.processor_engine import ProcessorEngine
from src.processors import (
    SingleCycleEngine,
    MultiCycleEngine,
    PipelineForwardingEngine,
    PipelineStallEngine,
)


MAX_EXECUTION_CYCLES = 100000
CYCLE_LIMIT_MESSAGE = (
    "Execution stopped because the maximum cycle limit was reached. "
    "The program may contain an infinite loop."
)


class ProcessorSimulationMixin:
    def architecture_changed(self):

        self.reset_execution()
        if hasattr(self, "update_datapath_visibility"):
            self.update_datapath_visibility()

        if hasattr(self, "comparison_page"):
            self.comparison_page.update_comparison()

    def step_execution(self):

        if not self._ensure_program_ready():
            return

        if self.running and self._continuous_cycle_count >= MAX_EXECUTION_CYCLES:
            self._stop_for_cycle_limit()
            return

        try:
            executed = self.engine.step()
        except ValueError as exc:
            self._show_friendly_execution_error(exc)
            return

        if not executed:

            self.timer.stop()
            self.running = False

            if self.hazard_box.count() == 0 or \
                self.hazard_box.item(self.hazard_box.count()-1).text() != "Programa finalizado":
                    self.hazard_box.addItem("Programa finalizado")

            # Registrar ejecucion completa en el historial.
            snapshot = self.engine.get_snapshot()
            self.main_window.add_history(
                self._build_history_entry(snapshot)
            )
            self.clear_editor_execution_line()
            return

        snapshot = self.engine.get_snapshot()
        print("STALL:", getattr(snapshot, "stalled", None))
        print("FLUSH:", getattr(snapshot, "flushed", None))
        print("FA:", getattr(snapshot, "forward_a", None))
        print("FB:", getattr(snapshot, "forward_b", None))
        self.hazard_box.clear()

        # Actualizar pipeline.
        if (
            hasattr(snapshot, "pipeline")
            and snapshot.pipeline
        ):

            self.pipeline_data = snapshot.pipeline
            self.update_pipeline_table()

        self.update_pipeline_state(snapshot)

        # Actualizar metricas.
        self.update_metrics(snapshot)

        # Actualizar registros.
        self.update_registers(snapshot)

        # Actualizar memoria.
        self.update_memory(snapshot)

        self.update_datapath(snapshot)
        self.update_editor_execution_line(snapshot)

        if self.running:
            self._continuous_cycle_count += 1

            if self._continuous_cycle_count >= MAX_EXECUTION_CYCLES:
                self._stop_for_cycle_limit()

    # RUN
    def run_execution(self):

        if not self._ensure_program_ready():
            return

        self.running = True
        self._continuous_cycle_count = 0
        mode = self.main_window.mode.currentText()

        # Ejecutar un ciclo cada 400 ms o correr completo con limite.
        if mode == "Completo":

            limit_reached = False

            while self._continuous_cycle_count < MAX_EXECUTION_CYCLES:
                try:
                    executed = self.engine.step()
                except ValueError as exc:
                    self._show_friendly_execution_error(exc)
                    return

                if not executed:
                    break

                snapshot = self.engine.get_snapshot()
                self._continuous_cycle_count += 1

                if (
                    hasattr(snapshot, "pipeline")
                    and snapshot.pipeline
                ):
                    self.pipeline_data = snapshot.pipeline

                # Mantiene respirando la UI sin usar sleeps bloqueantes.
                if self._continuous_cycle_count % 200 == 0:
                    self.update_editor_execution_line(snapshot)
                    QApplication.processEvents()

                    if not self.running:
                        break

            else:
                limit_reached = True

            snapshot = self.engine.get_snapshot()
            self.update_pipeline_table()
            self.pipeline.setRowCount(len(self.pipeline_data))
            self.update_metrics(snapshot)
            self.update_registers(snapshot)
            self.update_memory(snapshot)

            if limit_reached:
                self._mark_cycle_limit_reached()
                self._add_status_message(CYCLE_LIMIT_MESSAGE)
            else:
                self.hazard_box.addItem(
                    "Ejecucion completa finalizada"
                )

            self.main_window.add_history(
                self._build_history_entry(snapshot)
            )
            self.update_pipeline_state(snapshot)
            self.update_datapath(snapshot)
            if limit_reached:
                self.update_editor_execution_line(snapshot)
            else:
                self.clear_editor_execution_line()

            self.running = False
            QApplication.processEvents()
        else:
            delay = (
                self.main_window.automatic_speed.value()
                if hasattr(self.main_window, "automatic_speed")
                else 400
            )
            self.timer.start(delay)

    # RESET
    def reset_execution(self):

        self.timer.stop()

        self.running = False
        self._continuous_cycle_count = 0

        self.current_cycle = 0

        self.metric_cycles.set_value("0")
        self.metric_instructions.set_value("0")
        self.metric_cpi.set_value("0")
        if hasattr(self, "metric_ipc"):
            self.metric_ipc.set_value("0")
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

        try:
            self.engine.load_program(
                self.editor.toPlainText()
            )
            self.engine.program_loaded = True
        except (AssemblyValidationError, ValueError) as exc:
            self.engine.program_loaded = False
            self._show_friendly_execution_error(exc)

        self.datapath_widget.set_active_blocks([])
        self.clear_editor_execution_line()
        if hasattr(self, "single_cycle_datapath_widget"):
            self.single_cycle_datapath_widget.clear()
        if hasattr(self, "multi_cycle_datapath_widget"):
            self.multi_cycle_datapath_widget.clear()
        if hasattr(self, "pipeline_datapath_widget"):
            self.pipeline_datapath_widget.clear()
        if hasattr(self, "update_datapath_visibility"):
            self.update_datapath_visibility()

    # STOP
    def stop_execution(self):

        self.running = False
        self._continuous_cycle_count = 0
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

                "ipc":
                self.metric_ipc.value_label.text()
                if hasattr(self, "metric_ipc") else "0",

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
        self._continuous_cycle_count = 0
    
    # CARGAR PROGRAMA EN ENGINE
    def load_program_into_engine(self):

        source_code = self.editor.toPlainText()

        self.create_engine()

        self.engine.load_program(source_code)

        self.running = False
        self._continuous_cycle_count = 0

    # VALIDACION Y ERRORES
    def _ensure_program_ready(self) -> bool:
        source_code = self.editor.toPlainText()

        try:
            # Valida antes de crear/cargar motores para no alterar estado si el codigo esta malo.
            ProcessorEngine.validate_program(source_code)
        except (AssemblyValidationError, ValueError) as exc:
            self._show_friendly_execution_error(exc)
            return False

        if self.engine is None:
            self.create_engine()

        if not self.engine.program_loaded:
            try:
                self.engine.load_program(source_code)
                self.engine.program_loaded = True
            except (AssemblyValidationError, ValueError) as exc:
                self._show_friendly_execution_error(exc)
                return False

        return True

    def _show_friendly_execution_error(self, error) -> None:
        self.running = False
        self.timer.stop()
        self._continuous_cycle_count = 0
        self._add_status_message(self._format_execution_error(error))

    def _format_execution_error(self, error) -> str:
        if isinstance(error, AssemblyValidationError):
            details = []

            if error.line_number is not None:
                details.append(f"Linea {error.line_number}")

            if error.instruction:
                details.append(f"Instruccion: {error.instruction}")

            if error.token:
                details.append(f"Token: {error.token}")

            details.append(f"Detalle: {error.description}")
            return "Codigo invalido. " + ". ".join(details)

        return f"No se pudo ejecutar el programa: {error}"

    def _add_status_message(self, message: str) -> None:
        if hasattr(self, "hazard_box"):
            self.hazard_box.clear()
            self.hazard_box.addItem(message)

    def _stop_for_cycle_limit(self) -> None:
        self.running = False
        self.timer.stop()
        self._mark_cycle_limit_reached()
        self._add_status_message(CYCLE_LIMIT_MESSAGE)

    def _mark_cycle_limit_reached(self) -> None:
        if self.engine is not None and hasattr(self.engine.metrics, "stopped_by_cycle_limit"):
            self.engine.metrics.stopped_by_cycle_limit = True

    # CONSTRUIR ENTRADA DE HISTORIAL
    def _build_history_entry(self, snapshot) -> dict:
        """Devuelve un dict con las metricas del snapshot para el historial."""
        from src.core.latency import (
            CLOCK_PERIOD_SINGLE_CYCLE,
            CLOCK_PERIOD_MULTICYCLE,
            CLOCK_PERIOD_PIPELINE,
            fmt_time,
        )

        architecture = self.selector.currentText()

        if architecture == "Procesador Uniciclo":
            clock_ps = CLOCK_PERIOD_SINGLE_CYCLE
        elif architecture == "Procesador Multiciclo":
            clock_ps = CLOCK_PERIOD_MULTICYCLE
        else:
            clock_ps = CLOCK_PERIOD_PIPELINE

        m = snapshot.metrics.get_metrics()
        cycles       = m.get("cycles", 0)
        instructions = m.get("instructions", 0)
        total_ps     = m.get("time_ps", 0)   # suma de rutas criticas acumuladas
        cpi          = round(cycles / instructions, 2) if instructions > 0 else 0
        ipc          = round(m.get("ipc", 0), 2)
        total_time   = fmt_time(total_ps)

        return {
            "processor":    self.processor_name,
            "architecture": architecture,
            "cycles":       cycles,
            "instructions": instructions,
            "cpi":          cpi,
            "ipc":          ipc,
            "total_time":   total_time,
        }
