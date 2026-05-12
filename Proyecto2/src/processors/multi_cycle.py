from src.processors.ProcessorEngine import ProcessorEngine, ProcessorSnapshot


class MultiCycleEngine(ProcessorEngine):
    """Punto de extension para dividir una instruccion en varios ciclos."""

    def load_program(self, program: list[str], labels: dict[str, int] | None = None) -> None:
        raise NotImplementedError("MultiCycleEngine se implementara en la siguiente etapa.")

    def step(self) -> ProcessorSnapshot:
        raise NotImplementedError("MultiCycleEngine se implementara en la siguiente etapa.")

    def get_snapshot(self) -> ProcessorSnapshot:
        return ProcessorSnapshot(pc=self.pc, metrics=self.metrics.dump())
