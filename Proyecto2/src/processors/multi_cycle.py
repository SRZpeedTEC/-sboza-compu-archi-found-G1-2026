from enum import Enum, auto

from src.processors.processor_engine import ProcessorEngine
from src.processors.processor_snapshot import ProcessorSnapshot
from src.assembler import ControlSignals


class Stage(Enum):
    FETCH = auto()
    DECODE = auto()
    EXECUTE = auto()
    MEMORY = auto()
    WRITEBACK = auto()


# Ciclos por tipo de instruccion:
#   R-type / ADDI / SW  → IF → ID → EX → WB   = 4 ciclos
#   LW                  → IF → ID → EX → MEM → WB = 5 ciclos
#   BEQ / BNE           → IF → ID → EX          = 3 ciclos


class MultiCycleEngine(ProcessorEngine):
    """Procesador multiciclo: cada step() avanza exactamente un ciclo.

    La maquina de estados sigue el flujo:
        FETCH → DECODE → EXECUTE → (MEMORY →) WRITEBACK → FETCH 
    """

    def __init__(self) -> None:
        super().__init__()
        self._init_stage_registers()
        self.processor_snapshot = self.get_snapshot()


    def _init_stage_registers(self) -> None:
        self._stage: Stage = Stage.FETCH
        self._ir: str | None = None       # Instruction Register
        self._old_pc: int = 0             # PC antes de incrementar en FETCH
        self._a: int = 0                  # Valor leido de rs1
        self._b: int = 0                  # Valor leido de rs2
        self._alu_out: int = 0            # Salida de la ALU
        self._mdr: int = 0                # Memory Data Register
        self._instruction = None
        self._control_signal: ControlSignals | None = None


    # Interfaz publica
    def step(self) -> bool:
        #Avanza un ciclo de reloj. Retorna False cuando el programa termino.#
        if self._stage == Stage.FETCH and self.is_program_finished():
            return False

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
        #Ejecuta el programa completo ciclo a ciclo.#
        while self.step():
            pass

    #recuperar datos para el snapshot
    def get_snapshot(self):

        registers = []

        for i in range(32):
            registers.append(
                self.register_bank.read(f"x{i}")
            )

        memory = {}

        for index, value in enumerate(self.memory._memory):

            real_address = index * 4

            memory[real_address] = value

        return ProcessorSnapshot(

            pc=self.pc,

            metrics=self.metrics,

            control_signals=self.control_signals,

            registers=registers,

            memory=memory,

            pipeline=self.pipeline_history,

            stage=self._stage.name,

            ir=str(self._ir) if self._ir else None,

            a=self._a,

            b=self._b,

            alu_out=self._alu_out,

            mdr=self._mdr
        )


    # ------ Etapas de la maquina de estados ----------


    def _do_fetch(self) -> None:
        #IF: lee la instruccion de memoria e incrementa el PC.
        self._old_pc = self.pc
        self._ir = self.instruction_memory.fetch(self.pc)
        self.pc += 4
        self._stage = Stage.DECODE

    def _do_decode(self) -> None:
        #ID: decodifica, genera senales de control y lee registros fuente.
        self._instruction = self.decoder.decode(self._ir)
        self._control_signal = self.control_unit.generate_control_signals(self._instruction)
        self.control_signals = self._control_signal

        if self._instruction.rs1 is not None:
            self._a = self.register_bank.read(self._instruction.rs1)
        if self._instruction.rs2 is not None:
            self._b = self.register_bank.read(self._instruction.rs2)

        self._stage = Stage.EXECUTE

    def _do_execute(self) -> None:
        #EX: opera la ALU; determina la siguiente etapa segun el tipo.
        opcode = self._instruction.opcode
        cs = self._control_signal

        if opcode in {"add", "sub", "and", "or", "xor"}:
            self._alu_out = self.alu.execute(cs.alu_control, self._a, self._b)
            self._stage = Stage.WRITEBACK

        elif opcode == "addi":
            self._alu_out = self.alu.execute(cs.alu_control, self._a, self._instruction.imm)
            self._stage = Stage.WRITEBACK

        elif opcode in {"lw", "sw"}:
            # Calcula la direccion de memoria: base + offset
            self._alu_out = self.alu.execute(cs.alu_control, self._a, self._instruction.imm)
            self._stage = Stage.MEMORY

        elif opcode in {"beq", "bne"}:
            result = self.alu.execute(cs.alu_control, self._a, self._b)
            condition_met = (result == 0) if opcode == "beq" else (result != 0)

            if condition_met:
                # El decoder resuelve labels a direcciones absolutas
                self.pc = self._instruction.imm
            # Si no se toma, pc ya fue incrementado a PC+4 en FETCH

            self.metrics.count_instruction()
            self._stage = Stage.FETCH

    def _do_memory(self) -> None:
        #MEM: accede a memoria de datos (lw lee, sw escribe).
        opcode = self._instruction.opcode

        if opcode == "lw":
            self._mdr = self.memory.load_word(self._alu_out)
            self._stage = Stage.WRITEBACK

        elif opcode == "sw":
            self.memory.store_word(self._alu_out, self._b)
            self.metrics.count_instruction()
            self._stage = Stage.FETCH

    def _do_writeback(self) -> None:
        #WB: escribe el resultado en el banco de registros.
        opcode = self._instruction.opcode

        if opcode == "lw":
            self.register_bank.write(self._instruction.rd, self._mdr)
        else:
            # R-type y ADDI escriben el resultado de la ALU
            self.register_bank.write(self._instruction.rd, self._alu_out)

        self.metrics.count_instruction()
        self._stage = Stage.FETCH
