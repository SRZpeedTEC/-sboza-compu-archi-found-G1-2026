"""
memory.py — RISC-V processor data memory

Implements a byte-addressable data memory of configurable size
(default 4 096 bytes) backed by a sparse dictionary for efficiency.

Conventions:
  - Byte order: little-endian (matching RISC-V RV32I).
  - Access widths: byte (8 b), halfword (16 b), word (32 b).
  - Signed / unsigned: loads come in signed and unsigned variants
    (lb/lbu, lh/lhu; lw is always sign-extended in RV32I).
  - last_access: records the most recent operation so the UI can
    highlight the active memory cell in real time.

Instructions that use this module: lw, sw (and optionally lb, lh, sb, sh).
"""


class DataMemory:
    """
    Byte-addressable data memory backed by a sparse dictionary.
    Supports byte, halfword (16-bit), and word (32-bit) accesses,
    all using little-endian byte order (RISC-V convention).
    """

    def __init__(self, size: int = 4096):
        self.size = size
        self._mem: dict[int, int] = {}
        self.last_access: dict = {"type": None, "address": None, "value": None}

    # ------------------------------------------------------------------
    # Bounds check
    # ------------------------------------------------------------------
    def _check(self, address: int, width: int = 1) -> None:
        if address < 0 or address + width > self.size:
            raise MemoryError(
                f"Address {address:#010x} out of bounds (size={self.size})"
            )

    # ------------------------------------------------------------------
    # Byte
    # ------------------------------------------------------------------
    def load_byte(self, address: int) -> int:
        """Load unsigned byte (0-255)."""
        self._check(address)
        val = self._mem.get(address, 0) & 0xFF
        self.last_access = {"type": "LB", "address": address, "value": val}
        return val

    def load_byte_signed(self, address: int) -> int:
        """Load sign-extended byte (-128..127)."""
        val = self.load_byte(address)
        return val if val < 128 else val - 256

    def store_byte(self, address: int, value: int) -> None:
        self._check(address)
        self._mem[address] = value & 0xFF
        self.last_access = {"type": "SB", "address": address, "value": value & 0xFF}

    # ------------------------------------------------------------------
    # Halfword (16-bit, little-endian)
    # ------------------------------------------------------------------
    def load_halfword(self, address: int) -> int:
        """Load unsigned halfword."""
        self._check(address, 2)
        val = self._mem.get(address, 0) | (self._mem.get(address + 1, 0) << 8)
        val &= 0xFFFF
        self.last_access = {"type": "LH", "address": address, "value": val}
        return val

    def load_halfword_signed(self, address: int) -> int:
        val = self.load_halfword(address)
        return val if val < 0x8000 else val - 0x10000

    def store_halfword(self, address: int, value: int) -> None:
        self._check(address, 2)
        self._mem[address]     = value & 0xFF
        self._mem[address + 1] = (value >> 8) & 0xFF
        self.last_access = {"type": "SH", "address": address, "value": value & 0xFFFF}

    # ------------------------------------------------------------------
    # Word (32-bit, little-endian)
    # ------------------------------------------------------------------
    def load_word(self, address: int) -> int:
        """Load signed 32-bit word."""
        self._check(address, 4)
        val = (
            self._mem.get(address, 0)
            | (self._mem.get(address + 1, 0) << 8)
            | (self._mem.get(address + 2, 0) << 16)
            | (self._mem.get(address + 3, 0) << 24)
        )
        val &= 0xFFFF_FFFF
        if val >= 0x8000_0000:
            val -= 0x1_0000_0000
        self.last_access = {"type": "LW", "address": address, "value": val}
        return val

    def store_word(self, address: int, value: int) -> None:
        self._check(address, 4)
        value &= 0xFFFF_FFFF
        self._mem[address]     = value & 0xFF
        self._mem[address + 1] = (value >> 8)  & 0xFF
        self._mem[address + 2] = (value >> 16) & 0xFF
        self._mem[address + 3] = (value >> 24) & 0xFF
        self.last_access = {"type": "SW", "address": address, "value": value}

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def snapshot(self) -> list[tuple[int, int]]:
        """Return all written addresses as (address, byte_value) pairs, sorted."""
        if not self._mem:
            return []
        max_addr = max(self._mem.keys())
        return [(addr, self._mem.get(addr, 0)) for addr in range(0, max_addr + 1)]

    def reset(self) -> None:
        self._mem.clear()
        self.last_access = {"type": None, "address": None, "value": None}

    def __repr__(self) -> str:
        if not self._mem:
            return "DataMemory: (empty)"
        entries = ", ".join(
            f"{addr:#06x}={val}" for addr, val in sorted(self._mem.items())
        )
        return f"DataMemory: [{entries}]"
