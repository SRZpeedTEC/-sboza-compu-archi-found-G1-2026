"""
Cada dataclass transporta todo lo que la siguiente etapa necesita: la
instruccion decodificada y las senales de control viajan juntas para que
cada etapa sea independiente y no necesite releer la instruccion original.
"""

from dataclasses import dataclass, field

from src.assembler.instruction import Instruction
from src.assembler.control_signals import ControlSignals


@dataclass
class IF_ID:
    """Registro entre Fetch y Decode.

    Contiene el string crudo de la instruccion y el PC con el que fue
    fetcheada. instruction=None indica stall (NOP).
    """
    instruction: str | None = None   # texto original; None = burbuja/stall
    pc: int = 0                      # PC de la instruccion

    def to_dict(self) -> dict:
        """Vista serializable del registro (para snapshots/tests)."""
        return {"instruction": self.instruction, "pc": self.pc}


@dataclass
class ID_EX:
    """Registro entre Decode y Execute.

    Transporta la instruccion decodificada, las senales de control y los
    valores ya leidos del banco de registros (A = rs1, B = rs2).
    instruction=None indica stall.
    """
    instruction: Instruction | None = None
    control: ControlSignals | None = None
    a: int = 0            # valor de rs1
    b: int = 0            # valor de rs2
    rs1: str | None = None
    rs2: str | None = None
    rd: str | None = None
    imm: int = 0
    pc: int = 0

    def to_dict(self) -> dict:
        """Vista serializable del registro (opcode None en burbuja)."""
        return {
            "opcode": self.instruction.opcode if self.instruction else None,
            "rd": self.rd,
            "rs1": self.rs1,
            "rs2": self.rs2,
            "imm": self.imm,
            "a": self.a,
            "b": self.b,
            "pc": self.pc,
        }


@dataclass
class EX_MEM:
    """Registro entre Execute y Memory.

    Guarda el resultado de la ALU y el valor de rs2 (necesario para SW).
    instruction=None indica stall.
    """
    instruction: Instruction | None = None
    control: ControlSignals | None = None
    alu_result: int = 0
    b: int = 0            # valor de rs2, usado por SW en MEM
    rd: str | None = None
    pc: int = 0

    def to_dict(self) -> dict:
        """Vista serializable del registro (opcode None en burbuja)."""
        return {
            "opcode": self.instruction.opcode if self.instruction else None,
            "alu_result": self.alu_result,
            "b": self.b,
            "rd": self.rd,
            "pc": self.pc,
        }


@dataclass
class MEM_WB:
    """Registro entre Memory y Writeback.

    Transporta el resultado de la ALU (instrucciones aritmeticas) o el dato
    leido de memoria (LW). instruction=None indica stall.
    """
    instruction: Instruction | None = None
    control: ControlSignals | None = None
    alu_result: int = 0
    mem_data: int = 0
    rd: str | None = None
    pc: int = 0

    def to_dict(self) -> dict:
        """Vista serializable del registro (opcode None en burbuja)."""
        return {
            "opcode": self.instruction.opcode if self.instruction else None,
            "alu_result": self.alu_result,
            "mem_data": self.mem_data,
            "rd": self.rd,
            "pc": self.pc,
        }
