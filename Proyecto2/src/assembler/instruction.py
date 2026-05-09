"""
instruction.py — Internal representation of RISC-V RV32I instructions

Defines two main things:
  1. INSTRUCTION_SET: lookup table mapping each mnemonic to its format
     (R/I/S/B/U/J), opcode, funct3, and funct7 per the RV32I spec.
  2. Instruction (dataclass): data structure filled by the parser for
     every assembly line. Holds all fields the ALU, control unit, and
     pipeline need to execute the instruction without re-parsing text.

Target instructions for the simulator:
  Arithmetic : add, sub, addi, and, or, xor
  Memory     : lw, sw
  Jumps      : beq, bne, jal, jalr
"""
from dataclasses import dataclass
from typing import Optional

RTYPE = "R"
ITYPE = "I"
STYPE = "S"
BTYPE = "B"
UTYPE = "U"
JTYPE = "J"

# mnemonic -> (format, opcode, funct3, funct7)
INSTRUCTION_SET: dict = {
    # R-type: arithmetic/logic between two registers
    "add":  (RTYPE, 0x33, 0x0, 0x00),
    "sub":  (RTYPE, 0x33, 0x0, 0x20),
    "and":  (RTYPE, 0x33, 0x7, 0x00),
    "or":   (RTYPE, 0x33, 0x6, 0x00),
    "xor":  (RTYPE, 0x33, 0x4, 0x00),
    "sll":  (RTYPE, 0x33, 0x1, 0x00),
    "srl":  (RTYPE, 0x33, 0x5, 0x00),
    "sra":  (RTYPE, 0x33, 0x5, 0x20),
    "slt":  (RTYPE, 0x33, 0x2, 0x00),
    "sltu": (RTYPE, 0x33, 0x3, 0x00),
    # I-type: arithmetic with immediate
    "addi": (ITYPE, 0x13, 0x0, None),
    "andi": (ITYPE, 0x13, 0x7, None),
    "ori":  (ITYPE, 0x13, 0x6, None),
    "xori": (ITYPE, 0x13, 0x4, None),
    "slti": (ITYPE, 0x13, 0x2, None),
    # I-type: loads
    "lw":   (ITYPE, 0x03, 0x2, None),
    "lh":   (ITYPE, 0x03, 0x1, None),
    "lb":   (ITYPE, 0x03, 0x0, None),
    "lbu":  (ITYPE, 0x03, 0x4, None),
    "lhu":  (ITYPE, 0x03, 0x5, None),
    # I-type: jump-and-link register
    "jalr": (ITYPE, 0x67, 0x0, None),
    # S-type: stores
    "sw":   (STYPE, 0x23, 0x2, None),
    "sh":   (STYPE, 0x23, 0x1, None),
    "sb":   (STYPE, 0x23, 0x0, None),
    # B-type: conditional branches
    "beq":  (BTYPE, 0x63, 0x0, None),
    "bne":  (BTYPE, 0x63, 0x1, None),
    "blt":  (BTYPE, 0x63, 0x4, None),
    "bge":  (BTYPE, 0x63, 0x5, None),
    "bltu": (BTYPE, 0x63, 0x6, None),
    "bgeu": (BTYPE, 0x63, 0x7, None),
    # U-type: upper immediate
    "lui":   (UTYPE, 0x37, None, None),
    "auipc": (UTYPE, 0x17, None, None),
    # J-type: jump-and-link
    "jal":  (JTYPE, 0x6F, None, None),
}


@dataclass
class Instruction:
    mnemonic: str
    fmt: str                      # R / I / S / B / U / J
    opcode: int
    funct3: Optional[int]
    funct7: Optional[int]
    rd:  Optional[int] = None     # destination register index (0-31)
    rs1: Optional[int] = None     # source register 1 index
    rs2: Optional[int] = None     # source register 2 index
    imm: Optional[int] = None     # sign-extended immediate value
    label: Optional[str] = None   # label defined at this instruction's address
    raw: str = ""                 # original assembly line (for display)
    pc: int = 0                   # byte address of this instruction

    def __str__(self) -> str:
        return f"[PC={self.pc:#06x}] {self.raw.strip() or self.mnemonic}"
