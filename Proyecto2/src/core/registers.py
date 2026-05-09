"""
registers.py — Banco de registros RISC-V RV32I

Modela los 32 registros de propósito general (x0-x31) del procesador.
Características principales:
  - x0 (zero) es hardwired a 0: cualquier escritura a él se descarta.
  - Todos los valores se mantienen en representación signed 32-bit
    (complemento a 2), igual que el hardware real.
  - Se puede acceder por índice numérico (0-31) o por nombre ABI
    (zero, ra, sp, a0, t0, s0, etc.).
  - snapshot() devuelve un dict con todos los registros, que la UI
    usa para actualizar la tabla de registros en cada ciclo.
"""

# ABI name -> register index (x0-x31)
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

# Canonical ABI name for each index (fp is an alias of s0, so we keep s0)
INDEX_TO_ABI: dict[int, str] = {v: k for k, v in ABI_NAMES.items() if k != "fp"}


def _to_int32(value: int) -> int:
    """Force value into the signed 32-bit range."""
    value = value & 0xFFFF_FFFF
    return value - 0x1_0000_0000 if value >= 0x8000_0000 else value


class RegisterFile:
    """
    Models the 32 general-purpose registers of a RISC-V RV32I processor.
    x0 (zero) is hardwired to 0 and silently ignores writes.
    All values are kept as signed 32-bit integers.
    """

    def __init__(self):
        self._regs: list[int] = [0] * 32

    # ------------------------------------------------------------------
    # Core read / write
    # ------------------------------------------------------------------
    def read(self, index: int) -> int:
        if not 0 <= index <= 31:
            raise IndexError(f"Register index out of range: {index}")
        return self._regs[index]

    def write(self, index: int, value: int) -> None:
        if not 0 <= index <= 31:
            raise IndexError(f"Register index out of range: {index}")
        if index == 0:
            return  # x0 is always 0
        self._regs[index] = _to_int32(value)

    # ------------------------------------------------------------------
    # Convenience: access by ABI name
    # ------------------------------------------------------------------
    def read_by_name(self, name: str) -> int:
        return self.read(ABI_NAMES[name.lower()])

    def write_by_name(self, name: str, value: int) -> None:
        self.write(ABI_NAMES[name.lower()], value)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def snapshot(self) -> dict[str, int]:
        """Return a dict mapping ABI name -> current value for all 32 registers."""
        return {INDEX_TO_ABI.get(i, f"x{i}"): self._regs[i] for i in range(32)}

    def reset(self) -> None:
        self._regs = [0] * 32

    def __repr__(self) -> str:
        lines = [f"  {INDEX_TO_ABI.get(i, f'x{i}'):>4} (x{i:<2}): {self._regs[i]}"
                 for i in range(32)]
        return "RegisterFile:\n" + "\n".join(lines)
