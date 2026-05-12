from src.assembler.instruction import Instruction 

class Decoder:
    def __init__(self, labels: dict[str, int]):
        self.labels = labels

    def decode(self, raw: str) -> Instruction:
        if raw is None:
            return None

        parts = raw.split()
        opcode = parts[0]


        if opcode in ["add", "sub", "and", "or", "xor"]:
            return self._decode_r_type(raw, parts)

        elif opcode in ["addi", "lw"]:
            return self._decode_i_type(raw, parts)

        elif opcode == "sw":
            return self._decode_s_type(raw, parts)

        elif opcode in ["beq", "bne"]:
            return self._decode_sb_type(raw, parts)

        else:
            raise ValueError(f"Instrucción no soportada: {opcode}")
        

    # Para las instrucciones de tipo R, el formato es: opcode rd rs1 rs2  
    def _decode_r_type(self, raw: str, parts: list[str]) -> Instruction:
        
        return Instruction(
            opcode=parts[0],
            rd=parts[1],
            rs1=parts[2],
            rs2=parts[3],
            completeInstruction=raw
        )
        
    
    # Para las instrucciones de tipo I, el formato es: opcode rd rs1 imm  
    def _decode_i_type(self, raw: str, parts: list[str]) -> Instruction:

        imm = int(parts[3]) if parts[3].isdigit() else self.labels.get(parts[3], 0)

        return Instruction(
            opcode=parts[0],
            rd=parts[1],
            rs1=parts[2],
            imm=imm,
            completeInstruction=raw
        )
    
    # Para las instrucciones de tipo S, el formato es: opcode rs1 rs2 imm
    def _decode_s_type(self, raw: str, parts: list[str]) -> Instruction:

        imm = int(parts[2]) if parts[2].isdigit() else self.labels.get(parts[2], 0)

        return Instruction(
            opcode=parts[0],
            rs1=parts[1],
            imm=imm,
            completeInstruction=raw
        )
    

    # Para las instrucciones de tipo SB, el formato es: opcode rs1 rs2 label
    def _decode_sb_type(self, raw: str, parts: list[str]) -> Instruction:

        imm = int(parts[3]) if parts[3].isdigit() else self.labels.get(parts[3], 0)

        return Instruction(
            opcode=parts[0],
            rs1=parts[1],
            rs2=parts[2],
            imm=imm,
            completeInstruction=raw
        )
    

    