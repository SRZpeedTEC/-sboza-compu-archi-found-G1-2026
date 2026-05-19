"""Pipeline con unidad de riesgos y adelantamiento.

Las dependencias RAW se resuelven con forwarding desde EX/MEM o MEM/WB cuando
el dato ya esta disponible. El unico stall de datos modelado es load-use:
cuando un lw en EX produce un registro que la instruccion en ID necesita de
inmediato.
"""

from dataclasses import replace

from src.assembler import ControlSignals
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


class PipelineForwardingSnapshot(ProcessorSnapshot):
    """Snapshot del pipeline con forwarding."""

    def __init__(
        self,
        pc: int,
        metrics,
        control_signals: ControlSignals,
        if_id: IF_ID,
        id_ex: ID_EX,
        ex_mem: EX_MEM,
        mem_wb: MEM_WB,
        stalled: bool,
        flushed: bool,
        forward_a: str,
        forward_b: str,
    ) -> None:
        super().__init__(pc=pc, metrics=metrics, control_signals=control_signals)
        self.if_id = if_id
        self.id_ex = id_ex
        self.ex_mem = ex_mem
        self.mem_wb = mem_wb
        self.stalled = stalled
        self.flushed = flushed
        self.forward_a = forward_a
        self.forward_b = forward_b

    def get_snapshot(self) -> dict:
        base = super().get_snapshot()

        def _opcode(reg) -> str | None:
            return reg.instruction.opcode if reg.instruction else None

        base["if_id"] = {
            "instruction": self.if_id.instruction,
            "pc": self.if_id.pc,
        }
        base["id_ex"] = {
            "opcode": _opcode(self.id_ex),
            "rd": self.id_ex.rd,
            "rs1": self.id_ex.rs1,
            "rs2": self.id_ex.rs2,
            "a": self.id_ex.a,
            "b": self.id_ex.b,
            "imm": self.id_ex.imm,
        }
        base["ex_mem"] = {
            "opcode": _opcode(self.ex_mem),
            "rd": self.ex_mem.rd,
            "alu_result": self.ex_mem.alu_result,
            "b": self.ex_mem.b,
        }
        base["mem_wb"] = {
            "opcode": _opcode(self.mem_wb),
            "rd": self.mem_wb.rd,
            "alu_result": self.mem_wb.alu_result,
            "mem_data": self.mem_wb.mem_data,
        }
        base["stalled"] = self.stalled
        base["flushed"] = self.flushed
        base["forward_a"] = self.forward_a
        base["forward_b"] = self.forward_b
        return base


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

        if branch_taken:
            self._flushed = True
            self.pc = branch_target
            self._pc_beyond_end = False
            self.metrics.count_cycle()
            self._if_id = IF_ID()
            self._id_ex = ID_EX()
            self._ex_mem = next_ex_mem
            self._mem_wb = next_mem_wb
            self.processor_snapshot = self.get_snapshot()
            return True

        if detect_load_use_hazard(self._if_id, self._id_ex, self.decoder):
            self._stalled = True
            self.metrics.count_stall()
            self.metrics.count_cycle()
            self._id_ex = ID_EX()
            self._ex_mem = next_ex_mem
            self._mem_wb = next_mem_wb
            self.processor_snapshot = self.get_snapshot()
            return True

        next_id_ex = stage_decode(
            self._if_id, self.register_bank, self.decoder, self.control_unit
        )

        try:
            self.instruction_memory.fetch(self.pc)
            next_if_id = stage_fetch(self.pc, self.instruction_memory)
            self.pc += 4
        except IndexError:
            next_if_id = IF_ID()
            self._pc_beyond_end = True

        self.metrics.count_cycle()
        self._if_id = next_if_id
        self._id_ex = next_id_ex
        self._ex_mem = next_ex_mem
        self._mem_wb = next_mem_wb
        self.processor_snapshot = self.get_snapshot()
        return True

    def run(self) -> None:
        while self.step():
            pass

    def get_snapshot(self) -> PipelineForwardingSnapshot:
        return PipelineForwardingSnapshot(
            pc=self.pc,
            metrics=self.metrics,
            control_signals=self.control_signals,
            if_id=self._if_id,
            id_ex=self._id_ex,
            ex_mem=self._ex_mem,
            mem_wb=self._mem_wb,
            stalled=self._stalled,
            flushed=self._flushed,
            forward_a=self._forward_a,
            forward_b=self._forward_b,
        )
