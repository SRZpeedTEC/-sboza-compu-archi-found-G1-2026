from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Metrics:
    """Metricas basicas compartidas por los futuros motores de procesador."""

    cycles: int = 0
    instructions_executed: int = 0
    stalls: int = 0
    flushes: int = 0

    def dump(self) -> dict[str, int]:
        return asdict(self)
