import re

from src.assembler.instruction import Instruction


class Decoder:
    """Convierte strings limpios en objetos Instruction.

    El decoder conoce la sintaxis del subconjunto RISC-V soportado. No limpia
    comentarios ni administra memoria de instrucciones; esas responsabilidades
    pertenecen al Parser y a InstructionMemory.
    """

    # Las operaciones se agrupan por formato para validar cantidad y tipo de
    # operandos antes de construir Instruction.
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

    def decode(self, instruction_line : str) -> Instruction:
        """Decodifica una instruccion limpia en un objeto Instruction.

        El Parser ya elimino comentarios y labels; aqui se valida que el opcode
        exista y que cada operando tenga el formato esperado.
        """
        
        if not isinstance(instruction_line, str) or not instruction_line.strip():
            raise ValueError("No se puede decodificar una instruccion vacia.")
        
        instruction_line = instruction_line.replace(",", " ")
        
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
    

    def _decode_r_type(self, instruction_line: str, parts: list[str]) -> Instruction:
        """Formato R: opcode rd rs1 rs2."""
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
        """Formato I aritmetico: opcode rd rs1 imm."""
        self._expect_operand_count(parts, 4, "opcode rd rs1 imm", instruction_line)
        return Instruction(
            opcode=parts[0],
            rd=self._parse_register(parts[1], instruction_line),
            rs1=self._parse_register(parts[2], instruction_line),
            imm=self._parse_immediate(parts[3], instruction_line),
            complete_instruction=instruction_line,
        )

    def _decode_load(self, instruction_line: str, parts: list[str]) -> Instruction:
        """Formato load: opcode rd offset(rs1)."""
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
        """Formato store: opcode rs2 offset(rs1)."""
        
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
        """Formato branch: opcode rs1 rs2 label|imm."""
        self._expect_operand_count(parts, 4, "opcode rs1 rs2 label|imm", instruction_line)

        return Instruction(
            opcode=parts[0],
            rs1=self._parse_register(parts[1], instruction_line),
            rs2=self._parse_register(parts[2], instruction_line),
            imm=self._parse_label_or_immediate(parts[3], instruction_line),
            complete_instruction=instruction_line,
        )
    

    def _expect_operand_count(self, parts: list[str], expected_count: int, 
        expected_format: str, instruction_line: str) -> None:
        """Valida cantidad exacta de operandos para errores claros."""

        if len(parts) != expected_count:
            raise ValueError(
                f"Formato invalido en {instruction_line!r}. Esperado: {expected_format}; "
                f"recibido {len(parts) - 1} operandos."
            )


    def _parse_register(self, token: str, instruction_line: str) -> str:
        """Valida registros x0..x31."""
        if not self._REGISTER_PATTERN.fullmatch(token):
            raise ValueError(f"Registro invalido '{token}' en instruccion {instruction_line!r}.")
        return token
    

    def _parse_immediate(self, token: str, instruction_line: str) -> int:
        """Acepta inmediatos decimales o hexadecimales usando int(..., 0)."""
        try:
            return int(token, 0)
        except ValueError as exc:
            raise ValueError(f"Inmediato invalido '{token}' en instruccion {instruction_line!r}.") from exc


    def _parse_label_or_immediate(self, token: str, instruction_line: str) -> int:
        """Resuelve branch hacia inmediato numerico o etiqueta del Parser."""
        try:
            return int(token, 0)
        except ValueError:
            label = token.lower()
            if label not in self.labels:
                raise ValueError(f"Label no definido '{token}' en instruccion {instruction_line!r}.")
            return self.labels[label]


    def _parse_memory_operand(self, token: str, instruction_line: str) -> tuple[int, str]:
        """Parsea offset(base), por ejemplo 0(x2)."""
        match = self._MEMORY_OPERAND_PATTERN.fullmatch(token)
        if not match:
            raise ValueError(
                f"Operando de memoria invalido '{token}' en {instruction_line!r}. "
                "Use el formato offset(registro), por ejemplo 0(x2)."
            )
        offset = self._parse_immediate(match.group("offset"), instruction_line)
        base = self._parse_register(match.group("base"), instruction_line)
        return offset, base
