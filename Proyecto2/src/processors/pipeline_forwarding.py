"""Pipeline con unidad de riesgos y adelantamiento.

Las dependencias RAW se resuelven con forwarding desde EX/MEM o MEM/WB cuando
el dato ya esta disponible. El unico stall de datos modelado es load-use:
cuando un lw en EX produce un registro que la instruccion en ID necesita de
inmediato.
"""

from dataclasses import replace

from src.assembler import ControlSignals
from src.core.latency import PIPELINE_LATENCY_PS
from src.pipeline.forwarding_unit import resolve_forwarding
from src.pipeline.hazard_detection import detect_load_use_hazard
from src.pipeline.pipeline_registers import IF_ID, ID_EX, EX_MEM, MEM_WB
from src.pipeline.stages import (
    stage_decode,
    stage_execute,
    stage_fetch,
    stage_memory,
    stage_writeback,
)
from src.processors.processor_engine import ProcessorEngine
from src.processors.processor_snapshot import ProcessorSnapshot

class PipelineForwardingEngine(ProcessorEngine):
    """Cada step() representa un ciclo completo con forwarding en EX."""

    def __init__(self) -> None:
        super().__init__()
        self.load_program(self.source_code)
        self._init_pipeline_registers()
        self.processor_snapshot = self.get_snapshot()

    def _init_pipeline_registers(self) -> None:
        self._if_id: IF_ID = IF_ID()
        self._id_ex: ID_EX = ID_EX()
        self._ex_mem: EX_MEM = EX_MEM()
        self._mem_wb: MEM_WB = MEM_WB()
        self._stalled: bool = False
        self._flushed: bool = False
        self._forward_a: str = "ID/EX"
        self._forward_b: str = "ID/EX"
        self._pc_beyond_end: bool = False

    def is_program_finished(self) -> bool:
        pipeline_empty = (
            self._if_id.instruction is None
            and self._id_ex.instruction is None
            and self._ex_mem.instruction is None
            and self._mem_wb.instruction is None
        )
        return pipeline_empty and self._pc_beyond_end

    def step(self) -> bool:
        if self.is_program_finished():
            return False

        self._stalled = False
        self._flushed = False
        self._forward_a = "ID/EX"
        self._forward_b = "ID/EX"

        # WB escribe al inicio del ciclo, como en PipelineStallEngine.
        stage_writeback(self._mem_wb, self.register_bank)

        next_mem_wb = stage_memory(self._ex_mem, self.memory)

        forwarding = resolve_forwarding(self._id_ex, self._ex_mem, self._mem_wb)
        self._forward_a = forwarding.forward_a
        self._forward_b = forwarding.forward_b
        forwarded_id_ex = replace(self._id_ex, a=forwarding.a, b=forwarding.b)
        next_ex_mem, branch_taken, branch_target = stage_execute(
            forwarded_id_ex, self.alu
        )

        if self._mem_wb.instruction is not None and self._mem_wb.control is not None:
            self.control_signals = self._mem_wb.control
            self.metrics.count_instruction()

        # ---- Control hazard: branch tomado -> flush de IF_ID e ID_EX ----
        if branch_taken:
            self._flushed = True
            self.pc = branch_target
            self._pc_beyond_end = False
            self.metrics.count_cycle()
            self.metrics.add_time(PIPELINE_LATENCY_PS)
            self.record_pipeline_state(
                "-",
                IF_ID(),
                ID_EX(),
                next_ex_mem,
                next_mem_wb,
            )
            self._if_id = IF_ID()
            self._id_ex = ID_EX()
            self._ex_mem = next_ex_mem
            self._mem_wb = next_mem_wb
            self.processor_snapshot = self.get_snapshot()
            return True

        # ---- Load-use hazard: unico stall de datos del modelo con forwarding ----
        if detect_load_use_hazard(self._if_id, self._id_ex, self.decoder):
            self._stalled = True
            self.metrics.count_stall()
            self.metrics.count_cycle()
            self.metrics.add_time(PIPELINE_LATENCY_PS)
            self.record_pipeline_state(
                self._if_id.instruction if self._if_id.instruction else "-",
                self._if_id,
                ID_EX(),   # burbuja
                next_ex_mem,
                next_mem_wb,
            )
            # Congela PC e IF_ID; inserta burbuja en ID_EX
            self._id_ex = ID_EX()
            self._ex_mem = next_ex_mem
            self._mem_wb = next_mem_wb
            self.processor_snapshot = self.get_snapshot()
            return True

        next_id_ex = stage_decode(
            self._if_id, self.register_bank, self.decoder, self.control_unit
        )

        fetched_instruction = None

        try:
            fetched_instruction = self.instruction_memory.fetch(self.pc)

            next_if_id = stage_fetch(
                self.pc,
                self.instruction_memory
            )

            self.pc += 4

        except IndexError:

            next_if_id = IF_ID()
            self._pc_beyond_end = True

        self.metrics.count_cycle()
        self.metrics.add_time(PIPELINE_LATENCY_PS)

        # Guardar estado ACTUAL antes del avance
        self.record_pipeline_state(
            fetched_instruction,
            self._if_id,
            self._id_ex,
            self._ex_mem,
            self._mem_wb
        )

        # Ahora sí avanzar pipeline
        self._if_id = next_if_id
        self._id_ex = next_id_ex
        self._ex_mem = next_ex_mem
        self._mem_wb = next_mem_wb
        self.processor_snapshot = self.get_snapshot()

        return True

    # run() se hereda de ProcessorEngine: con is_program_finished() sobrescrita
    # ("pipeline vacio + PC fuera de rango") drena el pipeline correctamente.

    def get_snapshot(self) -> ProcessorSnapshot:
        return ProcessorSnapshot(
            pc=self.pc,
            metrics=self.metrics,
            control_signals=self.control_signals,
            registers=self._collect_registers(),
            memory=self._collect_memory(),
            pipeline=self.pipeline_history,
            if_id=self._if_id,
            id_ex=self._id_ex,
            ex_mem=self._ex_mem,
            mem_wb=self._mem_wb,
            stalled=self._stalled,
            flushed=self._flushed,
            forward_a=self._forward_a,
            forward_b=self._forward_b,
        )
