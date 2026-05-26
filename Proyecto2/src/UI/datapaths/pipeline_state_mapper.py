"""Mapper puro del datapath del Pipeline (Forwarding / Stalls).

Espeja a ``single_cycle_state_mapper``: traduce el ``snapshot`` a un dict
autonomo que la View consume sin volver a leer el snapshot. Sin Qt, sin estado
y None-safe (acepta ``snapshot=None``).

El datapath se dibuja a nivel de componente (Unidad de Control, MUXes, ALU,
memorias, banco de registros, inmediato), igual que el Uniciclo, pero repartido
en las cinco etapas con sus cuatro registros de pipeline y las dos unidades de
control de riesgos. Las senales de control de cada etapa viajan dentro de su
registro de pipeline (``*.control``).
"""

# Componentes del datapath (orden de dibujo / lectura).
MODULE_ORDER = [
    "control_unit",
    "pc_src_mux",
    "pc",
    "instruction_memory",
    "register_file",
    "immediate",
    "alu_src_mux",
    "alu",
    "data_memory",
    "result_src_mux",
]

MODULE_TITLES = {
    "control_unit": "ControlUnit",
    "pc_src_mux": "PCSrc MUX",
    "pc": "PC",
    "instruction_memory": "Instruction Memory",
    "register_file": "Register File",
    "immediate": "Immediate",
    "alu_src_mux": "ALUSrc MUX",
    "alu": "ALU",
    "data_memory": "Data Memory",
    "result_src_mux": "ResultSrc MUX",
}

# Etapa a la que pertenece cada componente (para el resaltado de "activo").
MODULE_STAGE = {
    "pc_src_mux": "if",
    "pc": "if",
    "instruction_memory": "if",
    "control_unit": "id",
    "register_file": "id",
    "immediate": "id",
    "alu_src_mux": "ex",
    "alu": "ex",
    "data_memory": "mem",
    "result_src_mux": "wb",
}

STAGE_ORDER = ["if", "id", "ex", "mem", "wb"]
STAGE_TITLES = {"if": "IF", "id": "ID", "ex": "EX", "mem": "MEM", "wb": "WB"}

PIPE_REGISTER_ORDER = ["if_id", "id_ex", "ex_mem", "mem_wb"]
PIPE_REGISTER_TITLES = {
    "if_id": "IF/ID",
    "id_ex": "ID/EX",
    "ex_mem": "EX/MEM",
    "mem_wb": "MEM/WB",
}

UNIT_ORDER = ["risk_unit"]

NO_FORWARD = "ID/EX"

R_TYPE_OPCODES = {"add", "sub", "and", "or", "xor"}
BRANCH_OPCODES = {"beq", "bne"}


def map_pipeline_datapath_state(snapshot) -> dict:
    if_id = _get(snapshot, "if_id")
    id_ex = _get(snapshot, "id_ex")
    ex_mem = _get(snapshot, "ex_mem")
    mem_wb = _get(snapshot, "mem_wb")

    # Una etapa esta "activa" si el registro que la representa lleva una
    # instruccion real (instruction is not None). None = burbuja/NOP.
    if_id_present = _has_instruction(if_id)
    id_ex_present = _has_instruction(id_ex)
    ex_mem_present = _has_instruction(ex_mem)
    mem_wb_present = _has_instruction(mem_wb)

    active_stages: set[str] = set()
    if if_id_present:
        active_stages.add("if")
    if id_ex_present:
        active_stages.add("id")
    if ex_mem_present:
        active_stages.add("ex")
    if mem_wb_present:
        active_stages.add("mem")
        active_stages.add("wb")  # el writeback consume MEM/WB

    # Componentes activos: cada uno hereda la actividad de su etapa. El banco de
    # registros se enciende tambien en WB (escritura del writeback).
    active_modules = {
        key for key, stage in MODULE_STAGE.items() if stage in active_stages
    }
    if "wb" in active_stages:
        active_modules.add("register_file")

    forward_a = _value(_get(snapshot, "forward_a", NO_FORWARD)) or NO_FORWARD
    forward_b = _value(_get(snapshot, "forward_b", NO_FORWARD)) or NO_FORWARD
    stalled = bool(_get(snapshot, "stalled", False))
    flushed = bool(_get(snapshot, "flushed", False))

    id_opcode = _opcode(id_ex)

    modules = {
        "control_unit": _module(
            "control_unit",
            [
                ("opcode", id_opcode),
                ("RegWrite", _bool_value(_control(id_ex, "reg_write"))),
                ("MemRead", _bool_value(_control(id_ex, "mem_read"))),
                ("MemWrite", _bool_value(_control(id_ex, "mem_write"))),
                ("ALUSrc", _control(id_ex, "alu_src")),
                ("ResultSrc", _control(id_ex, "result_src")),
                ("Branch", _bool_value(_control(id_ex, "branch"))),
                ("ALUCtrl", _control(id_ex, "alu_control")),
            ],
            active_modules,
        ),
        "pc_src_mux": _module(
            "pc_src_mux",
            [("PCSrc", "branch" if flushed else "pc_plus_4")],
            active_modules,
        ),
        "pc": _module(
            "pc",
            [
                ("PC", _get(if_id, "pc") if if_id_present else _get(snapshot, "pc")),
                ("PC+4", _pc_plus_4(if_id, snapshot, if_id_present)),
            ],
            active_modules,
        ),
        "instruction_memory": _module(
            "instruction_memory",
            [("Instr", _get(if_id, "instruction"))],
            active_modules,
        ),
        "register_file": _module(
            "register_file",
            [
                ("rs1", _get(id_ex, "rs1")),
                ("rs2", _get(id_ex, "rs2")),
                ("rd", _get(mem_wb, "rd")),
                ("WB", _writeback_value(mem_wb)),
                ("RegWrite", _bool_value(_control(mem_wb, "reg_write"))),
            ],
            active_modules,
        ),
        "immediate": _module(
            "immediate",
            [
                ("imm", _get(id_ex, "imm")),
                ("ImmSrc", _imm_src(id_opcode)),
            ],
            active_modules,
        ),
        "alu_src_mux": _module(
            "alu_src_mux",
            [("ALUSrc", _control(ex_mem, "alu_src"))],
            active_modules,
        ),
        "alu": _module(
            "alu",
            [
                ("ALUCtrl", _control(ex_mem, "alu_control")),
                ("Result", _get(ex_mem, "alu_result")),
                ("rd", _get(ex_mem, "rd")),
                ("OpA", forward_a),
                ("OpB", forward_b),
            ],
            active_modules,
        ),
        "data_memory": _module(
            "data_memory",
            [
                ("MemRead", _bool_value(_control(mem_wb, "mem_read"))),
                ("MemWrite", _bool_value(_control(mem_wb, "mem_write"))),
                ("Addr", _get(mem_wb, "alu_result")),
                ("ReadData", _get(mem_wb, "mem_data")),
            ],
            active_modules,
        ),
        "result_src_mux": _module(
            "result_src_mux",
            [("ResultSrc", _control(mem_wb, "result_src"))],
            active_modules,
        ),
    }

    pipe_registers = {
        "if_id": _pipe_register(
            "if_id",
            if_id_present,
            [
                ("instr", _get(if_id, "instruction")),
                ("pc", _get(if_id, "pc")),
            ],
        ),
        "id_ex": _pipe_register(
            "id_ex",
            id_ex_present,
            [
                ("op", _opcode(id_ex)),
                ("rs1", _get(id_ex, "rs1")),
                ("rs2", _get(id_ex, "rs2")),
                ("rd", _get(id_ex, "rd")),
                ("imm", _get(id_ex, "imm")),
                ("a", _get(id_ex, "a")),
                ("b", _get(id_ex, "b")),
                ("pc", _get(id_ex, "pc")),
            ],
        ),
        "ex_mem": _pipe_register(
            "ex_mem",
            ex_mem_present,
            [
                ("op", _opcode(ex_mem)),
                ("res", _get(ex_mem, "alu_result")),
                ("b", _get(ex_mem, "b")),
                ("rd", _get(ex_mem, "rd")),
            ],
        ),
        "mem_wb": _pipe_register(
            "mem_wb",
            mem_wb_present,
            [
                ("op", _opcode(mem_wb)),
                ("res", _get(mem_wb, "alu_result")),
                ("data", _get(mem_wb, "mem_data")),
                ("rd", _get(mem_wb, "rd")),
            ],
        ),
    }

    forwarding_active = (forward_a != NO_FORWARD) or (forward_b != NO_FORWARD)
    hazard_active = stalled or flushed or forwarding_active

    units = {
        "risk_unit": {
            "title": "Hazard / Forwarding Unit",
            "lines": [
                f"Stall: {_bool_value(stalled)}",
                f"Flush: {_bool_value(flushed)}",
                f"Cause: {_hazard_cause(stalled, flushed)}",
                f"ForwardA: {forward_a}",
                f"ForwardB: {forward_b}",
            ],
            "active": hazard_active or forwarding_active,
        },
    }

    stage_instructions = {
        "IF": _value(_get(if_id, "instruction")) if if_id_present else "-",
        "ID": _instruction_text(_get(id_ex, "instruction")) if id_ex_present else "-",
        "EX": (
            _instruction_text(_get(ex_mem, "instruction"))
            if ex_mem_present
            else ("STALL" if stalled else "-")
        ),
        "MEM": _instruction_text(_get(mem_wb, "instruction")) if mem_wb_present else "-",
        "WB": _instruction_text(_get(mem_wb, "instruction")) if mem_wb_present else "-",
    }

    return {
        "active_stages": active_stages,
        "active_modules": active_modules,
        "modules": modules,
        "pipe_registers": pipe_registers,
        "units": units,
        "stage_instructions": stage_instructions,
        "forward_a": forward_a,
        "forward_b": forward_b,
        "stalled": stalled,
        "flushed": flushed,
    }


def _module(key: str, pairs: list[tuple[str, object]], active_modules: set[str]) -> dict:
    """Modulo: si el componente no esta activo, todas las lineas en ``-``."""
    active = key in active_modules
    lines = []
    for label, raw_value in pairs:
        value = _value(raw_value) if active else "-"
        lines.append(f"{label}: {value}")
    return {"title": MODULE_TITLES[key], "lines": lines}


def _pipe_register(key: str, present: bool, pairs: list[tuple[str, object]]) -> dict:
    """Barrera de registro: lineas en ``-`` cuando no transporta instruccion."""
    lines = []
    for label, raw_value in pairs:
        value = _value(raw_value) if present else "-"
        lines.append(f"{label}: {value}")
    return {"title": PIPE_REGISTER_TITLES[key], "lines": lines, "present": present}


def _has_instruction(register) -> bool:
    return register is not None and _get(register, "instruction") is not None


def _opcode(register):
    return _get(_get(register, "instruction"), "opcode")


def _control(register, field: str):
    """Lee una senal de control que viaja dentro del registro de pipeline."""
    return _get(_get(register, "control"), field)


def _pc_plus_4(if_id, snapshot, present):
    pc = _get(if_id, "pc") if present else _get(snapshot, "pc")
    if isinstance(pc, int):
        return pc + 4
    return None


def _writeback_value(mem_wb):
    """Valor escrito en WB: dato de memoria para LW, resultado de ALU si no."""
    if mem_wb is None:
        return None
    if _opcode(mem_wb) == "lw":
        return _get(mem_wb, "mem_data")
    return _get(mem_wb, "alu_result")


def _imm_src(opcode: str) -> str:
    if opcode in {"addi", "lw"}:
        return "I-type"
    if opcode == "sw":
        return "S-type"
    if opcode in BRANCH_OPCODES:
        return "B-type"
    return "-"


def _hazard_cause(stalled: bool, flushed: bool) -> str:
    if stalled:
        return "load-use"
    if flushed:
        return "branch"
    return "-"


def _instruction_text(instruction) -> str:
    if instruction is None:
        return "-"
    text = _get(instruction, "complete_instruction")
    if text:
        return str(text)
    opcode = _get(instruction, "opcode")
    if opcode:
        return str(opcode)
    return "-"


def _bool_value(value) -> str:
    if value is None:
        return "-"
    return "True" if bool(value) else "False"


def _value(value) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def _get(source, name: str, default=None):
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)
