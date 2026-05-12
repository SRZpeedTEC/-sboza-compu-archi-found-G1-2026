class Memory:
    def __init__(self):
        self.memory = [0] * 1024  # Assuming a memory size of 1024 locations

    def loadWord(self, address):
        index = address // 4  # Assuming word size is 4 bytes
        if index < 0 or index >= len(self.memory):
            raise IndexError("Memory address out of bounds")
        return self.memory[index]

    def storeWord(self, address, value):
        index = address // 4  # Assuming word size is 4 bytes
        if index < 0 or index >= len(self.memory):
            raise IndexError("Memory address out of bounds")
        self.memory[index] = value
