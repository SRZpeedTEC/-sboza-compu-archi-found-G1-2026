from src.assembler import ControlSignals, Instruction
from src.core.metrics import Metrics


""" ProcessorSnapshot is a class that captures the state of the processor at a given point in time.
 It includes the program counter (PC), the current metrics, and the control signals. 
 This snapshot can be used for debugging, visualization, or any other purpose where you want 
 to inspect the state of the processor without affecting its execution."""

class ProcessorSnapshot:

    def __init__(self, pc: int, metrics: Metrics, control_signals: ControlSignals) -> None:
        self.pc = pc
        self.metrics = metrics
        self.control_signals = control_signals

    def update_pc(self, new_pc: int):
        self.pc = new_pc

    def update_metrics(self, new_metrics: Metrics):
        self.metrics = new_metrics

    def update_control_signals(self, new_control_signals: ControlSignals):
        self.control_signals = new_control_signals

    
    def get_snapshot(self):
        return {
            'pc': self.pc,
            'metrics': self.metrics.get_metrics(),
            'control_signals': self.control_signals.get_snapshot()
        }
    

        
