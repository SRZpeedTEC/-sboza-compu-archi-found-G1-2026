from abc import ABC, abstractmethod
from pathlib import Path
import re

from src.assembler.parser import AssemblyValidationError, Parser
from src.processors.processor_snapshot import ProcessorSnapshot
from src.core import Metrics, Decoder, ALU, RegisterBank, Memory, InstructionMemory, ControlUnit
from src.assembler import ControlSignals, Instruction


class ProcessorEngine(ABC):
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

        # Temporary variable to hold the source code for potential debugging or visualization purposes
        self.source_code = Path("programs/test.asm").read_text(encoding="utf-8")


    def load_program(self, source_code : str) -> None:
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
    

    """ Funciones de ayuda para ejecutar instrucciones. Estas funciones encapsulan 
    la logica de cada tipo de instruccion,"""

    def get_register(self, reg_name: str) -> int:
        return self.register_bank.read(reg_name)
    

    def write_register(self, reg_name: str, value: int) -> None:
        self.register_bank.write(reg_name, value)


    def execute_alu(self, operand1: int, operand2: int, control_signal: str) -> int:
        return self.alu.execute(control_signal, operand1, operand2)
    

    def load_from_memory(self, address: int) -> int:
        return self.memory.load_word(address)
    

    def write_in_memory(self, address: int, value: int) -> None:
        self.memory.store_word(address, value)

    def next_pc(self) -> None:
        self.pc += 4


    """ Funciones genericas para ejecutar instrucciones en cualquier procesador """

    def execute_branch(self, instruction: Instruction, control_signal : ControlSignals) -> None:
        rs1 = self.get_register(instruction.rs1)
        print("READING:", instruction.rs1)
        print("VALUE:", rs1)
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

        rs1 = self.get_register(instruction.rs1)
        rs2 = self.get_register(instruction.rs2)
        address = rs1 + instruction.imm
        self.write_in_memory(address, rs2)
        self.next_pc()


    def execute_lw(self, instruction: Instruction) -> None:

        rs1 = self.get_register(instruction.rs1)
        address = rs1 + instruction.imm
        value = self.load_from_memory(address)
        self.write_register(instruction.rd, value)
        self.next_pc()


    def execute_r_type(self, instruction: Instruction, control_signal: ControlSignals) -> None:

        rs1 = self.get_register(instruction.rs1)
        rs2 = self.get_register(instruction.rs2)
        result = self.execute_alu(rs1, rs2, control_signal.alu_control)
        self.write_register(instruction.rd, result)
        self.next_pc()



    def execute_addi(self, instruction: Instruction, control_signal: ControlSignals) -> None:

        print("EXECUTING ADDI")

        print("RD:", instruction.rd)
        print("RS1:", instruction.rs1)
        print("IMM:", instruction.imm)

        rs1 = self.get_register(instruction.rs1)

        print("RS1 VALUE:", rs1)

        imm = instruction.imm

        result = self.execute_alu(
            rs1,
            imm,
            control_signal.alu_control
        )

        print("RESULT:", result)

        self.write_register(
            instruction.rd,
            result
        )

        print(
            "REGISTER AFTER WRITE:",
            self.get_register(instruction.rd)
        )

        self.next_pc()

        print("PC:", self.pc)

    def record_pipeline_state(
        self,
        fetched_instruction,
        if_id,
        id_ex,
        ex_mem,
        mem_wb
    ):

        row = [
            fetched_instruction,
            if_id,
            id_ex,
            ex_mem,
            mem_wb,
        ]

        print("PIPELINE ROW:", row)

        self.pipeline_history.append(row)

    @abstractmethod

    def step(self):
        raise NotImplementedError
    
    def run(self):
        while not self.is_program_finished():
            self.step()
