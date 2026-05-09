"""
labels.py — Tabla de etiquetas para el ensamblador RISC-V

El parser realiza dos pasadas sobre el código fuente. En la primera
pasada construye esta tabla que asocia cada nombre de etiqueta con
su dirección de byte correspondiente en la memoria de instrucciones.
En la segunda pasada, las instrucciones de salto (beq, bne, jal, jalr)
consultan esta tabla para convertir el nombre de la etiqueta en el
offset PC-relativo que necesita la instrucción.
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
