from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

from src.core.metrics import Metrics


@dataclass(slots=True)
class ProcessorSnapshot:
    """Estado serializable que la UI podra dibujar en el futuro."""

    pc: int
    registers: list[int] = field(default_factory=list)
    memory: list[int] = field(default_factory=list)
    metrics: dict[str, int] = field(default_factory=dict)
    active_modules: list[str] = field(default_factory=list)
    control_signals: dict[str, bool | str | None] = field(default_factory=dict)
    pipeline_stages: dict[str, str | None] = field(default_factory=dict)

    def dump(self) -> dict[str, object]:
        return asdict(self)


class ProcessorEngine(ABC):
    """Contrato comun para motores single-cycle, multi-cycle y pipeline."""

    def __init__(self) -> None:
        self.pc = 0
        self.metrics = Metrics()

    @abstractmethod
    def load_program(self, program: list[str], labels: dict[str, int] | None = None) -> None:
        """Carga un programa ya parseado.

        Los motores reciben strings limpios y labels; no vuelven a parsear texto
        fuente. Esto conserva el flujo Parser -> InstructionMemory -> Decoder.
        """

    @abstractmethod
    def step(self) -> ProcessorSnapshot:
        """Ejecuta un paso de la microarquitectura."""

    def run(self, max_steps: int | None = None) -> list[ProcessorSnapshot]:
        """Ejecuta varios pasos y devuelve snapshots para la futura UI."""
        snapshots: list[ProcessorSnapshot] = []
        steps = 0

        while max_steps is None or steps < max_steps:
            snapshots.append(self.step())
            steps += 1

        return snapshots

    @abstractmethod
    def get_snapshot(self) -> ProcessorSnapshot:
        """Devuelve el ultimo estado observable."""
