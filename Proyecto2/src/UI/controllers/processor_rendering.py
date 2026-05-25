from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import QTableWidgetItem, QTextEdit


class ProcessorRenderingMixin:
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
    
    # ACTUALIZAR DATAPATH
    def update_datapath(self, snapshot):

        active = []

        architecture = self.selector.currentText()

        # UNICICLO
        if architecture == "Procesador Uniciclo":

            if hasattr(self, "single_cycle_datapath_widget"):
                self.single_cycle_datapath_widget.set_snapshot(snapshot)
            self.datapath_widget.set_active_blocks([])
            return

        # MULTICICLO
        elif architecture == "Procesador Multiciclo":

            if hasattr(self, "multi_cycle_datapath_widget"):
                self.multi_cycle_datapath_widget.set_snapshot(snapshot)
            self.datapath_widget.set_active_blocks([])
            return

        # PIPELINE
        else:

            active = []

            # IF
            if (
                getattr(snapshot, "if_id", None) is not None
                and getattr(snapshot.if_id, "instruction", None) is not None
            ):
                active.extend([
                    "pc",
                    "imem"
                ])

            # ID
            if (
                getattr(snapshot, "id_ex", None) is not None
                and getattr(snapshot.id_ex, "instruction", None) is not None
            ):
                active.extend([
                    "control",
                    "registers"
                ])

            # EX
            if (
                getattr(snapshot, "ex_mem", None) is not None
                and getattr(snapshot.ex_mem, "instruction", None) is not None
            ):
                active.append("alu")

            # MEM + WB
            if (
                getattr(snapshot, "mem_wb", None) is not None
                and getattr(snapshot.mem_wb, "instruction", None) is not None
            ):
                active.append("dmem")
                active.append("wb")

            # Stall
            if hasattr(snapshot, "stalled") and snapshot.stalled:
                active.append("alu")

        # SOLO LOS ACTIVOS SE ILUMINAN
        self.datapath_widget.set_active_blocks(active)

    def update_editor_execution_line(self, snapshot):
        if not hasattr(self, "editor"):
            return

        trace = getattr(snapshot, "single_cycle_trace", {}) or {}
        pc = trace.get("pc")
        if pc is None:
            pc = getattr(snapshot, "multi_cycle_old_pc", None)
        line_number = self._source_line_for_pc(pc)

        if line_number is None:
            self.clear_editor_execution_line()
            return

        selection = QTextEdit.ExtraSelection()
        block = self.editor.document().findBlockByNumber(line_number)
        selection.cursor = QTextCursor(block)
        selection.cursor.clearSelection()

        selection.format = QTextCharFormat()
        selection.format.setBackground(QColor("#fff1c7"))
        selection.format.setProperty(
            QTextFormat.FullWidthSelection,
            True
        )

        self.editor.setExtraSelections([selection])
        self.editor.setTextCursor(selection.cursor)
        self.editor.centerCursor()

    def clear_editor_execution_line(self):
        if hasattr(self, "editor"):
            self.editor.setExtraSelections([])

    def _source_line_for_pc(self, pc):
        if pc is None:
            return None

        try:
            instruction_index = int(pc) // 4
        except (TypeError, ValueError):
            return None

        current_index = 0

        for line_number, original_line in enumerate(
            self.editor.toPlainText().splitlines()
        ):
            line = original_line.split("#", 1)[0].strip()

            if not line:
                continue

            if ":" in line:
                _, line = line.split(":", 1)
                line = line.strip()

                if not line:
                    continue

            if current_index == instruction_index:
                return line_number

            current_index += 1

        return None
            
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

            raw_stage = getattr(
                snapshot,
                "multi_cycle_active_stage",
                snapshot.stage
            )
            current_stage = stage_map.get(raw_stage)

            if current_stage:

                instruction_text = self.format_instruction(snapshot.ir)

                text = instruction_text

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
