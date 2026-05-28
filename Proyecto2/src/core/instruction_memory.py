class InstructionMemory:
    """Memoria de instrucciones con strings limpios.

    Por decision arquitectonica, esta memoria no guarda objetos Instruction.
    Cada motor de procesador decide cuando llamar al Decoder despues de fetch.
    """

    WORD_SIZE_BYTES = 4

    def __init__(self) -> None:
        self._instructions: list[str] = []

    def load_instructions(self, instructions: list[str]) -> None:
        """Carga instrucciones ya normalizadas por Parser.

        La memoria conserva strings, no Instruction, para que cada motor decida
        en que momento exacto ocurre la decodificacion.
        """
        
        if not isinstance(instructions, list):
            raise ValueError("InstructionMemory.load_program espera una lista de strings.")
        for index, instruction in enumerate(instructions):
            if not isinstance(instruction, str) or not instruction.strip():
                raise ValueError(f"Instruccion invalida en posicion {index}: {instruction!r}.")
        self._instructions = list(instructions)

    def load_program(self, instructions: list[str]) -> None:
        """Alias publico conservado por compatibilidad con pruebas y UI."""
        self.load_instructions(instructions)


    def fetch(self, pc: int) -> str:
        """Retorna el string crudo asociado al PC."""
        
        self._validate_pc(pc)
        index = pc // self.WORD_SIZE_BYTES

        if index >= len(self._instructions):
            raise IndexError(f"PC fuera del programa: pc={pc}, instrucciones={len(self._instructions)}.")
        return self._instructions[index]
    
    
    def get_snapshot(self) -> list[str]:
        """Retorna una copia del estado actual de las instrucciones."""
        return list(self._instructions)
    

    def _validate_pc(self, pc: int) -> None:
        """Valida que el PC sea entero, no negativo y alineado a palabra."""
        if not isinstance(pc, int):
            raise ValueError(f"PC debe ser entero, recibido: {pc!r}.")
        if pc < 0:
            raise ValueError(f"PC no puede ser negativo: {pc}.")
        if pc % self.WORD_SIZE_BYTES != 0:
            raise ValueError(f"PC debe estar alineado a 4 bytes: {pc}.")
