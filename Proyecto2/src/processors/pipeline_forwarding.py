from src.processors.ProcessorEngine import ProcessorEngine, ProcessorSnapshot


class PipelineForwardingEngine(ProcessorEngine):
    """Punto de extension para pipeline con forwarding."""

    def load_program(self, program: list[str], labels: dict[str, int] | None = None) -> None:
        raise NotImplementedError("PipelineForwardingEngine se implementara en la siguiente etapa.")

    def step(self) -> ProcessorSnapshot:
        raise NotImplementedError("PipelineForwardingEngine se implementara en la siguiente etapa.")

    def get_snapshot(self) -> ProcessorSnapshot:
        return ProcessorSnapshot(pc=self.pc, metrics=self.metrics.dump())
