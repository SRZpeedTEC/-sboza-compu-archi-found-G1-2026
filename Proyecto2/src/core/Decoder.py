import re

from src.assembler.instruction import Instruction


class Decoder:
    """Convierte strings limpios en objetos Instruction.

    El decoder conoce la sintaxis del subconjunto RISC-V soportado. No limpia
    comentarios ni administra memoria de instrucciones; esas responsabilidades
    pertenecen al Parser y a InstructionMemory.
    """

    """ Conjuntos de operaciones soportadas, organizados por tipo. Esto facilita la decodificacion y la 
    validacion de formato. Si se quisiera agregar mas instrucciones, se puede ampliar """
    R_TYPE_OPS = {"add", "sub", "and", "or", "xor"}
    I_TYPE_OPS = {"addi"}
    LOAD_OPS = {"lw"}
    STORE_OPS = {"sw"}
    BRANCH_OPS = {"beq", "bne"}
    SUPPORTED_OPS = R_TYPE_OPS | I_TYPE_OPS | LOAD_OPS | STORE_OPS | BRANCH_OPS



    _REGISTER_PATTERN = re.compile(r"^[x](0|[1-9]|[12][0-9]|3[01])$")
    _MEMORY_OPERAND_PATTERN = re.compile(
        r"^(?P<offset>[+-]?(?:0x[0-9a-f]+|\d+))\((?P<base>[x](?:0|[1-9]|[12][0-9]|3[01]))\)$"
    )


    def __init__(self, labels: dict[str, int] | None = None):
        self.labels = labels or {}

    """ Decodifica una linea de instruccion limpia (sin comentarios ni etiquetas) en un objeto Instruction. 
    Si la linea es None, devuelve None. Si la linea no es un string valido o no corresponde a una instruccion 
    soportada, lanza ValueError con mensaje claro para la UI. """

    def decode(self, instruction_line : str) -> Instruction:
        
        if not isinstance(instruction_line, str) or not instruction_line.strip():
            raise ValueError("No se puede decodificar una instruccion vacia.")

        parts = instruction_line.split()
        opcode = parts[0]

        if opcode not in self.SUPPORTED_OPS:
            raise ValueError(f"Instruccion no soportada '{opcode}' en: {instruction_line!r}.")

        if opcode in self.R_TYPE_OPS:
            return self._decode_r_type(instruction_line, parts)
        if opcode in self.I_TYPE_OPS:
            return self._decode_i_type(instruction_line, parts)
        if opcode in self.LOAD_OPS:
            return self._decode_load(instruction_line, parts)
        if opcode in self.STORE_OPS:
            return self._decode_store(instruction_line, parts)
        if opcode in self.BRANCH_OPS:
            return self._decode_branch(instruction_line, parts)
    

    """Decodificadores por tipo de instruccion. Cada uno valida el formato especifico de su tipo,
    y extrae los operandos correspondientes."""

    def _decode_r_type(self, instruction_line: str, parts: list[str]) -> Instruction:
        self._expect_operand_count(parts, 4, "opcode rd rs1 rs2", instruction_line)
        rd, rs1, rs2 = (self._parse_register(part, instruction_line) for part in parts[1:4])
        return Instruction(
            opcode=parts[0],
            rd=rd,
            rs1=rs1,
            rs2=rs2,
            complete_instruction=instruction_line,
        )

    def _decode_i_type(self, instruction_line: str, parts: list[str]) -> Instruction:
        self._expect_operand_count(parts, 4, "opcode rd rs1 imm", instruction_line)
        return Instruction(
            opcode=parts[0],
            rd=self._parse_register(parts[1], instruction_line),
            rs1=self._parse_register(parts[2], instruction_line),
            imm=self._parse_immediate(parts[3], instruction_line),
            complete_instruction=instruction_line,
        )

    def _decode_load(self, instruction_line: str, parts: list[str]) -> Instruction:
        self._expect_operand_count(parts, 3, "opcode rd offset(rs1)", instruction_line)
        offset, base = self._parse_memory_operand(parts[2], instruction_line)

        return Instruction(
            opcode=parts[0],
            rd=self._parse_register(parts[1], instruction_line),
            rs1=base,
            imm=offset,
            complete_instruction=instruction_line,
        )

    def _decode_store(self, instruction_line: str, parts: list[str]) -> Instruction:
        
        self._expect_operand_count(parts, 3, "opcode rs2 offset(rs1)", instruction_line)
        offset, base = self._parse_memory_operand(parts[2], instruction_line)

        return Instruction(
            opcode=parts[0],
            rs1=base,
            rs2=self._parse_register(parts[1], instruction_line),
            imm=offset,
            complete_instruction=instruction_line,
        )
    

    def _decode_branch(self, instruction_line: str, parts: list[str]) -> Instruction:
        self._expect_operand_count(parts, 4, "opcode rs1 rs2 label|imm", instruction_line)

        return Instruction(
            opcode=parts[0],
            rs1=self._parse_register(parts[1], instruction_line),
            rs2=self._parse_register(parts[2], instruction_line),
            imm=self._parse_label_or_immediate(parts[3], instruction_line),
            complete_instruction=instruction_line,
        )
    

    """ Funcion auxiliar para validar que una instruccion tiene la cantidad de operandos esperada. 
    Si no, lanza ValueError con mensaje claro para la UI. """
    def _expect_operand_count(self, parts: list[str], expected_count: int, 
        expected_format: str, instruction_line: str) -> None:

        if len(parts) != expected_count:
            raise ValueError(
                f"Formato invalido en {instruction_line!r}. Esperado: {expected_format}; "
                f"recibido {len(parts) - 1} operandos."
            )


    """ Funcion auxiliar para validar que un token es un registro valido 
        (x0-x31). Si es valido, devuelve el token."""
    def _parse_register(self, token: str, instruction_line: str) -> str:
        if not self._REGISTER_PATTERN.fullmatch(token):
            raise ValueError(f"Registro invalido '{token}' en instruccion {instruction_line!r}.")
        return token
    

    """ Funcion auxiliar para validar que un token es un inmediato valido (decimal o hexadecimal)."""
    def _parse_immediate(self, token: str, instruction_line: str) -> int:
        try:
            return int(token, 0)
        except ValueError as exc:
            raise ValueError(f"Inmediato invalido '{token}' en instruccion {instruction_line!r}.") from exc


    """ Funcion auxiliar para parsear el operando de un branch, que puede ser un inmediato numerico 
    o una etiqueta resuelta por Parser."""
    def _parse_label_or_immediate(self, token: str, instruction_line: str) -> int:
        # Branch puede recibir un inmediato numerico o una etiqueta resuelta por Parser.
        try:
            return int(token, 0)
        except ValueError:
            label = token.lower()
            if label not in self.labels:
                raise ValueError(f"Label no definido '{token}' en instruccion {instruction_line!r}.")
            return self.labels[label]


    """ Funcion auxiliar para parsear un operando de memoria del formato offset(base), por ejemplo 0(x2)."""
    def _parse_memory_operand(self, token: str, instruction_line: str) -> tuple[int, str]:
        match = self._MEMORY_OPERAND_PATTERN.fullmatch(token)
        if not match:
            raise ValueError(
                f"Operando de memoria invalido '{token}' en {instruction_line!r}. "
                "Use el formato offset(registro), por ejemplo 0(x2)."
            )
        offset = self._parse_immediate(match.group("offset"), instruction_line)
        base = self._parse_register(match.group("base"), instruction_line)
        return offset, base
