from dataclasses import asdict, dataclass


@dataclass
class Metrics:
    """Guarda las metricas principales de una ejecucion."""

    cycles: int = 0
    instructions: int = 0
    stalls: int = 0
    hazards: int = 0

    def count_cycle(self) -> None:
        self.cycles += 1

    def count_instruction(self) -> None:
        self.instructions += 1

    def count_stall(self) -> None:
        self.stalls += 1

    def count_hazard(self) -> None:
        self.hazards += 1


    def reset(self) -> None:
        self.cycles = 0
        self.instructions = 0
        self.stalls = 0
        self.hazards = 0

    def get_metrics(self) -> dict[str, int]:
        return asdict(self)
