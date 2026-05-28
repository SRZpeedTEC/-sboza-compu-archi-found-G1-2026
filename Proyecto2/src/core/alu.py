import operator


class ALU:
    """Implementacion de la Unidad Aritmetico Logica (ALU)."""

    # La tabla centraliza la seleccion de operacion que viene de ControlUnit.
    _OPERATIONS = {
        "ADD": operator.add,
        "SUB": operator.sub,
        "AND": operator.and_,
        "OR": operator.or_,
        "XOR": operator.xor,
    }

    def execute(self, operation: str, a: int, b: int) -> int:
        """Ejecuta la operacion seleccionada por ControlUnit.

        La tabla evita repetir un metodo por cada operacion y deja visible el
        conjunto de operaciones soportadas.
        """
        if operation not in self._OPERATIONS:
            raise ValueError(f"Operacion ALU no soportada: {operation!r}.")
        return self._OPERATIONS[operation](a, b)
