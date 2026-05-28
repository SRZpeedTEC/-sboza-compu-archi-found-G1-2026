from dataclasses import replace
from enum import Enum, auto

from src.assembler import ControlSignals
from src.core.latency import MULTICYCLE_LATENCY_PS
from src.processors.processor_engine import ProcessorEngine
from src.processors.processor_snapshot import ProcessorSnapshot


class Stage(Enum):
    FETCH = auto()
    DECODE = auto()
    EXECUTE = auto()
    MEMORY = auto()
    WRITEBACK = auto()


# Ciclos por tipo de instruccion:
#   R-type / ADDI / SW: IF -> ID -> EX -> WB         = 4 ciclos
#   LW:                  IF -> ID -> EX -> MEM -> WB = 5 ciclos
#   BEQ / BNE:           IF -> ID -> EX              = 3 ciclos
class MultiCycleEngine(ProcessorEngine):
    """Procesador multiciclo: cada step avanza exactamente un ciclo.

    La maquina de estados sigue el flujo:
        FETCH -> DECODE -> EXECUTE -> (MEMORY) -> WRITEBACK -> FETCH
    """

    def __init__(self) -> None:
        super().__init__()
        self._init_stage_registers()
        self.processor_snapshot = self.get_snapshot()

    def _init_stage_registers(self) -> None:
        """Inicializa registros internos entre etapas multiciclo."""
        self._stage: Stage = Stage.FETCH
        self._ir: str | None = None       # Instruction Register
        self._old_pc: int = 0             # PC antes de incrementar en FETCH
        self._a: int = 0                  # Valor leido de rs1
        self._b: int = 0                  # Valor leido de rs2
        self._alu_out: int = 0            # Salida de la ALU
        self._mdr: int = 0                # Memory Data Register
        self._instruction = None
        self._control_signal: ControlSignals | None = None
        self._last_completed_stage: str | None = None
        self._branch_taken: bool | None = None

    def step(self) -> bool:
        """Avanza un ciclo de reloj. Retorna False cuando el programa termino."""
        if self._stage == Stage.FETCH and self.is_program_finished():
            return False

        self._last_completed_stage = self._stage.name

        match self._stage:
            case Stage.FETCH:
                self._do_fetch()
            case Stage.DECODE:
                self._do_decode()
            case Stage.EXECUTE:
                self._do_execute()
            case Stage.MEMORY:
                self._do_memory()
            case Stage.WRITEBACK:
                self._do_writeback()

        self.metrics.count_cycle()
        self.processor_snapshot = self.get_snapshot()
        return True

    def run(self) -> None:
        """Ejecuta el programa completo ciclo a ciclo."""
        while self.step():
            pass

    def get_snapshot(self):
        """Recupera estado visible de datapath, registros, memoria y metricas."""
        return ProcessorSnapshot(
            pc=self.pc,
            metrics=self.metrics,
            control_signals=self._get_multicycle_control_signals(),
            registers=self._collect_registers(),
            memory=self._collect_memory(),
            pipeline=self.pipeline_history,
            stage=self._stage.name,
            ir=str(self._ir) if self._ir else None,
            a=self._a,
            b=self._b,
            alu_out=self._alu_out,
            mdr=self._mdr,
            current_instruction=self._instruction,
            multi_cycle_active_stage=self._last_completed_stage,
            multi_cycle_old_pc=self._old_pc,
            multi_cycle_branch_taken=self._branch_taken,
        )

    def _get_multicycle_control_signals(self) -> ControlSignals:
        """Expone senales de control para la etapa recien ejecutada.

        La ejecucion multiciclo activa senales distintas por ciclo. El snapshot
        usa `_last_completed_stage` para que la UI muestre la etapa que acaba de
        producir efectos, no la siguiente etapa ya programada.
        """
        stage = self._last_completed_stage
        opcode = (
            self._instruction.opcode
            if self._instruction is not None
            else None
        )
        base = (
            self._control_signal
            if stage in {"DECODE", "EXECUTE", "MEMORY", "WRITEBACK"}
            and self._control_signal is not None
            else ControlSignals()
        )

        if stage == "FETCH":
            return replace(
                base,
                pc_write=True,
                adr_src="PC",
                ir_write=True,
                alu_src_a="PC",
                alu_src_b="4",
            )

        if stage == "DECODE":
            return replace(
                base,
                pc_write=False,
                adr_src=None,
                ir_write=False,
                alu_src_a=None,
                alu_src_b=None,
            )

        if stage == "EXECUTE":
            return replace(
                base,
                pc_write=(
                    self._branch_taken
                    if opcode in {"beq", "bne"}
                    else False
                ),
                adr_src=None,
                ir_write=False,
                alu_src_a="A",
                alu_src_b=(
                    "B"
                    if opcode in {"add", "sub", "and", "or", "xor", "beq", "bne"}
                    else "imm"
                ),
            )

        if stage == "MEMORY":
            return replace(
                base,
                pc_write=False,
                adr_src="ALUOut",
                ir_write=False,
                alu_src_a=None,
                alu_src_b=None,
            )

        if stage == "WRITEBACK":
            return replace(
                base,
                pc_write=False,
                adr_src=None,
                ir_write=False,
                alu_src_a=None,
                alu_src_b=None,
            )

        return base

    def _do_fetch(self) -> None:
        """IF: lee la instruccion de memoria e incrementa el PC."""
        self._branch_taken = None
        self._old_pc = self.pc
        self._ir = self.instruction_memory.fetch(self.pc)
        self.pc += 4
        self._stage = Stage.DECODE

    def _do_decode(self) -> None:
        """ID: decodifica, genera senales de control y lee registros fuente."""
        self._instruction = self.decoder.decode(self._ir)
        self._control_signal = self.control_unit.generate_control_signals(
            self._instruction
        )
        self.control_signals = self._control_signal

        if self._instruction.rs1 is not None:
            self._a = self.register_bank.read(self._instruction.rs1)
        if self._instruction.rs2 is not None:
            self._b = self.register_bank.read(self._instruction.rs2)

        self._stage = Stage.EXECUTE

    def _do_execute(self) -> None:
        """EX: opera la ALU y decide la siguiente etapa por opcode."""
        opcode = self._instruction.opcode
        cs = self._control_signal

        if opcode in {"add", "sub", "and", "or", "xor"}:
            self._alu_out = self.alu.execute(cs.alu_control, self._a, self._b)
            self._stage = Stage.WRITEBACK

        elif opcode == "addi":
            self._alu_out = self.alu.execute(
                cs.alu_control,
                self._a,
                self._instruction.imm,
            )
            self._stage = Stage.WRITEBACK

        elif opcode in {"lw", "sw"}:
            # Direccion efectiva de memoria: base de rs1 + offset inmediato.
            self._alu_out = self.alu.execute(
                cs.alu_control,
                self._a,
                self._instruction.imm,
            )
            self._stage = Stage.MEMORY

        elif opcode in {"beq", "bne"}:
            result = self.alu.execute(cs.alu_control, self._a, self._b)
            condition_met = (result == 0) if opcode == "beq" else (result != 0)
            self._branch_taken = condition_met
            self._alu_out = result

            if condition_met:
                # El decoder ya resolvio labels a direcciones absolutas.
                self.pc = self._instruction.imm
            # Si no se toma, el PC ya apunta a PC+4 desde FETCH.

            self.metrics.count_instruction()
            self.metrics.add_time(MULTICYCLE_LATENCY_PS.get(opcode, 825))
            self._stage = Stage.FETCH

    def _do_memory(self) -> None:
        """MEM: accede a memoria de datos; lw lee y sw escribe."""
        opcode = self._instruction.opcode

        if opcode == "lw":
            self._mdr = self.memory.load_word(self._alu_out)
            self._stage = Stage.WRITEBACK

        elif opcode == "sw":
            self.memory.store_word(self._alu_out, self._b)
            self.metrics.count_instruction()
            self.metrics.add_time(MULTICYCLE_LATENCY_PS.get(opcode, 1100))
            self._stage = Stage.FETCH

    def _do_writeback(self) -> None:
        """WB: escribe el resultado final en el banco de registros."""
        opcode = self._instruction.opcode

        if opcode == "lw":
            self.register_bank.write(self._instruction.rd, self._mdr)
        else:
            # R-type y ADDI escriben el resultado previamente calculado por ALU.
            self.register_bank.write(self._instruction.rd, self._alu_out)

        self.metrics.count_instruction()
        self.metrics.add_time(MULTICYCLE_LATENCY_PS.get(opcode, 1100))
        self._stage = Stage.FETCH
