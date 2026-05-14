class RegisterBank:
    """Banco de 32 registros enteros.

    Acepta registros `x0..x31`. El registro cero conserva la semantica RISC-V: siempre
    lee 0 y las escrituras sobre el se ignoran.
    """

    REGISTER_COUNT = 32

    def __init__(self) -> None:
        self._registers = [0] * self.REGISTER_COUNT



    def read_register(self, reg: str) -> int:
        """Lee un registro validado."""
        index = self._to_index(reg)
        if index == 0:
            return 0
        return self._registers[index]

   

    def write_register(self, reg: str, value: int) -> None:
        """Escribe un registro; x0 ignora escrituras como en RISC-V."""
        index = self._to_index(reg)
        if not isinstance(value, int):
            raise ValueError(f"El valor de registro debe ser entero: {value!r}.")
        if index == 0:
            return
        
        self._registers[index] = value



    """Funcion para obtener una copia del estado actual de los registros"""
    def get_snapshot(self) -> list[int]:
        snapshot = list(self._registers)
        snapshot[0] = 0
        return snapshot
    

    
    
    """Funcion para convertir un registro a su indice numerico, validando su formato y rango."""
    def _to_index(self, reg: str) -> int:
        if not isinstance(reg, str) or len(reg) < 2:
            raise ValueError(f"Registro invalido: {reg!r}.")

        prefix = reg[0].lower()
        number = reg[1:]

        if prefix not in {"x", "r"} or not number.isdigit():
            raise ValueError(f"Registro invalido: {reg!r}. Use x0..x31 o r0..r31.")

        index = int(number)
        if index < 0 or index >= self.REGISTER_COUNT:
            raise ValueError(f"Registro fuera de rango: {reg!r}. Use x0..x31 o r0..r31.")
        return index
