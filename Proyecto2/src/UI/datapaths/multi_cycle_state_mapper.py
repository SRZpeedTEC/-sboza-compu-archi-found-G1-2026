from dataclasses import asdict, is_dataclass


MODULE_ORDER = [
    "control_unit",
    "pc",
    "adr_src_mux",
    "memory",
    "ir",
    "register_file",
    "ab_register",
    "immediate",
    "alu_src_a_mux",
    "alu_src_b_mux",
    "alu",
    "alu_out",
    "mdr",
    "result_src_mux",
]

MODULE_TITLES = {
    "control_unit": "ControlUnit",
    "pc": "PC",
    "adr_src_mux": "AdrSrc MUX",
    "memory": "Instruction/Data Memory",
    "ir": "IR",
    "register_file": "Register File",
    "ab_register": "A/B",
    "immediate": "Immediate",
    "alu_src_a_mux": "ALUSrcA MUX",
    "alu_src_b_mux": "ALUSrcB MUX",
    "alu": "ALU",
    "alu_out": "ALUOut",
    "mdr": "MDR",
    "result_src_mux": "ResultSrc MUX",
}

R_TYPE_OPCODES = {"add", "sub", "and", "or", "xor"}
MEMORY_OPCODES = {"lw", "sw"}
BRANCH_OPCODES = {"beq", "bne"}

STAGE_MAP = {
    "FETCH": "IF",
    "DECODE": "ID",
    "EXECUTE": "EX",
    "MEMORY": "MEM",
    "WRITEBACK": "WB",
    "IF": "IF",
    "ID": "ID",
    "EX": "EX",
    "MEM": "MEM",
    "WB": "WB",
}


def map_multi_cycle_datapath_state(snapshot) -> dict:
    """Convierte el snapshot multiciclo en estado visual por etapa.

    Cada componente se activa según la etapa FSM actual y el opcode; si el
    snapshot está vacío se devuelve un estado neutral para el reset de la vista.
    """
    neutral = _is_neutral_snapshot(snapshot)
    active_stage = "-" if neutral else _active_stage(snapshot)
    instruction = _get(snapshot, "current_instruction")
    opcode = _value(_get(instruction, "opcode"))
    control = _control_snapshot(_get(snapshot, "control_signals"))
    active_modules = set() if neutral else _active_modules(active_stage, opcode)

    modules = {
        "control_unit": _module(
            "control_unit",
            [
                ("stage", active_stage),
                ("PCWrite", control.get("pc_write")),
                ("AdrSrc", control.get("adr_src")),
                ("MemWrite", control.get("mem_write")),
                ("IRWrite", control.get("ir_write")),
                ("ResultSrc", control.get("result_src")),
                ("ALUCtrl", control.get("alu_control")),
                ("ALUSrcA", control.get("alu_src_a")),
                ("ALUSrcB", control.get("alu_src_b")),
                ("ImmSrc", _imm_src(opcode)),
                ("RegWrite", control.get("reg_write")),
                ("Branch", control.get("branch")),
            ],
            active_modules,
        ),
        "pc": _module(
            "pc",
            [
                ("PC", _pc_value(snapshot, active_stage)),
                ("Next", _next_pc_value(snapshot, active_stage)),
                ("PCWrite", control.get("pc_write")),
            ],
            active_modules,
        ),
        "adr_src_mux": _module(
            "adr_src_mux",
            [
                ("AdrSrc", control.get("adr_src")),
            ],
            active_modules,
        ),
        "memory": _module(
            "memory",
            [
                ("Op", _memory_operation(active_stage, opcode)),
                ("Addr", _memory_address(snapshot, active_stage)),
                ("ReadData", _memory_read_data(snapshot, active_stage, opcode)),
                ("WriteData", _memory_write_data(snapshot, active_stage, opcode)),
                ("MemWrite", control.get("mem_write")),
            ],
            active_modules,
        ),
        "ir": _module(
            "ir",
            [
                ("Instr", _value(_get(snapshot, "ir"))),
                ("IRWrite", control.get("ir_write")),
            ],
            active_modules,
        ),
        "register_file": _module(
            "register_file",
            [
                ("rs1", _register_line(instruction, snapshot, "rs1", "a")),
                ("rs2", _register_line(instruction, snapshot, "rs2", "b")),
                ("rd", _get(instruction, "rd")),
                ("WB", _writeback_value(snapshot, opcode)),
                ("RegWrite", control.get("reg_write")),
            ],
            active_modules,
        ),
        "ab_register": _module(
            "ab_register",
            [
                ("A", _get(snapshot, "a")),
                ("B", _get(snapshot, "b")),
                ("CLK", "ID"),
            ],
            active_modules,
        ),
        "immediate": _module(
            "immediate",
            [
                ("imm", _get(instruction, "imm")),
                ("ImmSrc", _imm_src(opcode)),
            ],
            active_modules,
        ),
        "alu_src_a_mux": _module(
            "alu_src_a_mux",
            [
                ("ALUSrcA", control.get("alu_src_a")),
            ],
            active_modules,
        ),
        "alu_src_b_mux": _module(
            "alu_src_b_mux",
            [
                ("ALUSrcB", control.get("alu_src_b")),
            ],
            active_modules,
        ),
        "alu": _module(
            "alu",
            [
                ("Op1", _alu_operand_a(snapshot, active_stage)),
                ("Op2", _alu_operand_b(instruction, snapshot, active_stage, opcode)),
                ("ALUCtrl", control.get("alu_control")),
                ("Result", _alu_result(snapshot, active_stage, opcode)),
                ("Branch", _branch_taken(snapshot, active_stage, opcode)),
            ],
            active_modules,
        ),
        "alu_out": _module(
            "alu_out",
            [("ALUOut", _get(snapshot, "alu_out")), ("CLK", "EX")],
            active_modules,
        ),
        "mdr": _module(
            "mdr",
            [("Data", _get(snapshot, "mdr")), ("CLK", "MEM")],
            active_modules,
        ),
        "result_src_mux": _module(
            "result_src_mux",
            [
                ("ResultSrc", control.get("result_src")),
            ],
            active_modules,
        ),
    }

    return {
        "active_stage": active_stage,
        "active_modules": active_modules,
        "modules": modules,
        "stage_states": {
            stage: stage == active_stage
            for stage in ["IF", "ID", "EX", "MEM", "WB"]
        },
    }


def _active_stage(snapshot) -> str:
    raw_stage = (
        _get(snapshot, "multi_cycle_active_stage")
        or _get(snapshot, "active_stage")
        or _get(snapshot, "current_stage")
        or _get(snapshot, "stage")
    )
    if raw_stage is None:
        return "-"
    return STAGE_MAP.get(str(raw_stage), "IF")


def _is_neutral_snapshot(snapshot) -> bool:
    if snapshot is None:
        return True

    metrics = _get(snapshot, "metrics")
    if metrics is not None and hasattr(metrics, "get_metrics"):
        cycles = metrics.get_metrics().get("cycles", 0)
        if cycles == 0 and _get(snapshot, "ir") is None:
            return True

    return False


def _active_modules(stage: str, opcode: str) -> set[str]:
    if stage == "IF":
        return {
            "control_unit",
            "pc",
            "adr_src_mux",
            "memory",
            "ir",
            "alu_src_a_mux",
            "alu_src_b_mux",
            "alu",
            "result_src_mux",
        }

    if stage == "ID":
        return {
            "control_unit",
            "ir",
            "register_file",
            "ab_register",
            "immediate",
        }

    if stage == "EX":
        modules = {
            "control_unit",
            "ab_register",
            "alu_src_a_mux",
            "alu_src_b_mux",
            "alu",
        }
        if opcode in R_TYPE_OPCODES or opcode in MEMORY_OPCODES or opcode == "addi":
            modules.add("alu_out")
        if opcode in MEMORY_OPCODES or opcode == "addi":
            modules.add("immediate")
        return modules

    if stage == "MEM":
        modules = {
            "control_unit",
            "alu_out",
            "adr_src_mux",
            "memory",
        }
        if opcode == "lw":
            modules.add("mdr")
        if opcode == "sw":
            modules.add("ab_register")
        return modules

    if stage == "WB":
        if opcode in {"sw", "beq", "bne"}:
            return {"control_unit"}

        modules = {
            "control_unit",
            "register_file",
            "result_src_mux",
        }
        modules.add("mdr" if opcode == "lw" else "alu_out")
        return modules

    return set()


def _module(key: str, pairs: list[tuple[str, object]], active_modules: set[str]) -> dict:
    active = key in active_modules
    lines = []

    for label, raw_value in pairs:
        value = _value(raw_value) if active else "-"
        lines.append(f"{label}: {value}")

    return {
        "title": MODULE_TITLES[key],
        "lines": lines,
    }


def _control_snapshot(control) -> dict:
    if control is None:
        return {}
    if isinstance(control, dict):
        return control
    if is_dataclass(control):
        return asdict(control)
    return {
        "reg_write": _get(control, "reg_write"),
        "mem_read": _get(control, "mem_read"),
        "mem_write": _get(control, "mem_write"),
        "alu_src": _get(control, "alu_src"),
        "result_src": _get(control, "result_src"),
        "pc_src": _get(control, "pc_src"),
        "branch": _get(control, "branch"),
        "branch_condition": _get(control, "branch_condition"),
        "alu_control": _get(control, "alu_control"),
        "pc_write": _get(control, "pc_write"),
        "adr_src": _get(control, "adr_src"),
        "ir_write": _get(control, "ir_write"),
        "alu_src_a": _get(control, "alu_src_a"),
        "alu_src_b": _get(control, "alu_src_b"),
    }


def _memory_operation(stage: str, opcode: str) -> str:
    if stage == "IF":
        return "fetch"
    if stage == "MEM" and opcode == "lw":
        return "load"
    if stage == "MEM" and opcode == "sw":
        return "store"
    return "inactive"


def _memory_address(snapshot, stage: str) -> object:
    if stage == "IF":
        return _pc_value(snapshot, stage)
    if stage == "MEM":
        return _get(snapshot, "alu_out")
    return None


def _memory_read_data(snapshot, stage: str, opcode: str) -> object:
    if stage == "IF":
        return _get(snapshot, "ir")
    if stage == "MEM" and opcode == "lw":
        return _get(snapshot, "mdr")
    return None


def _memory_write_data(snapshot, stage: str, opcode: str) -> object:
    if stage == "MEM" and opcode == "sw":
        return _get(snapshot, "b")
    return None


def _register_line(instruction, snapshot, register_key: str, value_key: str) -> str:
    register = _get(instruction, register_key)
    value = _get(snapshot, value_key)
    if register is None:
        return "-"
    return f"{register} = {_value(value)}"


def _writeback_value(snapshot, opcode: str) -> object:
    if opcode == "lw":
        return _get(snapshot, "mdr")
    if opcode in R_TYPE_OPCODES or opcode == "addi":
        return _get(snapshot, "alu_out")
    return None


def _alu_operand_a(snapshot, stage: str) -> str:
    if stage == "IF":
        return f"PC = {_value(_pc_value(snapshot, stage))}"
    if stage == "EX":
        return f"A = {_value(_get(snapshot, 'a'))}"
    return "-"


def _alu_operand_b(instruction, snapshot, stage: str, opcode: str) -> str:
    if stage == "IF":
        return "4"
    if stage == "EX" and opcode in R_TYPE_OPCODES | BRANCH_OPCODES:
        return f"B = {_value(_get(snapshot, 'b'))}"
    if stage == "EX" and (opcode in MEMORY_OPCODES or opcode == "addi"):
        return f"imm = {_value(_get(instruction, 'imm'))}"
    return "-"


def _alu_result(snapshot, stage: str, opcode: str) -> object:
    if stage == "IF":
        pc = _pc_value(snapshot, stage)
        if isinstance(pc, int):
            return pc + 4
        return None
    if stage == "EX":
        return _get(snapshot, "alu_out")
    return None


def _branch_taken(snapshot, stage: str, opcode: str) -> object:
    if stage == "EX" and opcode in BRANCH_OPCODES:
        return _get(snapshot, "multi_cycle_branch_taken")
    return None


def _imm_src(opcode: str) -> str:
    if opcode in {"addi", "lw"}:
        return "I-type"
    if opcode == "sw":
        return "S-type"
    if opcode in BRANCH_OPCODES:
        return "B-type"
    return "-"


def _pc_value(snapshot, stage: str) -> object:
    if stage == "IF":
        return _get(snapshot, "multi_cycle_old_pc", _get(snapshot, "pc"))
    return _get(snapshot, "pc")


def _next_pc_value(snapshot, stage: str) -> object:
    if stage == "IF":
        return _get(snapshot, "pc")
    return None


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
