"""
alu.py — Unidad Aritmético-Lógica (ALU) RISC-V RV32I

Implementa todas las operaciones que el datapath necesita para ejecutar
las instrucciones del simulador. La unidad de control le indica a la
ALU cuál operación realizar mediante una constante string (ALU_*).

Operaciones disponibles:
  ADD, SUB          — suma y resta (también usadas para calcular
                       direcciones en lw, sw, jalr)
  AND, OR, XOR      — lógicas bit a bit
  SLL, SRL, SRA     — desplazamientos (lógico izquierdo, lógico derecho,
                       aritmético derecho con extensión de signo)
  SLT, SLTU         — set-less-than signed/unsigned (→ 0 o 1)
  LUI               — pasa el operando B sin modificarlo (para lui)
  SEQ, SNE          — comparadores para beq y bne (→ 1 si condición true)
  SLT_B, SGE_B      — comparadores para blt y bge
  SLTU_B, SGEU_B    — variantes unsigned para bltu y bgeu

Toda aritmética interna se hace en signed 32-bit para respetar el
comportamiento de complemento a dos del hardware real.
"""

# ALU operation identifiers
ALU_ADD    = "ADD"
ALU_SUB    = "SUB"
ALU_AND    = "AND"
ALU_OR     = "OR"
ALU_XOR    = "XOR"
ALU_SLL    = "SLL"   # shift left logical
ALU_SRL    = "SRL"   # shift right logical
ALU_SRA    = "SRA"   # shift right arithmetic
ALU_SLT    = "SLT"   # set less than (signed)
ALU_SLTU   = "SLTU"  # set less than (unsigned)
ALU_LUI    = "LUI"   # pass operand B through (for LUI / upper immediate)
ALU_SEQ    = "SEQ"   # 1 if A == B (beq)
ALU_SNE    = "SNE"   # 1 if A != B (bne)
ALU_SLT_B  = "SLT_B" # 1 if A < B signed  (blt)
ALU_SGE_B  = "SGE_B" # 1 if A >= B signed  (bge)
ALU_SLTU_B = "SLTU_B"# 1 if A < B unsigned (bltu)
ALU_SGEU_B = "SGEU_B"# 1 if A >= B unsigned (bgeu)

_MASK32 = 0xFFFF_FFFF


def _s32(val: int) -> int:
    """Clamp to signed 32-bit range."""
    val &= _MASK32
    return val - 0x1_0000_0000 if val >= 0x8000_0000 else val


def _u32(val: int) -> int:
    return val & _MASK32


class ALU:
    """
    Arithmetic Logic Unit for RV32I.

    After each execute() call the following flags are updated:
      zero_flag  – result is zero (used by branch comparators)
      negative   – MSB of result is 1
    """

    def __init__(self):
        self.zero_flag: bool = False
        self.negative: bool = False

    def execute(self, operation: str, a: int, b: int) -> int:
        """Perform *operation* on operands a and b; return signed 32-bit result."""
        result = _s32(self._compute(operation, a, b))
        self.zero_flag = (result == 0)
        self.negative  = (result < 0)
        return result

    # ------------------------------------------------------------------
    # Internal computation (returns raw Python int, normalised by execute)
    # ------------------------------------------------------------------
    def _compute(self, op: str, a: int, b: int) -> int:
        a32 = _s32(a)
        b32 = _s32(b)
        au  = _u32(a)
        bu  = _u32(b)
        shamt = bu & 0x1F  # shift amount is lower 5 bits

        if op == ALU_ADD:    return a32 + b32
        if op == ALU_SUB:    return a32 - b32
        if op == ALU_AND:    return au  & bu
        if op == ALU_OR:     return au  | bu
        if op == ALU_XOR:    return au  ^ bu
        if op == ALU_SLL:    return _u32(au << shamt)
        if op == ALU_SRL:    return au >> shamt
        if op == ALU_SRA:    return a32 >> shamt      # Python >> preserves sign
        if op == ALU_SLT:    return 1 if a32 < b32 else 0
        if op == ALU_SLTU:   return 1 if au  < bu  else 0
        if op == ALU_LUI:    return b32              # pass upper-immediate through
        if op == ALU_SEQ:    return 1 if a32 == b32 else 0
        if op == ALU_SNE:    return 1 if a32 != b32 else 0
        if op == ALU_SLT_B:  return 1 if a32 <  b32 else 0
        if op == ALU_SGE_B:  return 1 if a32 >= b32 else 0
        if op == ALU_SLTU_B: return 1 if au  <  bu  else 0
        if op == ALU_SGEU_B: return 1 if au  >= bu  else 0

        raise ValueError(f"Unknown ALU operation: '{op}'")
