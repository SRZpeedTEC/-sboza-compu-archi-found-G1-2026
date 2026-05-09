"""
control_unit.py — RISC-V RV32I Control Unit

Decodes an instruction mnemonic and produces the set of control signals
that drive every other module in the datapath.

ControlUnit.decode(mnemonic) returns a ControlSignals dataclass:

  Signal            What it controls
  ──────────────────────────────────────────────────────────────────
  reg_write        Enable write to the register file (rd)
  mem_read         Activate data-memory read (lw)
  mem_write        Activate data-memory write (sw)
  mem_to_reg       Route memory output (not ALU) to rd
  alu_src_b        Second ALU operand is the immediate (not rs2)
  branch           Instruction is a conditional branch (beq, bne)
  jump             Unconditional jump (jal, jalr)
  jump_reg         jalr variant: target = (rs1 + imm) & ~1
  pc_plus4_to_reg  Save PC+4 into rd as the return address
  alu_op           Specific ALU operation to perform

Coverage of the 12 target instructions:
  add, sub         → R-type  | reg_write, ALU_ADD/SUB
  addi             → I-type  | reg_write, alu_src_b, ALU_ADD
  and, or, xor     → R-type  | reg_write, ALU_AND/OR/XOR
  lw               → I-type  | reg_write, mem_read, mem_to_reg, ALU_ADD
  sw               → S-type  | mem_write, ALU_ADD
  beq, bne         → B-type  | branch, ALU_SEQ/SNE
  jal              → J-type  | reg_write, jump, pc_plus4_to_reg
  jalr             → I-type  | reg_write, jump, jump_reg, pc_plus4_to_reg
"""
from dataclasses import dataclass

from src.core.alu import (
    ALU_ADD, ALU_SUB, ALU_AND, ALU_OR, ALU_XOR,
    ALU_SLL, ALU_SRL, ALU_SRA, ALU_SLT, ALU_SLTU, ALU_LUI,
    ALU_SEQ, ALU_SNE, ALU_SLT_B, ALU_SGE_B, ALU_SLTU_B, ALU_SGEU_B,
)
from src.assembler.instruction import INSTRUCTION_SET


@dataclass
class ControlSignals:
    """
    All control signals produced by the control unit for one instruction.

    reg_write     – write ALU/memory result into rd
    mem_read      – read a value from data memory (load)
    mem_write     – write a value to data memory (store)
    mem_to_reg    – route memory output (not ALU output) to the register file
    alu_src_b     – second ALU operand comes from immediate (True) or rs2 (False)
    branch        – this is a conditional branch instruction
    jump          – unconditional jump (jal / jalr)
    jump_reg      – jalr: target = (rs1 + imm) & ~1
    pc_plus4_to_reg – write return address (PC+4) into rd
    alu_op        – which ALU operation to perform
    """
    reg_write:        bool = False
    mem_read:         bool = False
    mem_write:        bool = False
    mem_to_reg:       bool = False
    alu_src_b:        bool = False
    branch:           bool = False
    jump:             bool = False
    jump_reg:         bool = False
    pc_plus4_to_reg:  bool = False
    alu_op:           str  = ALU_ADD


class ControlUnit:
    """
    Decodes a RISC-V mnemonic into a full set of ControlSignals.
    This is the combinational logic block that drives all other units.
    """

    def decode(self, mnemonic: str) -> ControlSignals:
        if mnemonic not in INSTRUCTION_SET:
            raise ValueError(f"Unsupported instruction: '{mnemonic}'")

        fmt, opcode, funct3, funct7 = INSTRUCTION_SET[mnemonic]
        sig = ControlSignals()

        # ------------------------------------------------------------------
        # R-type: register-register operations
        # ------------------------------------------------------------------
        if fmt == "R":
            sig.reg_write = True
            sig.alu_op = self._rtype_op(mnemonic)

        # ------------------------------------------------------------------
        # I-type
        # ------------------------------------------------------------------
        elif fmt == "I":
            if opcode == 0x13:        # arithmetic immediate
                sig.reg_write = True
                sig.alu_src_b = True
                sig.alu_op = self._itype_arith_op(mnemonic)

            elif opcode == 0x03:      # load
                sig.reg_write  = True
                sig.mem_read   = True
                sig.mem_to_reg = True
                sig.alu_src_b  = True
                sig.alu_op     = ALU_ADD  # address = rs1 + imm

            elif opcode == 0x67:      # jalr
                sig.reg_write       = True
                sig.jump            = True
                sig.jump_reg        = True
                sig.alu_src_b       = True
                sig.alu_op          = ALU_ADD  # target = rs1 + imm
                sig.pc_plus4_to_reg = True

        # ------------------------------------------------------------------
        # S-type: stores
        # ------------------------------------------------------------------
        elif fmt == "S":
            sig.mem_write = True
            sig.alu_src_b = True
            sig.alu_op    = ALU_ADD   # address = rs1 + imm

        # ------------------------------------------------------------------
        # B-type: conditional branches
        # ------------------------------------------------------------------
        elif fmt == "B":
            sig.branch = True
            sig.alu_op = self._btype_op(mnemonic)

        # ------------------------------------------------------------------
        # U-type: upper immediates
        # ------------------------------------------------------------------
        elif fmt == "U":
            sig.reg_write = True
            sig.alu_src_b = True
            # lui:   rd = imm << 12  (processor shifts before passing to ALU)
            # auipc: rd = PC + (imm << 12)  (processor adds PC to shifted imm)
            sig.alu_op = ALU_LUI if mnemonic == "lui" else ALU_ADD

        # ------------------------------------------------------------------
        # J-type: jal
        # ------------------------------------------------------------------
        elif fmt == "J":
            sig.reg_write       = True
            sig.jump            = True
            sig.pc_plus4_to_reg = True

        return sig

    # ------------------------------------------------------------------
    # ALU operation selectors
    # ------------------------------------------------------------------
    def _rtype_op(self, mnemonic: str) -> str:
        return {
            "add":  ALU_ADD,  "sub":  ALU_SUB,
            "and":  ALU_AND,  "or":   ALU_OR,
            "xor":  ALU_XOR,  "sll":  ALU_SLL,
            "srl":  ALU_SRL,  "sra":  ALU_SRA,
            "slt":  ALU_SLT,  "sltu": ALU_SLTU,
        }[mnemonic]

    def _itype_arith_op(self, mnemonic: str) -> str:
        return {
            "addi": ALU_ADD,  "andi": ALU_AND,
            "ori":  ALU_OR,   "xori": ALU_XOR,
            "slti": ALU_SLT,
        }[mnemonic]

    def _btype_op(self, mnemonic: str) -> str:
        return {
            "beq":  ALU_SEQ,    "bne":  ALU_SNE,
            "blt":  ALU_SLT_B,  "bge":  ALU_SGE_B,
            "bltu": ALU_SLTU_B, "bgeu": ALU_SGEU_B,
        }[mnemonic]
