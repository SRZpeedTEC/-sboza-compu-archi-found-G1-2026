"""
base_processor.py — Clase base abstracta para todos los modelos de procesador

Define el estado de hardware compartido y la interfaz común que deben
implementar los cuatro modelos del simulador:
  - Procesador uniciclo       (single_cycle.py)
  - Procesador multiciclo     (multi_cycle.py)
  - Segmentado con stalls     (pipeline_stalls.py)
  - Segmentado con forwarding (pipeline_forwarding.py)

Estado interno que BaseProcessor gestiona:
  registers  — banco de 32 registros RV32I (RegisterFile)
  memory     — memoria de datos byte-addressable (DataMemory)
  metrics    — contadores de ciclos, CPI, stalls, hazards (Metrics)
  pc         — Program Counter en bytes (int)
  pipeline   — ocupación actual de las 5 etapas IF/ID/EX/MEM/WB
  program    — lista de Instruction cargada por el parser

Interfaz que cada subclase debe implementar:
  step() → bool   ejecuta un ciclo; retorna False cuando termina
  run()           ejecuta el programa completo de una vez

state_snapshot() devuelve todo el estado en un dict serializable
que la capa UI lee en cada ciclo para refrescar los paneles.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.registers import RegisterFile
from src.core.memory import DataMemory
from src.core.metrics import Metrics
from src.assembler.instruction import Instruction


class PipelineState:
    """
    Holds the instruction currently occupying each of the five
    classic pipeline stages (IF, ID, EX, MEM, WB).
    Single-cycle and multi-cycle processors leave most slots None.
    """

    STAGES = ("IF", "ID", "EX", "MEM", "WB")

    def __init__(self):
        self.IF:  Optional[Instruction] = None
        self.ID:  Optional[Instruction] = None
        self.EX:  Optional[Instruction] = None
        self.MEM: Optional[Instruction] = None
        self.WB:  Optional[Instruction] = None

    def snapshot(self) -> dict[str, Optional[str]]:
        """Return stage -> mnemonic mapping (None if stage is empty)."""
        return {
            "IF":  self.IF.mnemonic  if self.IF  else None,
            "ID":  self.ID.mnemonic  if self.ID  else None,
            "EX":  self.EX.mnemonic  if self.EX  else None,
            "MEM": self.MEM.mnemonic if self.MEM else None,
            "WB":  self.WB.mnemonic  if self.WB  else None,
        }

    def clear(self) -> None:
        self.IF = self.ID = self.EX = self.MEM = self.WB = None


class BaseProcessor(ABC):
    """
    Abstract base class for all processor models (single-cycle,
    multi-cycle, pipelined with stalls, pipelined with forwarding).

    Concrete subclasses implement step() and run().
    The base class owns the shared hardware state:
      - register file
      - data memory
      - program counter (PC)
      - pipeline stage tracker
      - execution metrics
    """

    def __init__(self, processor_type: str):
        self.processor_type:  str           = processor_type
        self.registers:       RegisterFile  = RegisterFile()
        self.memory:          DataMemory    = DataMemory()
        self.metrics:         Metrics       = Metrics(processor_type)
        self.pc:              int           = 0
        self.pipeline:        PipelineState = PipelineState()
        self.program:         List[Instruction] = []
        self._running:        bool          = False

    # ------------------------------------------------------------------
    # Program loading
    # ------------------------------------------------------------------
    def load_program(self, instructions: List[Instruction]) -> None:
        self.program = list(instructions)
        self.reset()

    # ------------------------------------------------------------------
    # Fetch helper
    # ------------------------------------------------------------------
    def fetch(self) -> Optional[Instruction]:
        """Return the instruction at the current PC, or None if past end."""
        idx = self.pc >> 2  # byte address / 4
        return self.program[idx] if 0 <= idx < len(self.program) else None

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def reset(self) -> None:
        self.pc = 0
        self.registers.reset()
        self.memory.reset()
        self.metrics.reset()
        self.pipeline.clear()
        self._running = False

    # ------------------------------------------------------------------
    # Termination check
    # ------------------------------------------------------------------
    def is_done(self) -> bool:
        return (self.pc >> 2) >= len(self.program)

    # ------------------------------------------------------------------
    # State snapshot (used by UI layer)
    # ------------------------------------------------------------------
    def state_snapshot(self) -> dict:
        """
        Return a complete, serialisable view of the processor state.
        The UI reads this after every cycle to refresh all panels.
        """
        return {
            "processor_type": self.processor_type,
            "pc":             self.pc,
            "cycle":          self.metrics.cycles,
            "elapsed_time":   self.metrics.elapsed_time,
            "registers":      self.registers.snapshot(),
            "memory":         self.memory.snapshot(),
            "pipeline":       self.pipeline.snapshot(),
            "metrics":        self.metrics.summary(),
        }

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------
    @abstractmethod
    def step(self) -> bool:
        """
        Execute one processor cycle.
        Returns True while the program is still running, False when done.
        """
        ...

    @abstractmethod
    def run(self) -> None:
        """Execute the full program until completion."""
        ...
