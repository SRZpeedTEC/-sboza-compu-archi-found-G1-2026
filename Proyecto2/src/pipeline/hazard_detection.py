"""Deteccion de hazards de datos para pipelines de cinco etapas.

El pipeline maneja dependencias RAW (Read-After-Write). En el modelo con stalls
se congela IF/ID y se inserta una burbuja en ID/EX hasta que el productor pueda
escribir. En el modelo con forwarding solo se necesita stall para load-use,
porque el dato de memoria no esta disponible a tiempo para EX.
"""

from src.assembler import Instruction
from src.pipeline.pipeline_registers import EX_MEM, ID_EX, IF_ID


def detect_data_hazard(
    if_id: IF_ID,
    id_ex: ID_EX,
    ex_mem: EX_MEM,
    decoder,
) -> bool:
    """Detecta RAW que requiere stall en pipeline sin forwarding.

    IF/ID contiene la instruccion consumidora. ID/EX y EX/MEM contienen
    productores que aun no han llegado a WB, por eso sus destinos se comparan
    contra rs1/rs2 de la consumidora.
    """
    consumer = _decode_if_needed(if_id.instruction, decoder)

    if consumer is None:
        return False

    src_regs = _source_registers(consumer)

    if not src_regs:
        return False

    if _writes_register(id_ex) and id_ex.rd in src_regs:
        return True

    if _writes_register(ex_mem) and ex_mem.rd in src_regs:
        return True

    return False


def detect_load_use_hazard(if_id: IF_ID, id_ex: ID_EX, decoder) -> bool:
    """Detecta el caso load-use que forwarding no puede resolver.

    Si un lw esta en ID/EX, el dato aparece hasta MEM. La instruccion en IF/ID
    que lo usa en el ciclo siguiente no puede recibirlo a tiempo para EX, por
    eso se congela un ciclo aun en el pipeline con forwarding.
    """
    consumer = _decode_if_needed(if_id.instruction, decoder)

    if consumer is None or id_ex.instruction is None or id_ex.control is None:
        return False

    if not id_ex.control.mem_read or id_ex.rd in (None, "x0"):
        return False

    return id_ex.rd in _source_registers(consumer)


def _decode_if_needed(instruction, decoder) -> Instruction | None:
    """IF/ID guarda texto crudo; para hazards se necesitan rs1 y rs2."""
    if instruction is None:
        return None

    if isinstance(instruction, Instruction):
        return instruction

    if isinstance(instruction, str):
        try:
            return decoder.decode(instruction)
        except Exception:
            # Una instruccion invalida no debe romper la deteccion de hazards;
            # el parser/decoder principal reporta el error en el flujo normal.
            return None

    return None


def _source_registers(instruction: Instruction) -> set[str]:
    """Devuelve registros fuente reales; x0 se ignora porque nunca cambia."""
    return {
        reg for reg in (instruction.rs1, instruction.rs2)
        if reg is not None and reg != "x0"
    }


def _writes_register(pipe_reg) -> bool:
    """Indica si una etapa pendiente escribira un registro arquitectonico."""
    return (
        pipe_reg.control is not None
        and pipe_reg.control.reg_write
        and pipe_reg.rd not in (None, "x0")
    )
