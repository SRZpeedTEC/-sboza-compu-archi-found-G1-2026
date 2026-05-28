from dataclasses import asdict, dataclass


@dataclass
class Metrics:
    """Guarda las metricas principales de una ejecucion."""

    cycles: int = 0
    instructions: int = 0
    cpi: float = 0
    ipc: float = 0
    stalls: int = 0
    hazards: int = 0
    time_ps: int = 0   # tiempo acumulado en picosegundos (ciclos * periodo)
    stopped_by_cycle_limit: bool = False

    def count_cycle(self) -> None:
        self.cycles += 1

    def count_instruction(self) -> None:
        self.instructions += 1

    def add_time(self, ps: int) -> None:
        """Suma el tiempo de un ciclo de reloj simulado."""
        self.time_ps += ps

    def count_stall(self) -> None:
        self.stalls += 1

    def count_hazard(self) -> None:
        self.hazards += 1

    def reset(self) -> None:
        self.cycles = 0
        self.instructions = 0
        self.cpi = 0
        self.ipc = 0
        self.stalls = 0
        self.hazards = 0
        self.time_ps = 0
        self.stopped_by_cycle_limit = False

    def update_cpi(self) -> None:
        self.cpi = self.cycles / self.instructions if self.instructions > 0 else 0

    def update_ipc(self) -> None:
        self.ipc = self.instructions / self.cycles if self.cycles > 0 else 0

    def get_metrics(self) -> dict[str, int | float]:
        self.update_cpi()
        self.update_ipc()
        return asdict(self)
