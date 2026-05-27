"""Las cinco etapas del pipeline RISC-V.

Cada funcion recibe el registro de entrada de su etapa y devuelve el
registro de salida. Ninguna etapa muta los registros en medio de una etapa. 
El motor las llama y decide que hacer con los valores devueltos
"""

from src.pipeline.pipeline_registers import IF_ID, ID_EX, EX_MEM, MEM_WB



# IF — Instruction Fetch
def stage_fetch(pc: int, instruction_memory) -> IF_ID:
    """Lee la instruccion en 'pc' y la empaqueta en IF_ID."""
    try:
        raw = instruction_memory.fetch(pc)
        return IF_ID(instruction=raw, pc=pc)
    except IndexError:
        return IF_ID(instruction=None, pc=pc)


# ID — Instruction Decode / Register Read
def stage_decode(if_id: IF_ID, register_bank, decoder, control_unit) -> ID_EX:
    """Decodifica IF_ID y lee los operandos del banco de registros."""
    if if_id.instruction is None:
        return ID_EX()   # burbuja: todos los campos en su valor por defecto

    instr = decoder.decode(if_id.instruction)
    ctrl = control_unit.generate_control_signals(instr)

    a = register_bank.read(instr.rs1) if instr.rs1 is not None else 0
    b = register_bank.read(instr.rs2) if instr.rs2 is not None else 0

    return ID_EX(
        instruction=instr,
        control=ctrl,
        a=a,
        b=b,
        rs1=instr.rs1,
        rs2=instr.rs2,
        rd=instr.rd,
        imm=instr.imm if instr.imm is not None else 0,
        pc=if_id.pc,
    )


# EX — Execute
def stage_execute(id_ex: ID_EX, alu) -> tuple[EX_MEM, bool, int]:
    """Opera la ALU y decide si un salto es tomado.

    Retorna (EX_MEM, branch_taken, branch_target).
    branch_taken=True implica que el motor debe limpiar IF_ID e ID_EX y
    redirigir el PC a branch_target.
    """
    if id_ex.instruction is None or id_ex.control is None:
        return EX_MEM(), False, 0

    opcode = id_ex.instruction.opcode
    ctrl = id_ex.control
    branch_taken = False
    branch_target = 0
    result = 0

    if opcode in {"add", "sub", "and", "or", "xor"}:
        result = alu.execute(ctrl.alu_control, id_ex.a, id_ex.b)

    elif opcode == "addi":
        result = alu.execute(ctrl.alu_control, id_ex.a, id_ex.imm)

    elif opcode in {"lw", "sw"}:
        result = alu.execute(ctrl.alu_control, id_ex.a, id_ex.imm)

    elif opcode in {"beq", "bne"}:
        diff = alu.execute("SUB", id_ex.a, id_ex.b)
        result = diff
        condition_met = (diff == 0) if opcode == "beq" else (diff != 0)
        if condition_met:
            branch_taken = True
            branch_target = id_ex.imm

    return (
        EX_MEM(
            instruction=id_ex.instruction,
            control=ctrl,
            alu_result=result,
            b=id_ex.b,
            rd=id_ex.rd,
            pc=id_ex.pc,
        ),
        branch_taken,
        branch_target,
    )



# MEM — Memory Access
def stage_memory(ex_mem: EX_MEM, memory) -> MEM_WB:
    """Accede a la memoria de datos (load o store)."""
    if ex_mem.instruction is None or ex_mem.control is None:
        return MEM_WB()

    mem_data = 0
    opcode = ex_mem.instruction.opcode

    if opcode == "lw":
        mem_data = memory.load_word(ex_mem.alu_result)
    elif opcode == "sw":
        memory.store_word(ex_mem.alu_result, ex_mem.b)

    return MEM_WB(
        instruction=ex_mem.instruction,
        control=ex_mem.control,
        alu_result=ex_mem.alu_result,
        mem_data=mem_data,
        rd=ex_mem.rd,
        pc=ex_mem.pc,
    )


# WB — Write Back
def stage_writeback(mem_wb: MEM_WB, register_bank) -> None:
    """Escribe el resultado en el banco de registros si la instruccion lo requiere."""
    if mem_wb.instruction is None or mem_wb.control is None:
        return
    if not mem_wb.control.reg_write or mem_wb.rd is None:
        return

    opcode = mem_wb.instruction.opcode
    value = mem_wb.mem_data if opcode == "lw" else mem_wb.alu_result
    register_bank.write(mem_wb.rd, value)
