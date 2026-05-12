from dataclasses import dataclass

@dataclass
class Instruction:
    opcode : str
    rd : str | None = None
    rs1 : str | None = None
    rs2 : str | None = None
    imm : int | None = None
    completeInstruction : str | None = None


    
