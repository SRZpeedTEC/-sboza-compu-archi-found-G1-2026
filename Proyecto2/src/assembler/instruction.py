from dataclasses import dataclass


@dataclass(slots=True)
class Instruction:
    """Representa una instruccion ya decodificada.

    El parser conserva texto limpio; esta clase aparece recien en el decoder.
    Asi mantenemos una frontera clara para reutilizar Parser, Decoder y
    ControlUnit en procesadores single-cycle, multi-cycle o pipeline.
    """

    opcode: str
    rd: str | None = None
    rs1: str | None = None
    rs2: str | None = None
    imm: int | None = None
    completeInstruction: str | None = None

    @property
    def raw(self) -> str | None:
        """Alias legible para el texto original limpio."""
        return self.completeInstruction
