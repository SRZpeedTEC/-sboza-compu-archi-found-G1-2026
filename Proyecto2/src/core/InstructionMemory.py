class InstructionMemory:
    def __init__(self):
        self.instructions = []

    def load_program(self, istructions):
        self.instructions = istructions

    def fetch(self, pc):
        index = pc // 4  # Assuming each instruction is 4 bytes
        if index < len(self.instructions):
            return self.instructions[index]
        else:   
            raise IndexError("Program Counter out of bounds")