from src.processors.ProcessorEngine import ProcessorEngine, ProcessorSnapshot


class SingleCycleEngine(ProcessorEngine):
    """Punto de extension para ejecutar una instruccion completa por ciclo."""

    def load_program(self, program: list[str], labels: dict[str, int] | None = None) -> None:
        raise NotImplementedError("SingleCycleEngine se implementara en la siguiente etapa.")

    def step(self) -> ProcessorSnapshot:
        raise NotImplementedError("SingleCycleEngine se implementara en la siguiente etapa.")

    def get_snapshot(self) -> ProcessorSnapshot:
        return ProcessorSnapshot(pc=self.pc, metrics=self.metrics.dump())
