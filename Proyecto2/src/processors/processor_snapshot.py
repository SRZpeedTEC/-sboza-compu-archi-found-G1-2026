from src.assembler import ControlSignals
from src.core.metrics import Metrics


""" ProcessorSnapshot is a class that captures the state of the processor at a given point in time.
 It includes the program counter (PC), the current metrics, and the control signals. 
 This snapshot can be used for debugging, visualization, or any other purpose where you want 
 to inspect the state of the processor without affecting its execution."""

class ProcessorSnapshot:

    def __init__(
        self,
        pc: int,
        metrics: Metrics,
        control_signals: ControlSignals,
        registers,
        memory,
        pipeline=None,

        # MULTICYCLE
        stage=None,
        ir=None,
        a=0,
        b=0,
        alu_out=0,
        mdr=0,

        # PIPELINE FORWARDING
        if_id=None,
        id_ex=None,
        ex_mem=None,
        mem_wb=None,

        stalled=False,
        flushed=False,

        forward_a="ID/EX",
        forward_b="ID/EX",

    ) -> None:

        self.pc = pc
        self.metrics = metrics
        self.control_signals = control_signals

        self.registers = registers.copy()
        self.memory = memory.copy()

        self.pipeline = pipeline or []

        # MULTICICLO
        self.stage = stage
        self.ir = ir
        self.a = a
        self.b = b
        self.alu_out = alu_out
        self.mdr = mdr

        # PIPELINE FORWARDING

        self.if_id = if_id
        self.id_ex = id_ex
        self.ex_mem = ex_mem
        self.mem_wb = mem_wb

        self.stalled = stalled
        self.flushed = flushed

        self.forward_a = forward_a
        self.forward_b = forward_b

    def get_snapshot(self):

        return {

            "pc": self.pc,

            "metrics":
            self.metrics.get_metrics(),

            # MULTICICLO
            "stage":
            self.stage,

            "ir":
            self.ir,

            "a":
            self.a,

            "b":
            self.b,

            "alu_out":
            self.alu_out,

            "mdr":
            self.mdr,

            # PIPELINE
            "if_id":
            self.if_id,

            "id_ex":
            self.id_ex,

            "ex_mem":
            self.ex_mem,

            "mem_wb":
            self.mem_wb,

            "stalled":
            self.stalled,

            "flushed":
            self.flushed,

            "forward_a":
            self.forward_a,

            "forward_b":
            self.forward_b
        }