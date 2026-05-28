import re
from abc import ABC, abstractmethod
from pathlib import Path

from src.assembler import ControlSignals, Instruction
from src.assembler.parser import AssemblyValidationError, Parser
from src.core import ALU, ControlUnit, Decoder, InstructionMemory, Memory, Metrics, RegisterBank
from src.processors.processor_snapshot import ProcessorSnapshot


class ProcessorEngine(ABC):
    """Base comun para los motores de procesador del simulador.

    Mantiene el flujo compartido Parser -> InstructionMemory -> Decoder ->
    ControlUnit y ofrece helpers de ejecucion que usan uniciclo, multiciclo y
    pipeline sin duplicar acceso a registros, memoria o ALU.
    """

    DEFAULT_PROGRAM_PATH = Path("programs/test.asm")

    def __init__(self) -> None:
        self.pc = 0
        self.metrics = Metrics()
        self.control_signals = ControlSignals()

        self.parser = Parser()
        self.alu = ALU()
        self.control_unit = ControlUnit()

        self.register_bank = RegisterBank()
        self.memory = Memory()
        self.instruction_memory = InstructionMemory()
        self.pipeline_history = []
        self.labels = {}
        self.decoder = Decoder()
        self.instruction_line_numbers = {}

        # Programa inicial usado por la UI cuando crea un motor antes de cargar
        # explicitamente el contenido del editor.
        self.source_code = self.DEFAULT_PROGRAM_PATH.read_text(encoding="utf-8")


    def load_program(self, source_code : str) -> None:
        """Valida y carga un programa completo sin alterar estado si falla.

        Primero se ejecuta la validacion con Parser, InstructionMemory y
        Decoder. Solo cuando todo es correcto se reemplazan labels, memoria de
        instrucciones y decoder del motor actual.
        """
        instructions, labels, line_numbers = self.validate_program(source_code)
        self.labels = labels
        self.instruction_memory.load_instructions(instructions)
        self.decoder = Decoder(labels)
        self.instruction_line_numbers = line_numbers


    @classmethod
    def validate_program(
        cls,
        source_code: str
    ) -> tuple[list[str], dict[str, int], dict[int, int]]:
        """Valida el programa completo usando Parser, InstructionMemory y Decoder reales."""
        parser = Parser()

        try:
            instructions, labels, line_numbers = parser.parse_text_with_line_numbers(
                source_code
            )

            # Se usa InstructionMemory para validar la misma entrada que recibiran los motores.
            instruction_memory = InstructionMemory()
            instruction_memory.load_instructions(instructions)

            decoder = Decoder(labels)

            for index, raw_instruction in enumerate(instructions):
                try:
                    decoder.decode(raw_instruction)
                except ValueError as exc:
                    raise cls._build_validation_error(
                        exc,
                        index,
                        raw_instruction,
                        line_numbers
                    ) from exc

            return instructions, labels, line_numbers

        except AssemblyValidationError:
            raise
        except ValueError as exc:
            raise AssemblyValidationError(str(exc)) from exc


    @staticmethod
    def _build_validation_error(
        exc: ValueError,
        instruction_index: int,
        raw_instruction: str,
        line_numbers: dict[int, int]
    ) -> AssemblyValidationError:
        """Convierte errores bajos del decoder en mensajes con linea fuente."""
        description = str(exc)
        token = None
        match = re.search(r"'([^']+)'", description)

        if match:
            token = match.group(1)
        elif raw_instruction:
            token = raw_instruction.split()[0]

        return AssemblyValidationError(
            description=description,
            line_number=line_numbers.get(instruction_index),
            instruction=raw_instruction,
            token=token,
        )


    def is_program_finished(self) -> bool:
        """Indica si el PC ya salio del rango de instrucciones cargadas."""
        try:
            self.instruction_memory.fetch(self.pc)
            return False
        except IndexError:
            return True


    def _collect_registers(self) -> list[int]:
        """Lee los 32 registros x0..x31 en orden. Reutilizable por cualquier motor."""
        return [self.register_bank.read(f"x{i}") for i in range(32)]

    def _collect_memory(self) -> dict[int, int]:
        """Mapea direccion real (index*4) -> valor para toda la memoria de datos."""
        return {index * 4: value for index, value in enumerate(self.memory._memory)}

    def get_snapshot(self) -> ProcessorSnapshot:
        """Construye un snapshot generico para UI y pruebas."""
        return ProcessorSnapshot(
            pc=self.pc,
            metrics=self.metrics,
            control_signals=self.control_signals,
            registers=self._collect_registers(),
            memory=self._collect_memory(),
            pipeline=self.pipeline_history,
            current_instruction=getattr(self, "current_instruction", None),
            single_cycle_trace=getattr(self, "single_cycle_trace", None)
        )
    

    def get_register(self, reg_name: str) -> int:
        """Lee un registro usando la validacion del banco de registros."""
        return self.register_bank.read(reg_name)
    

    def write_register(self, reg_name: str, value: int) -> None:
        """Escribe un registro; x0 conserva su comportamiento interno."""
        self.register_bank.write(reg_name, value)


    def execute_alu(self, operand1: int, operand2: int, control_signal: str) -> int:
        """Ejecuta la operacion seleccionada por la unidad de control."""
        return self.alu.execute(control_signal, operand1, operand2)
    

    def load_from_memory(self, address: int) -> int:
        """Lee memoria de datos validando alineacion y rango."""
        return self.memory.load_word(address)
    

    def write_in_memory(self, address: int, value: int) -> None:
        """Escribe memoria de datos validando alineacion y rango."""
        self.memory.store_word(address, value)

    def next_pc(self) -> None:
        """Avanza el PC a la siguiente palabra de instruccion."""
        self.pc += 4


    def execute_branch(self, instruction: Instruction, control_signal : ControlSignals) -> None:
        """Ejecuta beq/bne con destino absoluto ya resuelto por el Decoder."""
        rs1 = self.get_register(instruction.rs1)
        rs2 = self.get_register(instruction.rs2)
        condition_met = False

        result = self.execute_alu(rs1, rs2, control_signal.alu_control)

        match control_signal.branch_condition:
            case "beq":
                condition_met = (result == 0)
            case "bne":
                condition_met = (result != 0)
        
        if condition_met:
            self.pc = instruction.imm
        else:
            self.next_pc()


    def execute_sw(self, instruction: Instruction) -> None:
        """Ejecuta store word: direccion = rs1 + inmediato, dato = rs2."""

        rs1 = self.get_register(instruction.rs1)
        rs2 = self.get_register(instruction.rs2)
        address = rs1 + instruction.imm
        self.write_in_memory(address, rs2)
        self.next_pc()


    def execute_lw(self, instruction: Instruction) -> None:
        """Ejecuta load word y escribe el dato leido en rd."""

        rs1 = self.get_register(instruction.rs1)
        address = rs1 + instruction.imm
        value = self.load_from_memory(address)
        self.write_register(instruction.rd, value)
        self.next_pc()


    def execute_r_type(self, instruction: Instruction, control_signal: ControlSignals) -> None:
        """Ejecuta instrucciones R-type con dos operandos de registro."""

        rs1 = self.get_register(instruction.rs1)
        rs2 = self.get_register(instruction.rs2)
        result = self.execute_alu(rs1, rs2, control_signal.alu_control)
        self.write_register(instruction.rd, result)
        self.next_pc()



    def execute_addi(self, instruction: Instruction, control_signal: ControlSignals) -> None:
        """Ejecuta addi usando rs1 e inmediato como entradas de la ALU."""

        rs1 = self.get_register(instruction.rs1)
        imm = instruction.imm

        result = self.execute_alu(
            rs1,
            imm,
            control_signal.alu_control
        )

        self.write_register(
            instruction.rd,
            result
        )

        self.next_pc()

    def record_pipeline_state(
        self,
        fetched_instruction,
        if_id,
        id_ex,
        ex_mem,
        mem_wb
    ):
        """Guarda una fila historica de pipeline consumida por la UI.

        Aunque el pipeline no se limpia en esta iteracion, el helper vive en la
        base para que los motores derivados compartan el formato de historial.
        """

        row = [
            fetched_instruction,
            if_id,
            id_ex,
            ex_mem,
            mem_wb,
        ]

        self.pipeline_history.append(row)

    @abstractmethod

    def step(self):
        raise NotImplementedError
    
    def run(self):
        """Ejecuta hasta que el PC salga del programa cargado."""
        while not self.is_program_finished():
            self.step()
