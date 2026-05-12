import re

from src.assembler.instruction import Instruction


class Decoder:
    """Convierte strings limpios en objetos Instruction.

    El decoder conoce la sintaxis del subconjunto RISC-V soportado. No limpia
    comentarios ni administra memoria de instrucciones; esas responsabilidades
    pertenecen al Parser y a InstructionMemory.
    """

    R_TYPE_OPS = {"add", "sub", "and", "or", "xor"}
    I_TYPE_OPS = {"addi"}
    LOAD_OPS = {"lw"}
    STORE_OPS = {"sw"}
    BRANCH_OPS = {"beq", "bne"}
    SUPPORTED_OPS = R_TYPE_OPS | I_TYPE_OPS | LOAD_OPS | STORE_OPS | BRANCH_OPS

    _REGISTER_PATTERN = re.compile(r"^[rx](0|[1-9]|[12][0-9]|3[01])$")
    _MEMORY_OPERAND_PATTERN = re.compile(
        r"^(?P<offset>[+-]?(?:0x[0-9a-f]+|\d+))\((?P<base>[rx](?:0|[1-9]|[12][0-9]|3[01]))\)$"
    )

    def __init__(self, labels: dict[str, int] | None = None):
        self.labels = labels or {}

    def decode(self, raw: str | None) -> Instruction | None:
        if raw is None:
            return None
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("No se puede decodificar una instruccion vacia.")

        parts = raw.split()
        opcode = parts[0]

        if opcode not in self.SUPPORTED_OPS:
            raise ValueError(f"Instruccion no soportada '{opcode}' en: {raw!r}.")

        if opcode in self.R_TYPE_OPS:
            return self._decode_r_type(raw, parts)
        if opcode in self.I_TYPE_OPS:
            return self._decode_i_type(raw, parts)
        if opcode in self.LOAD_OPS:
            return self._decode_load(raw, parts)
        if opcode in self.STORE_OPS:
            return self._decode_store(raw, parts)
        if opcode in self.BRANCH_OPS:
            return self._decode_branch(raw, parts)

        raise ValueError(f"Instruccion no soportada en: {raw!r}.")

    def _decode_r_type(self, raw: str, parts: list[str]) -> Instruction:
        self._expect_operand_count(parts, 4, "opcode rd rs1 rs2", raw)
        rd, rs1, rs2 = (self._parse_register(part, raw) for part in parts[1:4])
        return Instruction(
            opcode=parts[0],
            rd=rd,
            rs1=rs1,
            rs2=rs2,
            completeInstruction=raw,
        )

    def _decode_i_type(self, raw: str, parts: list[str]) -> Instruction:
        self._expect_operand_count(parts, 4, "opcode rd rs1 imm", raw)
        return Instruction(
            opcode=parts[0],
            rd=self._parse_register(parts[1], raw),
            rs1=self._parse_register(parts[2], raw),
            imm=self._parse_immediate(parts[3], raw),
            completeInstruction=raw,
        )

    def _decode_load(self, raw: str, parts: list[str]) -> Instruction:
        if len(parts) == 3:
            # Forma RISC-V usual: lw rd, offset(rs1). Parser ya quito comas.
            rd = self._parse_register(parts[1], raw)
            offset, base = self._parse_memory_operand(parts[2], raw)
        elif len(parts) == 4:
            # Compatibilidad con la forma educativa anterior: lw rd rs1 imm.
            rd = self._parse_register(parts[1], raw)
            base = self._parse_register(parts[2], raw)
            offset = self._parse_immediate(parts[3], raw)
        else:
            self._expect_operand_count(parts, 3, "lw rd offset(rs1)", raw)

        return Instruction(
            opcode=parts[0],
            rd=rd,
            rs1=base,
            imm=offset,
            completeInstruction=raw,
        )

    def _decode_store(self, raw: str, parts: list[str]) -> Instruction:
        if len(parts) == 3:
            # Forma RISC-V usual: sw rs2, offset(rs1). rs2 es el dato a guardar.
            rs2 = self._parse_register(parts[1], raw)
            offset, base = self._parse_memory_operand(parts[2], raw)
        elif len(parts) == 4:
            # Compatibilidad con la forma educativa anterior: sw rs2 rs1 imm.
            rs2 = self._parse_register(parts[1], raw)
            base = self._parse_register(parts[2], raw)
            offset = self._parse_immediate(parts[3], raw)
        else:
            self._expect_operand_count(parts, 3, "sw rs2 offset(rs1)", raw)

        return Instruction(
            opcode=parts[0],
            rs1=base,
            rs2=rs2,
            imm=offset,
            completeInstruction=raw,
        )

    def _decode_branch(self, raw: str, parts: list[str]) -> Instruction:
        self._expect_operand_count(parts, 4, "opcode rs1 rs2 label|imm", raw)
        return Instruction(
            opcode=parts[0],
            rs1=self._parse_register(parts[1], raw),
            rs2=self._parse_register(parts[2], raw),
            imm=self._parse_label_or_immediate(parts[3], raw),
            completeInstruction=raw,
        )

    def _expect_operand_count(
        self,
        parts: list[str],
        expected_count: int,
        expected_format: str,
        raw: str,
    ) -> None:
        if len(parts) != expected_count:
            raise ValueError(
                f"Formato invalido en {raw!r}. Esperado: {expected_format}; "
                f"recibido {len(parts) - 1} operandos."
            )

    def _parse_register(self, token: str, raw: str) -> str:
        if not self._REGISTER_PATTERN.fullmatch(token):
            raise ValueError(f"Registro invalido '{token}' en instruccion {raw!r}.")
        return token

    def _parse_immediate(self, token: str, raw: str) -> int:
        try:
            return int(token, 0)
        except ValueError as exc:
            raise ValueError(f"Inmediato invalido '{token}' en instruccion {raw!r}.") from exc

    def _parse_label_or_immediate(self, token: str, raw: str) -> int:
        # Branch puede recibir un inmediato numerico o una etiqueta resuelta por Parser.
        try:
            return int(token, 0)
        except ValueError:
            label = token.lower()
            if label not in self.labels:
                raise ValueError(f"Label no definido '{token}' en instruccion {raw!r}.")
            return self.labels[label]

    def _parse_memory_operand(self, token: str, raw: str) -> tuple[int, str]:
        match = self._MEMORY_OPERAND_PATTERN.fullmatch(token)
        if not match:
            raise ValueError(
                f"Operando de memoria invalido '{token}' en {raw!r}. "
                "Use el formato offset(registro), por ejemplo 0(x2)."
            )
        offset = self._parse_immediate(match.group("offset"), raw)
        base = self._parse_register(match.group("base"), raw)
        return offset, base
