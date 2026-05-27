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

    # Patron para validar etiquetas: deben empezar con letra o guion bajo, y luego pueden tener letras, numeros o guiones bajos.
    _LABEL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


    # Obtiene una lista de instrucciones limpias (sin comentarios ni etiquetas) y un diccionario de etiquetas con sus direcciones.
    def parse_text(self, code: str) -> tuple[list[str], dict[str, int]]:
        instructions, labels, _ = self.parse_text_with_line_numbers(code)
        return instructions, labels


    # Variante usada por la UI y los motores para conservar el numero de linea original de cada instruccion.
    def parse_text_with_line_numbers(
        self,
        code: str
    ) -> tuple[list[str], dict[str, int], dict[int, int]]:
        if not isinstance(code, str):
            raise ValueError("El parser espera codigo fuente como texto.")

        instructions: list[str] = []
        labels: dict[str, int] = {}
        line_numbers: dict[int, int] = {}

        for line_number, original_line in enumerate(code.splitlines(), start=1):
            
            # El numero de linea se conserva para mensajes de error legibles en la UI.
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
    

    # Funcion auxiliar para remover comentarios. Asume que el caracter '#' inicia un comentario, y todo lo que sigue es ignorado.
    def _remove_comment(self, line: str) -> str:
        return line.split("#", 1)[0]


    # Funcion auxiliar para extraer etiquetas al inicio de una linea. Modifica el diccionario de labels con las etiquetas encontradas y sus direcciones (basadas en la cantidad de instrucciones ya procesadas). Devuelve la parte de la linea que queda despues de remover las etiquetas.
    def _extract_labels(self, line: str, line_number: int, labels: dict[str, int], instructions: list[str]) -> str:

        """Extrae una o mas etiquetas al inicio de una linea.

        Permitimos `label: instruccion` y tambien varias etiquetas antes de una
        instruccion. Si aparece ':' dentro de una instruccion, se reporta como
        error para evitar labels ambiguas.
        """
        if ":" in line:
            label_part, rest = line.split(":", 1)
            label_name = label_part.strip().lower()

            """ Validamos la etiqueta y actualizamos el diccionario de labels. Si hay error, se lanza ValueError 
             con mensaje claro para la UI. """
            self._validate_label(label_name, line_number, labels)


            """ La direccion de la etiqueta se basa en la cantidad de instrucciones ya procesadas, asumiendo que cada 
            instruccion ocupa 4 bytes. """
            labels[label_name] = len(instructions) * 4
            line = rest.strip()

            if not line:
                return ""

        return line
     

    """ Funcion auxiliar para validar que un nombre de etiqueta es valido y no esta duplicado. Lanza ValueError 
    con mensajes claros para la UI en caso de error. """
    def _validate_label(self, label_name: str, line_number: int, labels: dict[str, int]) -> None:

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
        
           
    """Normaliza la instruccion: convierte a minusculas, reemplaza comas por espacios, y colapsa espacios multiples. 
    Esto facilita el parsing posterior."""
    def _normalize_instruction(self, line: str) -> str:
        # La normalizacion deja operandos de memoria como 0(x1) intactos.
        return " ".join(line.replace(",", " ").lower().split())
