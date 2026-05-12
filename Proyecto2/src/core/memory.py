class Memory:
    """Memoria de datos direccionada por bytes y almacenada por palabras."""

    WORD_SIZE_BYTES = 4

    def __init__(self, word_count: int = 1024) -> None:
        if word_count <= 0:
            raise ValueError("La memoria debe tener al menos una palabra.")
        self._memory = [0] * word_count

    def load_word(self, address: int) -> int:
        """Lee una palabra completa desde una direccion alineada."""
        index = self._address_to_index(address)
        return self._memory[index]

    def store_word(self, address: int, value: int) -> None:
        """Escribe una palabra completa desde una direccion alineada."""
        if not isinstance(value, int):
            raise ValueError(f"El valor de memoria debe ser entero: {value!r}.")
        index = self._address_to_index(address)
        self._memory[index] = value

    def dump(self) -> list[int]:
        return list(self._memory)

    def _address_to_index(self, address: int) -> int:
        if not isinstance(address, int):
            raise ValueError(f"La direccion debe ser entera: {address!r}.")
        if address < 0:
            raise ValueError(f"La direccion no puede ser negativa: {address}.")
        if address % self.WORD_SIZE_BYTES != 0:
            raise ValueError(f"La direccion debe estar alineada a 4 bytes: {address}.")

        index = address // self.WORD_SIZE_BYTES
        if index >= len(self._memory):
            raise IndexError(
                f"Direccion fuera de memoria: address={address}, bytes={len(self._memory) * 4}."
            )
        return index
