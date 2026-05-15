from src.processors.processor_engine import ProcessorEngine

class SingleCycleEngine(ProcessorEngine):
    """Punto de extension para ejecutar una instruccion completa por ciclo."""

    def __init__(self) -> None:
        super().__init__()
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
        self.control_signals = control_signal

        
        match instruction.opcode:
            case "add" | "sub" | "and" | "or" | "xor":
                self.execute_r_type(instruction, control_signal)
            
            case "addi":
                self.execute_addi(instruction, control_signal)

            case "lw":
                self.execute_lw(instruction)
                

            case "sw":
                self.execute_sw(instruction)

            case "beq" | "bne":
                self.execute_branch(instruction, control_signal)

            
        self.metrics.count_cycle()
        self.metrics.count_instruction()
        self.processor_snapshot = self.get_snapshot()
        return True
