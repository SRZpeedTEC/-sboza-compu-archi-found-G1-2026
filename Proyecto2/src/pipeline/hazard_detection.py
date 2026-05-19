"""Deteccion de hazards de datos para pipeline con stall.

Las dependencias RAW (Read-After-Write) entre una instruccion
en ID y una instruccion que todavia no ha completado WB debe resuelven
congelando el pipeline con un stall. El stall se detecta comparando los registros
destino de las instrucciones en EX y MEM contra los registros fuente de la
instruccion actualmente en ID.
"""

from src.pipeline.pipeline_registers import IF_ID, ID_EX, EX_MEM


def detect_data_hazard(
    if_id: IF_ID,
    id_ex: ID_EX,
    ex_mem: EX_MEM,
    decoder,
) -> bool:
    """Retorna True si hay un hazard RAW que requiere insertar un stall.

    Condicion: la instruccion en IF_ID lee un registro (rs1 o rs2) que sera
    escrito por la instruccion en ID_EX o EX_MEM, las cuales aun no han
    completado WB"""
    if if_id.instruction is None:
        return False

    # Extraer registros fuente de la instruccion que esta en ID
    try:
        instr = decoder.decode(if_id.instruction)
    except ValueError:
        return False

    src_regs = {
        r for r in (instr.rs1, instr.rs2)
        if r is not None and r != "x0"
    }
    if not src_regs:
        return False

    # Instruccion en EX todavia no ha escrito → hazard si coincide rd
    if (
        id_ex.control is not None
        and id_ex.control.reg_write
        and id_ex.rd is not None
        and id_ex.rd != "x0"
        and id_ex.rd in src_regs
    ):
        return True

    # Instruccion en MEM todavia no ha escrito → hazard si coincide rd
    if (
        ex_mem.control is not None
        and ex_mem.control.reg_write
        and ex_mem.rd is not None
        and ex_mem.rd != "x0"
        and ex_mem.rd in src_regs
    ):
        return True

    return False
