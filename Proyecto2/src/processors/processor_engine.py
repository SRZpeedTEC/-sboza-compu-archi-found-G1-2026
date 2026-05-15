from abc import ABC, abstractmethod
from pathlib import Path
from src.assembler.parser import Parser
from src.processors.processor_snapshot import ProcessorSnapshot
from src.core import Metrics, Decoder, ALU, RegisterBank, Memory, InstructionMemory
from src.assembler import ControlSignals, Instruction






class ProcessorEngine(ABC):
    def __init__(self) -> None:

        self.pc = 0
        self.metrics = Metrics()
        self.control_signals = ControlSignals()

        self.parser = Parser()
        self.alu = ALU()

        self.register_bank = RegisterBank()
        self.memory = Memory()
        self.instruction_memory = InstructionMemory()

        # Temporary variable to hold the source code for potential debugging or visualization purposes
        self.source_code = Path("programs/test.asm").read_text(encoding="utf-8")


    def load_program(self, source_code : str):
        instructions, labels  = self.parser.parse_text(source_code)
        self.instruction_memory.load_instructions(instructions)
        self.decoder = Decoder(labels)


    def is_program_finished(self) -> bool:
        try:
            self.instruction_memory.fetch(self.pc)
            return False
        except IndexError:
            return True


    def get_snapshot(self) -> ProcessorSnapshot:
        return ProcessorSnapshot(pc=self.pc, metrics=self.metrics.get_metrics())
    

    @abstractmethod

    def step(self):
        raise NotImplementedError


    def run(self):
        while not self.is_program_finished():
            self.step()

