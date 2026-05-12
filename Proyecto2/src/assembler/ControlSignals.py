from dataclasses import dataclass

@dataclass
class ControlSignals:
    reg_write: bool = False
    mem_read: bool = False
    mem_write: bool = False
    alu_src: str = "reg"        # "reg" o "imm"
    result_src: str = "alu"     # "alu", "memory", "pc_plus_4", "none"
    pc_src: str = "pc_plus_4"   # "pc_plus_4", "branch"
    branch: bool = False
    alu_control: str = "ADD"