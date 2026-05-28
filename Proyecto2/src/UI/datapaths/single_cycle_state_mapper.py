from dataclasses import asdict, is_dataclass

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

R_TYPE_OPCODES = {"add", "sub", "and", "or", "xor"}
BRANCH_OPCODES = {"beq", "bne"}


def map_single_cycle_datapath_state(snapshot) -> dict:
    """Traduce el snapshot uniciclo a datos simples para la vista Qt.

    El mapper es tolerante a ``None`` y a campos faltantes para que la UI pueda
    mostrar guiones durante reset o antes de ejecutar.
    """
    instruction = _get(snapshot, "current_instruction")
    trace = _get(snapshot, "single_cycle_trace") or {}
    control = _control_snapshot(_get(snapshot, "control_signals"))
    opcode = _value(_get(instruction, "opcode") or trace.get("opcode"))

    active_modules = _active_modules_for_opcode(opcode)

    modules = {
        "control_unit": _module(
            "control_unit",
            [
                ("opcode", opcode),
                ("RegWrite", _bool_value(control.get("reg_write"))),
                ("MemRead", _bool_value(control.get("mem_read"))),
                ("MemWrite", _bool_value(control.get("mem_write"))),
                ("ALUSrc", control.get("alu_src")),
                ("ResultSrc", control.get("result_src")),
                ("PCSrc", _pc_src_signal(control, trace)),
                ("Branch", _bool_value(control.get("branch"))),
                ("ALUCtrl", control.get("alu_control")),
            ],
            active_modules,
        ),
        "pc_src_mux": _module(
            "pc_src_mux",
            [
                ("PCSrc", _pc_src_signal(control, trace)),
            ],
            active_modules,
        ),
        "pc": _module(
            "pc",
            [
                ("PC", trace.get("pc", _get(snapshot, "pc"))),
                ("PC+4", trace.get("pc_plus_4")),
                ("Next", trace.get("next_pc")),
            ],
            active_modules,
        ),
        "instruction_memory": _module(
            "instruction_memory",
            [("Instr", _instruction_text(instruction, trace))],
            active_modules,
        ),
        "register_file": _module(
            "register_file",
            [
                ("rs1", _register_line(trace, "rs1", "rs1_value")),
                ("rs2", _register_line(trace, "rs2", "rs2_value")),
                ("rd", _value(_get(instruction, "rd") or trace.get("rd"))),
                ("WB", trace.get("writeback_value")),
                ("RegWrite", _bool_value(control.get("reg_write"))),
            ],
            active_modules,
        ),
        "immediate": _module(
            "immediate",
            [
                ("imm", trace.get("imm", _get(instruction, "imm"))),
                ("ImmSrc", _imm_src(opcode)),
            ],
            active_modules,
        ),
        "alu_src_mux": _module(
            "alu_src_mux",
            [
                ("ALUSrc", control.get("alu_src")),
            ],
            active_modules,
        ),
        "alu": _module(
            "alu",
            [
                ("Op1", _operand_line(trace, "operand_a_label", "operand_a_value")),
                ("Op2", _operand_line(trace, "operand_b_label", "operand_b_value")),
                ("ALUCtrl", control.get("alu_control")),
                ("Result", trace.get("alu_result")),
                ("Branch taken", trace.get("branch_taken")),
            ],
            active_modules,
        ),
        "data_memory": _module(
            "data_memory",
            [
                ("Addr", trace.get("memory_address")),
                ("WriteData", trace.get("memory_write_data")),
                ("ReadData", trace.get("memory_read_data")),
                ("MemRead", _bool_value(control.get("mem_read"))),
                ("MemWrite", _bool_value(control.get("mem_write"))),
            ],
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
        "active_modules": active_modules,
        "modules": modules,
    }


def _active_modules_for_opcode(opcode: str) -> set[str]:
    if opcode in R_TYPE_OPCODES:
        return {
            "control_unit",
            "pc",
            "instruction_memory",
            "register_file",
            "alu_src_mux",
            "alu",
            "result_src_mux",
        }

    if opcode == "addi":
        return {
            "control_unit",
            "pc",
            "instruction_memory",
            "register_file",
            "immediate",
            "alu_src_mux",
            "alu",
            "result_src_mux",
        }

    if opcode == "lw":
        return {
            "control_unit",
            "pc",
            "instruction_memory",
            "register_file",
            "immediate",
            "alu_src_mux",
            "alu",
            "data_memory",
            "result_src_mux",
        }

    if opcode == "sw":
        return {
            "control_unit",
            "pc",
            "instruction_memory",
            "register_file",
            "immediate",
            "alu_src_mux",
            "alu",
            "data_memory",
        }

    if opcode in BRANCH_OPCODES:
        return {
            "control_unit",
            "pc_src_mux",
            "pc",
            "instruction_memory",
            "register_file",
            "immediate",
            "alu",
        }

    return set()


def _module(key: str, pairs: list[tuple[str, object]], active_modules: set[str]) -> dict:
    active = key in active_modules
    lines = []

    for label, raw_value in pairs:
        value = _value(raw_value) if active else "-"

        if label == "Branch taken" and value == "-":
            continue

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
    }


def _pc_src_signal(control: dict, trace: dict) -> str:
    if "pc_src" in trace:
        return _value(trace["pc_src"])
    if "pc_src" in control:
        return _value(control["pc_src"])
    return "-"


def _instruction_text(instruction, trace: dict) -> str:
    text = trace.get("instruction")
    if text:
        return text

    text = _get(instruction, "complete_instruction")
    if text:
        return text

    opcode = _get(instruction, "opcode")
    if opcode:
        return opcode

    return "-"


def _register_line(trace: dict, register_key: str, value_key: str) -> str:
    register = trace.get(register_key)
    value = trace.get(value_key)

    if register is None:
        return "-"

    if value is None:
        return _value(register)

    return f"{register} = {value}"


def _operand_line(trace: dict, label_key: str, value_key: str) -> str:
    label = trace.get(label_key)
    value = trace.get(value_key)

    if label is None:
        return "-"

    if value is None:
        return _value(label)

    return f"{label} = {value}"


def _imm_src(opcode: str) -> str:
    if opcode in {"addi", "lw"}:
        return "I-type"
    if opcode == "sw":
        return "S-type"
    if opcode in BRANCH_OPCODES:
        return "B-type"
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
