"""Deteccion de hazards de datos para pipeline con stall.

Las dependencias RAW (Read-After-Write) entre una instruccion
en ID y una instruccion que todavia no ha completado WB debe resuelven
congelando el pipeline con un stall. El stall se detecta comparando los registros
destino de las instrucciones en EX y MEM contra los registros fuente de la
instruccion actualmente en ID.
"""

from src.pipeline.pipeline_registers import IF_ID, ID_EX, EX_MEM
from src.assembler import Instruction


def detect_data_hazard(
    if_id: IF_ID,
    id_ex: ID_EX,
    ex_mem: EX_MEM,
    decoder,
) -> bool:

    if if_id.instruction is None:
        return False

    consumer = if_id.instruction

    # Si viene como string se decodifica
    if isinstance(consumer, str):
        try:
            consumer = decoder.decode(consumer)
        except:
            return False

    # REGISTROS FUENTE
    src_regs = {
        reg for reg in (consumer.rs1, consumer.rs2)
        if reg is not None and reg != "x0"
    }

    if not src_regs:
        return False

    # HAZARD CON EX
    if (
        id_ex.control is not None
        and id_ex.control.reg_write
        and id_ex.rd is not None
        and id_ex.rd != "x0"
        and id_ex.rd in src_regs
    ):
        print("HAZARD DETECTED WITH EX:", id_ex.rd)
        return True

    # HAZARD CON MEM
    if (
        ex_mem.control is not None
        and ex_mem.control.reg_write
        and ex_mem.rd is not None
        and ex_mem.rd != "x0"
        and ex_mem.rd in src_regs
    ):
        print("HAZARD DETECTED WITH MEM:", ex_mem.rd)
        return True

    return False


def detect_load_use_hazard(if_id, id_ex, decoder) -> bool:

    # Nada en IF/ID
    if if_id.instruction is None:
        return False

    # Nada en ID/EX
    if id_ex.instruction is None:
        return False

    # Sin señales de control
    if id_ex.control is None:
        return False

    # Debe ser un load
    if not id_ex.control.mem_read:
        return False

    # Registro destino del lw
    producer_rd = id_ex.rd

    if producer_rd is None or producer_rd == "x0":
        return False

    consumer = if_id.instruction

    # IF/ID transporta el string crudo: se decodifica para leer sus fuentes,
    # igual que hace detect_data_hazard.
    if isinstance(consumer, str):
        try:
            consumer = decoder.decode(consumer)
        except Exception:
            return False

    rs1 = getattr(consumer, "rs1", None)
    rs2 = getattr(consumer, "rs2", None)

    if rs1 == producer_rd:
        return True

    if rs2 == producer_rd:
        return True

    return False
