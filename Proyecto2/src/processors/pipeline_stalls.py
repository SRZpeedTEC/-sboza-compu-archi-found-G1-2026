"""Pipeline que resuelve hazards RAW insertando stalls.

Toda dependencia RAW se resuelve congelando el PC y el registro IF/ID e insertando una burbuja (stall) en
ID/EX hasta que la instruccion productora complete WB.

Penalizacion de control (branch tomado): 2 ciclos (flush de IF_ID e ID_EX).
"""

from src.core.latency import PIPELINE_LATENCY_PS
from src.pipeline.hazard_detection import detect_data_hazard
from src.pipeline.pipeline_registers import EX_MEM, ID_EX, IF_ID, MEM_WB
from src.pipeline.stages import (
    stage_decode,
    stage_execute,
    stage_fetch,
    stage_memory,
    stage_writeback,
)
from src.processors.processor_engine import ProcessorEngine
from src.processors.processor_snapshot import ProcessorSnapshot


class PipelineStallEngine(ProcessorEngine):
    """Cada step representa un ciclo; todas las etapas avanzan en paralelo."""

    def __init__(self) -> None:
        super().__init__()
        self.load_program(self.source_code)
        self._init_pipeline_registers()
        self.processor_snapshot = self.get_snapshot()


    def _init_pipeline_registers(self) -> None:
        """Inicializa los registros entre etapas y banderas visibles para la UI."""
        self._if_id: IF_ID = IF_ID()
        self._id_ex: ID_EX = ID_EX()
        self._ex_mem: EX_MEM = EX_MEM()
        self._mem_wb: MEM_WB = MEM_WB()
        self._stalled: bool = False
        self._flushed: bool = False
        self._pc_beyond_end: bool = False

    def is_program_finished(self) -> bool:
        """El programa termina cuando el pipeline esta vacio y ya no hay
        instrucciones que fetchear."""
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

        # WB escribe al inicio del ciclo para que ID pueda leer valores recien
        # confirmados sin necesitar un stall adicional por MEM/WB.
        stage_writeback(self._mem_wb, self.register_bank)

        # MEM consume EX/MEM actual y prepara el registro MEM/WB siguiente.
        next_mem_wb = stage_memory(self._ex_mem, self.memory)

        # EX opera la ALU y puede decidir un branch tomado.
        next_ex_mem, branch_taken, branch_target = stage_execute(
            self._id_ex, self.alu
        )

        # Una instruccion cuenta como completada solo cuando llega a WB.
        if self._mem_wb.instruction is not None and self._mem_wb.control is not None:
            self.control_signals = self._mem_wb.control
            self.metrics.count_instruction()

        # Branch tomado: las instrucciones especulativas en IF/ID e ID/EX se
        # reemplazan por burbujas y el PC salta al destino absoluto.
        if branch_taken:
            self._flushed = True
            next_if_id = IF_ID()
            next_id_ex = ID_EX()
            self.pc = branch_target
            self._pc_beyond_end = False
            self.metrics.count_cycle()
            self.metrics.add_time(PIPELINE_LATENCY_PS)
            self.record_pipeline_state(
                "-",
                IF_ID(),
                ID_EX(),
                next_ex_mem,
                next_mem_wb
            )
            self._if_id = next_if_id
            self._id_ex = next_id_ex
            self._ex_mem = next_ex_mem
            self._mem_wb = next_mem_wb
            self.processor_snapshot = self.get_snapshot()
            return True

        # Data hazard: se compara la instruccion en ID contra productores en EX
        # y MEM. Como este motor no tiene forwarding, cualquier RAW pendiente
        # congela IF/ID y mete una burbuja a ID/EX.
        stall = detect_data_hazard(
            self._if_id,
            self._id_ex,
            self._ex_mem,
            self.decoder
        )

        if stall:
            self._stalled = True
            self.metrics.count_stall()
            self.metrics.count_cycle()
            self.metrics.add_time(PIPELINE_LATENCY_PS)
            self.record_pipeline_state(
                self._if_id.instruction if self._if_id.instruction else "-",
                self._if_id,
                ID_EX(),   # burbuja
                next_ex_mem,
                next_mem_wb
            )
            self._id_ex = ID_EX()
            self._ex_mem = next_ex_mem
            self._mem_wb = next_mem_wb
            self.processor_snapshot = self.get_snapshot()
            return True

        # Sin hazards: ID decodifica la instruccion anterior y IF trae la
        # siguiente instruccion si el PC aun esta dentro del programa.
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
        self.metrics.add_time(PIPELINE_LATENCY_PS)
        self.record_pipeline_state(
            next_if_id.instruction if next_if_id.instruction else "-",
            self._if_id,
            self._id_ex,
            self._ex_mem,
            self._mem_wb
        )
        self._if_id = next_if_id
        self._id_ex = next_id_ex
        self._ex_mem = next_ex_mem
        self._mem_wb = next_mem_wb
        self.processor_snapshot = self.get_snapshot()
        return True

    def get_snapshot(self) -> ProcessorSnapshot:
        """Entrega estado de pipeline, metricas y registros para UI/pruebas."""
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
            flushed=self._flushed
        )
