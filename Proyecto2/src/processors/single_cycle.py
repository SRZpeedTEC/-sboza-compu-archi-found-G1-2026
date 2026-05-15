from src.processors.processor_engine import ProcessorEngine, ProcessorSnapshot
i

class SingleCycleEngine(ProcessorEngine):
    """Punto de extension para ejecutar una instruccion completa por ciclo."""

    def __init__(self) -> None:
        super().__init__("Single Cycle")
        self.load_program(self.source_code)
        self.processor_snapshot = self.get_snapshot()


    def step(self) -> bool:
        if self.is_program_finished():
            return False
        
        raw_instruction = self.instruction_memory.fetch(self.pc)
        instruction = self.decoder.decode(raw_instruction)

        # Generar las señales de control para la instruccion actual. 
        # principalmente util para frontend
        control_signal = self.control_unit.generate_control_signals(
            instruction)

        
        match instruction.opcode:
            case "add", "sub", "and", "or":
                
                rs1 = self.get_register(instruction.rs1)
                rs2 = self.get_register(instruction.rs2)
                result = self.execute_alu(rs1, rs2, control_signal.alu_control)

                self.write_register(instruction.rd, result)
            
            case "addi":
                self.execute_addi(instruction, control_signal)

                rs1 = self.get_register(instruction.rs1)
                imm = instruction.imm
                result = self.execute_alu(rs1, imm, control_signal.alu_control)

                self.write_register(instruction.rd, result)

            case "lw":
                self.execute_lw(instruction)
                

            case "sw":
                self.execute_sw(instruction, control_signal)

            case "beq", "bne":
                self.execute_branch(instruction, control_signal)

            
        self.metrics.count_cycle()
        self.metrics.count_instruction()
        self.processor_snapshot = self.get_snapshot()

        
        

        

    


    

        


    