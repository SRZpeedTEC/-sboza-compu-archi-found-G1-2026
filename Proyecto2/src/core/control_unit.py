from src.assembler.control_signals import ControlSignals
from src.assembler.instruction import Instruction


class ControlUnit:
    """Genera senales de control a partir de una Instruction.

    La unidad de control no ejecuta la instruccion. Solo describe decisiones de
    datapath como origen de ALU, escritura de registros y acceso a memoria.
    """

    _R_TYPE_ALU_CONTROL = {
        "add": "ADD",
        "sub": "SUB",
        "and": "AND",
        "or": "OR",
        "xor": "XOR",
    }

    def generate_control_signals(self, instruction: Instruction) -> ControlSignals:
        """Construye las senales de control para el datapath.

        Aqui se modelan decisiones de alto nivel. Por ejemplo, `alu_src="imm"`
        reemplaza la idea de crear una clase Mux para elegir entre registro e
        inmediato, lo cual mantiene el simulador simple.
        """

        opcode = instruction.opcode

        if opcode in self._R_TYPE_ALU_CONTROL:
            return ControlSignals(
                reg_write=True,
                alu_src="reg",
                result_src="alu",
                alu_control=self._R_TYPE_ALU_CONTROL[opcode],
            )

        if opcode == "addi":
            return ControlSignals(
                reg_write=True,
                alu_src="imm",
                result_src="alu",
                alu_control="ADD",
            )

        if opcode == "lw":
            return ControlSignals(
                reg_write=True,
                mem_read=True,
                alu_src="imm",
                result_src="memory",
                alu_control="ADD",
            )

        if opcode == "sw":
            return ControlSignals(
                mem_write=True,
                alu_src="imm",
                result_src="none",
                alu_control="ADD",
            )

        if opcode in {"beq", "bne"}:
            return ControlSignals(
                alu_src="reg",
                result_src="none",
                pc_src="branch",
                branch=True,
                branch_condition=opcode,
                alu_control="SUB",
            )

        raise ValueError(
            f"No hay senales de control definidas para opcode '{opcode}' "
            f"en instruccion {instruction.complete_instruction!r}."
        )
