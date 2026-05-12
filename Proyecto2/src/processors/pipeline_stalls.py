from src.processors.ProcessorEngine import ProcessorEngine, ProcessorSnapshot


class PipelineStallEngine(ProcessorEngine):
    """Punto de extension para pipeline con deteccion de riesgos y stalls."""

    def load_program(self, program: list[str], labels: dict[str, int] | None = None) -> None:
        raise NotImplementedError("PipelineStallEngine se implementara en la siguiente etapa.")

    def step(self) -> ProcessorSnapshot:
        raise NotImplementedError("PipelineStallEngine se implementara en la siguiente etapa.")

    def get_snapshot(self) -> ProcessorSnapshot:
        return ProcessorSnapshot(pc=self.pc, metrics=self.metrics.dump())
