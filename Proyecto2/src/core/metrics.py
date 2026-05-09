"""
metrics.py — Simulator execution metrics

Collects and exposes performance statistics for each processor model
(single-cycle, multi-cycle, pipeline with stalls, with forwarding).

Tracked metrics:
  cycles                — clock cycles elapsed
  instructions_executed — instructions completed
  cpi                   — Cycles Per Instruction (cycles / instructions)
  stalls                — cycles wasted due to data/control hazards
  hazards               — number of hazards detected
  elapsed_time          — wall-clock execution time in seconds

History:
  Each time a run finishes, save_to_history() stores an immutable
  ExecutionSnapshot in a rolling list of up to MAX_HISTORY=10 entries.
  The UI displays them in a side-by-side comparison table.
"""
import time
from dataclasses import dataclass, field
from typing import Optional

MAX_HISTORY = 10


@dataclass
class ExecutionSnapshot:
    """Immutable record of a completed program run, stored in history."""
    processor_type: str
    cycles: int
    instructions_executed: int
    cpi: float
    stalls: int
    hazards: int
    elapsed_time: float


class Metrics:
    """
    Tracks runtime statistics for one processor instance.
    Keeps a rolling history of the last MAX_HISTORY completed runs
    so the UI can display comparisons across executions.
    """

    def __init__(self, processor_type: str = "unknown"):
        self.processor_type = processor_type
        self.cycles: int = 0
        self.instructions_executed: int = 0
        self.stalls: int = 0
        self.hazards: int = 0
        self._start_time: Optional[float] = None
        self._elapsed: float = 0.0
        self.history: list[ExecutionSnapshot] = []

    # ------------------------------------------------------------------
    # Timer control
    # ------------------------------------------------------------------
    def start(self) -> None:
        self._start_time = time.perf_counter()
        self._elapsed = 0.0

    def stop(self) -> None:
        if self._start_time is not None:
            self._elapsed = time.perf_counter() - self._start_time

    @property
    def elapsed_time(self) -> float:
        if self._start_time is not None and self._elapsed == 0.0:
            return time.perf_counter() - self._start_time
        return self._elapsed

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------
    @property
    def cpi(self) -> float:
        if self.instructions_executed == 0:
            return 0.0
        return self.cycles / self.instructions_executed

    def tick(self) -> None:
        """Advance the cycle counter by one."""
        self.cycles += 1

    def instruction_completed(self) -> None:
        self.instructions_executed += 1

    def add_stall(self, count: int = 1) -> None:
        """Record stall cycles (also counted as cycles)."""
        self.stalls += count
        self.cycles += count

    def add_hazard(self) -> None:
        self.hazards += 1

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def save_to_history(self) -> None:
        """Snapshot current state into history (rolling window)."""
        snap = ExecutionSnapshot(
            processor_type=self.processor_type,
            cycles=self.cycles,
            instructions_executed=self.instructions_executed,
            cpi=round(self.cpi, 4),
            stalls=self.stalls,
            hazards=self.hazards,
            elapsed_time=round(self.elapsed_time, 6),
        )
        self.history.append(snap)
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def reset(self) -> None:
        self.cycles = 0
        self.instructions_executed = 0
        self.stalls = 0
        self.hazards = 0
        self._start_time = None
        self._elapsed = 0.0

    def summary(self) -> dict:
        return {
            "processor_type":        self.processor_type,
            "cycles":                self.cycles,
            "instructions_executed": self.instructions_executed,
            "cpi":                   round(self.cpi, 4),
            "stalls":                self.stalls,
            "hazards":               self.hazards,
            "elapsed_time_s":        round(self.elapsed_time, 6),
        }
