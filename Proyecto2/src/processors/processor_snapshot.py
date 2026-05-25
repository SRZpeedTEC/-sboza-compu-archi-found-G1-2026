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

        # UI UNICICLO
        current_instruction=None,
        single_cycle_trace=None,
        multi_cycle_active_stage=None,
        multi_cycle_old_pc=None,
        multi_cycle_branch_taken=None,

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

        self.current_instruction = current_instruction
        self.single_cycle_trace = single_cycle_trace or {}
        self.multi_cycle_active_stage = multi_cycle_active_stage
        self.multi_cycle_old_pc = multi_cycle_old_pc
        self.multi_cycle_branch_taken = multi_cycle_branch_taken

    def get_snapshot(self):

        return {

            "pc": self.pc,

            "metrics":
            self.metrics.get_metrics(),

            "control_signals":
            self.control_signals.get_snapshot(),

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
            # Los atributos (self.if_id, ...) siguen siendo los dataclasses crudos
            # que consume la UI; aqui se serializan a dicts None-safe para los tests.
            "if_id":
            self.if_id.to_dict() if self.if_id is not None else None,

            "id_ex":
            self.id_ex.to_dict() if self.id_ex is not None else None,

            "ex_mem":
            self.ex_mem.to_dict() if self.ex_mem is not None else None,

            "mem_wb":
            self.mem_wb.to_dict() if self.mem_wb is not None else None,

            "stalled":
            self.stalled,

            "flushed":
            self.flushed,

            "forward_a":
            self.forward_a,

            "forward_b":
            self.forward_b,

            "current_instruction":
            self.current_instruction,

            "single_cycle_trace":
            self.single_cycle_trace,

            "multi_cycle_active_stage":
            self.multi_cycle_active_stage,

            "multi_cycle_old_pc":
            self.multi_cycle_old_pc,

            "multi_cycle_branch_taken":
            self.multi_cycle_branch_taken
        }
