from src.processors.processor_engine import ProcessorEngine

class SingleCycleEngine(ProcessorEngine):
    """Punto de extension para ejecutar una instruccion completa por ciclo."""

    def __init__(self) -> None:
        super().__init__()
        self.current_instruction = None
        self.single_cycle_trace = {}
        self.load_program(self.source_code)
        self.processor_snapshot = self.get_snapshot()


    def step(self) -> bool:
        if self.is_program_finished():
            return False
        
        raw_instruction = self.instruction_memory.fetch(self.pc)
        instruction = self.decoder.decode(raw_instruction)
        self.current_instruction = instruction

        # Generar las señales de control para la instruccion actual. 
        # principalmente util para frontend
        control_signal = self.control_unit.generate_control_signals(
            instruction)
        self.control_signals = control_signal
        self.single_cycle_trace = self._build_single_cycle_trace(
            instruction,
            control_signal,
            self.pc
        )

        
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

            
        self.single_cycle_trace["next_pc"] = self.pc
        self.metrics.count_cycle()
        self.metrics.count_instruction()
        self.processor_snapshot = self.get_snapshot()
        return True

    def _build_single_cycle_trace(self, instruction, control_signal, pc_before):
        rs1_value = (
            self.get_register(instruction.rs1)
            if instruction.rs1 is not None
            else None
        )
        rs2_value = (
            self.get_register(instruction.rs2)
            if instruction.rs2 is not None
            else None
        )

        operand_a = rs1_value
        operand_b = (
            instruction.imm
            if control_signal.alu_src == "imm"
            else rs2_value
        )

        alu_result = None
        if operand_a is not None and operand_b is not None:
            alu_result = self.execute_alu(
                operand_a,
                operand_b,
                control_signal.alu_control
            )

        memory_address = None
        memory_read_data = None
        memory_write_data = None
        writeback_value = None
        branch_taken = None
        next_pc = pc_before + 4
        pc_src = "pc_plus_4"

        if instruction.opcode in {"lw", "sw"}:
            memory_address = alu_result

        if instruction.opcode == "lw" and memory_address is not None:
            memory_read_data = self.load_from_memory(memory_address)
            writeback_value = memory_read_data

        elif instruction.opcode == "sw":
            memory_write_data = rs2_value

        elif instruction.opcode in {"add", "sub", "and", "or", "xor", "addi"}:
            writeback_value = alu_result

        elif instruction.opcode in {"beq", "bne"}:
            branch_taken = self._branch_condition_met(
                instruction.opcode,
                alu_result
            )
            if branch_taken:
                next_pc = instruction.imm
                pc_src = "branch_target"

        return {
            "opcode": instruction.opcode,
            "instruction": instruction.complete_instruction,
            "pc": pc_before,
            "pc_plus_4": pc_before + 4,
            "next_pc": next_pc,
            "pc_src": pc_src,
            "rs1": instruction.rs1,
            "rs1_value": rs1_value,
            "rs2": instruction.rs2,
            "rs2_value": rs2_value,
            "rd": instruction.rd,
            "imm": instruction.imm,
            "operand_a_label": "R1" if instruction.rs1 is not None else None,
            "operand_a_value": operand_a,
            "operand_b_label": (
                "imm" if control_signal.alu_src == "imm" else "R2"
            ),
            "operand_b_value": operand_b,
            "alu_result": alu_result,
            "memory_address": memory_address,
            "memory_read_data": memory_read_data,
            "memory_write_data": memory_write_data,
            "writeback_value": writeback_value,
            "branch_taken": branch_taken,
        }

    def _branch_condition_met(self, opcode, alu_result):
        if alu_result is None:
            return None

        if opcode == "beq":
            return alu_result == 0

        if opcode == "bne":
            return alu_result != 0

        return None
