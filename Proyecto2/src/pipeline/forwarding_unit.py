"""Unidad de adelantamiento para el pipeline de cinco etapas.

La unidad compara los registros fuente que entran a EX contra los destinos que
estan en MEM y WB. Si encuentra una coincidencia, reemplaza el operando leido
en ID por el valor mas reciente disponible en el pipeline.
"""

from dataclasses import dataclass

from src.pipeline.pipeline_registers import ID_EX, EX_MEM, MEM_WB


@dataclass(frozen=True)
class ForwardingDecision:
    a: int
    b: int
    forward_a: str = "ID/EX"
    forward_b: str = "ID/EX"


def resolve_forwarding(id_ex: ID_EX, ex_mem: EX_MEM, mem_wb: MEM_WB) -> ForwardingDecision:
    """Retorna los operandos que debe usar EX y de donde vinieron."""
    if id_ex.instruction is None or id_ex.control is None:
        return ForwardingDecision(id_ex.a, id_ex.b)

    a = id_ex.a
    b = id_ex.b
    forward_a = "ID/EX"
    forward_b = "ID/EX"

    if _can_forward_from_ex_mem(ex_mem):
        if id_ex.rs1 == ex_mem.rd:
            a = ex_mem.alu_result
            forward_a = "EX/MEM"
        if id_ex.rs2 == ex_mem.rd:
            b = ex_mem.alu_result
            forward_b = "EX/MEM"

    mem_wb_value = _writeback_value(mem_wb)
    if mem_wb_value is not None and _can_forward_from_mem_wb(mem_wb):
        if forward_a == "ID/EX" and id_ex.rs1 == mem_wb.rd:
            a = mem_wb_value
            forward_a = "MEM/WB"
        if forward_b == "ID/EX" and id_ex.rs2 == mem_wb.rd:
            b = mem_wb_value
            forward_b = "MEM/WB"

    return ForwardingDecision(a=a, b=b, forward_a=forward_a, forward_b=forward_b)


def _can_forward_from_ex_mem(ex_mem: EX_MEM) -> bool:
    if ex_mem.instruction is None or ex_mem.control is None:
        return False
    if not ex_mem.control.reg_write or ex_mem.rd in (None, "x0"):
        return False
    return ex_mem.instruction.opcode != "lw"


def _can_forward_from_mem_wb(mem_wb: MEM_WB) -> bool:
    if mem_wb.instruction is None or mem_wb.control is None:
        return False
    return mem_wb.control.reg_write and mem_wb.rd not in (None, "x0")


def _writeback_value(mem_wb: MEM_WB) -> int | None:
    if not _can_forward_from_mem_wb(mem_wb):
        return None
    if mem_wb.instruction.opcode == "lw":
        return mem_wb.mem_data
    return mem_wb.alu_result
