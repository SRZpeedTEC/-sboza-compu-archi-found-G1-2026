import re
from dataclasses import dataclass


@dataclass
class AssemblyValidationError(ValueError):
    """Error legible para mostrar problemas del codigo en la interfaz."""

    description: str
    line_number: int | None = None
    instruction: str | None = None
    token: str | None = None

    def __str__(self) -> str:
        parts = []

        if self.line_number is not None:
            parts.append(f"Linea {self.line_number}")

        if self.instruction:
            parts.append(f"Instruccion: {self.instruction}")

        if self.token:
            parts.append(f"Token: {self.token}")

        parts.append(f"Detalle: {self.description}")
        return ". ".join(parts)


class Parser:
    """Limpia codigo ensamblador y detecta etiquetas.

    Esta clase no crea objetos Instruction. Su salida son strings limpios y una
    tabla de labels, justo como los consumira InstructionMemory y luego Decoder.
    """

    # Las etiquetas se restringen a identificadores simples para evitar
    # ambiguedades con operandos o inmediatos numericos.
    _LABEL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


    def parse_text(self, code: str) -> tuple[list[str], dict[str, int]]:
        """Obtiene instrucciones limpias y labels resueltos a direcciones."""
        instructions, labels, _ = self.parse_text_with_line_numbers(code)
        return instructions, labels


    def parse_text_with_line_numbers(
        self,
        code: str
    ) -> tuple[list[str], dict[str, int], dict[int, int]]:
        """Parsea preservando el numero de linea original por instruccion.

        La UI usa este mapa para reportar errores sobre el codigo fuente que
        escribio el usuario, no sobre la lista compactada de instrucciones.
        """
        if not isinstance(code, str):
            raise ValueError("El parser espera codigo fuente como texto.")

        instructions: list[str] = []
        labels: dict[str, int] = {}
        line_numbers: dict[int, int] = {}

        for line_number, original_line in enumerate(code.splitlines(), start=1):
            
            line = self._remove_comment(original_line).strip()

            if not line:
                continue

            line = self._extract_labels(line, line_number, labels, instructions)
            if not line:
                continue

            instruction_index = len(instructions)
            instructions.append(self._normalize_instruction(line))
            line_numbers[instruction_index] = line_number

        return instructions, labels, line_numbers
    

    def _remove_comment(self, line: str) -> str:
        """El caracter # inicia comentarios de linea."""
        return line.split("#", 1)[0]


    def _extract_labels(self, line: str, line_number: int, labels: dict[str, int], instructions: list[str]) -> str:

        """Extrae una o mas etiquetas al inicio de una linea.

        Permitimos `label: instruccion`. La direccion de cada label se calcula
        con la cantidad de instrucciones ya aceptadas, asumiendo palabras de
        4 bytes como en RISC-V.
        """
        if ":" in line:
            label_part, rest = line.split(":", 1)
            label_name = label_part.strip().lower()

            self._validate_label(label_name, line_number, labels)
            labels[label_name] = len(instructions) * 4
            line = rest.strip()

            if not line:
                return ""

        return line
     

    def _validate_label(self, label_name: str, line_number: int, labels: dict[str, int]) -> None:
        """Valida nombre y duplicados para mantener branches deterministas."""

        if not label_name:
            raise AssemblyValidationError(
                "Etiqueta vacia.",
                line_number=line_number,
            )
        if not self._LABEL_PATTERN.fullmatch(label_name):
            raise AssemblyValidationError(
                "Etiqueta invalida.",
                line_number=line_number,
                token=label_name,
            )
        if label_name in labels:
            raise AssemblyValidationError(
                "Etiqueta duplicada.",
                line_number=line_number,
                token=label_name,
            )
        
           
    def _normalize_instruction(self, line: str) -> str:
        """Normaliza formato sin alterar operandos de memoria como 0(x1)."""
        return " ".join(line.replace(",", " ").lower().split())
