class RegisterBank:
    def __init__(self):
        self.registers = [0] * 32

    def _to_index(self, reg):
        return int(reg[1:])
        
        
    def read(self, reg):
        index = self._to_index(reg)
        return self.registers[index]
    
    
    def write(self, reg, value):
        index = self._to_index(reg)
        self.registers[index] = value




    


    
