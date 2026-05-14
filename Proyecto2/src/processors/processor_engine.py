from dataclasses import dataclass, field

from src.core.metrics import Metrics


@dataclass
class ProcessorSnapshot:
    pc: int = 0
    metrics: dict[str, int] = field(default_factory=dict)


class ProcessorEngine:
    def __init__(self) -> None:
        self.pc = 0
        self.metrics = Metrics()

    def load_program(self, program, labels=None):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError


    def run(self):
        while True:
            self.step()


    def get_snapshot(self) -> ProcessorSnapshot:
        return ProcessorSnapshot(pc=self.pc, metrics=self.metrics.get_metrics())

