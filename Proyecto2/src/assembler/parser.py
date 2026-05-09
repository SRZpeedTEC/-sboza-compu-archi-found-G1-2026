"""
parser.py — Parser de ensamblador RISC-V de dos pasadas

Convierte un programa en texto plano (sintaxis RISC-V estándar) en
una lista de objetos Instruction listos para ser ejecutados.

Pasada 1 — recopila etiquetas:
  Recorre las líneas contando direcciones (PC += 4 por instrucción)
  y registra cada «etiqueta:» en el LabelTable.

Pasada 2 — decodifica instrucciones:
  Por cada línea activa extrae el mnemónico y los operandos, resuelve
  los registros (por nombre ABI o xN), los inmediatos y convierte las
  referencias a etiquetas en offsets PC-relativos (beq, bne, jal).

Formatos soportados:
  R  →  add  rd, rs1, rs2
  I  →  addi rd, rs1, imm   |  lw rd, imm(rs1)  |  jalr rd, imm(rs1)
  S  →  sw   rs2, imm(rs1)
  B  →  beq  rs1, rs2, label
  U  →  lui  rd, imm
  J  →  jal  rd, label

Comentarios de línea: # o //  (se eliminan antes de procesar).
"""
import re
from typing import List

from src.assembler.instruction import Instruction, INSTRUCTION_SET
from src.assembler.labels import LabelTable

# ABI name -> register index
ABI_NAMES: dict[str, int] = {
    "zero": 0,  "ra": 1,   "sp": 2,   "gp": 3,   "tp": 4,
    "t0": 5,    "t1": 6,   "t2": 7,
    "s0": 8,    "fp": 8,   "s1": 9,
    "a0": 10,   "a1": 11,  "a2": 12,  "a3": 13,
    "a4": 14,   "a5": 15,  "a6": 16,  "a7": 17,
    "s2": 18,   "s3": 19,  "s4": 20,  "s5": 21,
    "s6": 22,   "s7": 23,  "s8": 24,  "s9": 25,
    "s10": 26,  "s11": 27,
    "t3": 28,   "t4": 29,  "t5": 30,  "t6": 31,
}

_LABEL_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_OFFSET_RE = re.compile(r'^(-?\d+|0x[0-9a-fA-F]+)\((\w+)\)$')


def _parse_register(token: str) -> int:
    token = token.strip().lower()
    if token in ABI_NAMES:
        return ABI_NAMES[token]
    if token.startswith("x"):
        try:
            idx = int(token[1:])
            if 0 <= idx <= 31:
                return idx
        except ValueError:
            pass
    raise ValueError(f"Unknown register: '{token}'")


def _parse_imm(token: str) -> int:
    token = token.strip()
    if token.startswith("0x") or token.startswith("0X"):
        return int(token, 16)
    return int(token)


def _parse_offset(token: str):
    """Parse 'imm(rs1)' -> (imm: int, rs1_idx: int)."""
    m = _OFFSET_RE.match(token.strip())
    if not m:
        raise ValueError(f"Invalid offset syntax: '{token}'")
    return _parse_imm(m.group(1)), _parse_register(m.group(2))


def _strip_comment(line: str) -> str:
    for marker in ("#", "//"):
        idx = line.find(marker)
        if idx != -1:
            line = line[:idx]
    return line.strip()


class Parser:
    """
    Two-pass RISC-V assembly parser.

    Pass 1: collect all label -> address mappings.
    Pass 2: decode each instruction and resolve label references.
    """

    def __init__(self):
        self.labels = LabelTable()

    def parse(self, source: str) -> List[Instruction]:
        self.labels.clear()
        lines = [_strip_comment(ln) for ln in source.splitlines()]
        self._first_pass(lines)
        return self._second_pass(lines)

    # ------------------------------------------------------------------
    # Pass 1: build the label table
    # ------------------------------------------------------------------
    def _first_pass(self, lines: List[str]) -> None:
        pc = 0
        for line in lines:
            if not line:
                continue
            if ":" in line:
                label_part, _, rest = line.partition(":")
                label = label_part.strip()
                if _LABEL_RE.match(label):
                    self.labels.add(label, pc)
                    line = rest.strip()
            if line and line.split()[0].lower() in INSTRUCTION_SET:
                pc += 4

    # ------------------------------------------------------------------
    # Pass 2: build Instruction objects
    # ------------------------------------------------------------------
    def _second_pass(self, lines: List[str]) -> List[Instruction]:
        instructions: List[Instruction] = []
        pc = 0
        for raw in lines:
            line = raw
            label_here = None
            if ":" in line:
                label_part, _, rest = line.partition(":")
                candidate = label_part.strip()
                if _LABEL_RE.match(candidate):
                    label_here = candidate
                    line = rest.strip()
            if not line:
                continue
            mnemonic = line.split()[0].lower()
            if mnemonic not in INSTRUCTION_SET:
                continue
            instr = self._decode(line, pc, label_here)
            instr.raw = raw
            instructions.append(instr)
            pc += 4
        return instructions

    # ------------------------------------------------------------------
    # Decode a single assembly line into an Instruction
    # ------------------------------------------------------------------
    def _decode(self, line: str, pc: int, label: str = None) -> Instruction:
        parts = line.split(None, 1)
        mnemonic = parts[0].lower()
        operand_str = parts[1].strip() if len(parts) > 1 else ""

        if mnemonic not in INSTRUCTION_SET:
            raise ValueError(f"Unknown mnemonic: '{mnemonic}'")

        fmt, opcode, funct3, funct7 = INSTRUCTION_SET[mnemonic]
        instr = Instruction(
            mnemonic=mnemonic,
            fmt=fmt,
            opcode=opcode,
            funct3=funct3,
            funct7=funct7,
            label=label,
            pc=pc,
        )

        ops = [o.strip() for o in operand_str.split(",")]

        if fmt == "R":
            # add rd, rs1, rs2
            instr.rd  = _parse_register(ops[0])
            instr.rs1 = _parse_register(ops[1])
            instr.rs2 = _parse_register(ops[2])

        elif fmt == "I":
            if opcode == 0x03:
                # lw rd, imm(rs1)
                instr.rd = _parse_register(ops[0])
                instr.imm, instr.rs1 = _parse_offset(ops[1])
            elif opcode == 0x67:
                # jalr rd, rs1, imm  OR  jalr rd, imm(rs1)
                instr.rd = _parse_register(ops[0])
                if len(ops) == 3:
                    instr.rs1 = _parse_register(ops[1])
                    instr.imm = _parse_imm(ops[2])
                else:
                    instr.imm, instr.rs1 = _parse_offset(ops[1])
            else:
                # addi rd, rs1, imm
                instr.rd  = _parse_register(ops[0])
                instr.rs1 = _parse_register(ops[1])
                instr.imm = self._resolve_imm(ops[2], pc)

        elif fmt == "S":
            # sw rs2, imm(rs1)
            instr.rs2 = _parse_register(ops[0])
            instr.imm, instr.rs1 = _parse_offset(ops[1])

        elif fmt == "B":
            # beq rs1, rs2, label_or_offset
            instr.rs1 = _parse_register(ops[0])
            instr.rs2 = _parse_register(ops[1])
            instr.imm = self._resolve_branch_offset(ops[2], pc)

        elif fmt == "U":
            # lui rd, imm  (imm is the 20-bit upper value; actual = imm << 12)
            instr.rd  = _parse_register(ops[0])
            instr.imm = _parse_imm(ops[1])

        elif fmt == "J":
            # jal rd, label_or_offset
            instr.rd  = _parse_register(ops[0])
            instr.imm = self._resolve_branch_offset(ops[1], pc)

        return instr

    # ------------------------------------------------------------------
    # Immediate helpers
    # ------------------------------------------------------------------
    def _resolve_imm(self, token: str, pc: int) -> int:
        token = token.strip()
        if self.labels.exists(token):
            return self.labels.resolve(token)
        return _parse_imm(token)

    def _resolve_branch_offset(self, token: str, pc: int) -> int:
        """Branch/jump immediates are PC-relative byte offsets."""
        token = token.strip()
        if self.labels.exists(token):
            return self.labels.resolve(token) - pc
        return _parse_imm(token)
