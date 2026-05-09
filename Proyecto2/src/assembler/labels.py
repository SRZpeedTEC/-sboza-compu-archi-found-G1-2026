"""
labels.py — Label table for the RISC-V assembler

The parser makes two passes over the source code. In the first pass it
builds this table, associating each label name with its byte address in
instruction memory. In the second pass, branch and jump instructions
(beq, bne, jal, jalr) query this table to convert a label name into the
PC-relative offset the instruction encoding requires.
"""


class LabelTable:
    """Maps label names to their byte addresses in the instruction memory."""

    def __init__(self):
        self._table: dict[str, int] = {}

    def add(self, name: str, address: int) -> None:
        if name in self._table:
            raise ValueError(f"Duplicate label definition: '{name}'")
        self._table[name] = address

    def resolve(self, name: str) -> int:
        if name not in self._table:
            raise KeyError(f"Undefined label: '{name}'")
        return self._table[name]

    def exists(self, name: str) -> bool:
        return name in self._table

    def all(self) -> dict[str, int]:
        return dict(self._table)

    def clear(self) -> None:
        self._table.clear()

    def __repr__(self) -> str:
        return f"LabelTable({self._table})"
