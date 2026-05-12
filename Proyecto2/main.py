from src.assembler import Parser
from src.core import ControlUnit, Decoder, InstructionMemory


def main() -> None:
    code = """
        # Ejemplo minimo del flujo compartido
        loop:
        ADD R1, R2, R3
        LW x4, 0(x1)
        BEQ x1, x4, loop
    """

    try:
        parser = Parser()
        instructions, labels = parser.parse_text(code)

        instruction_memory = InstructionMemory()
        instruction_memory.load_program(instructions)

        decoder = Decoder(labels)
        control_unit = ControlUnit()

        pc = 0
        while pc < len(instructions) * 4:
            raw = instruction_memory.fetch(pc)
            instruction = decoder.decode(raw)
            control_signals = control_unit.generate_control_signals(instruction)

            print(raw, "=>", instruction, control_signals.dump())
            pc += 4
    except ValueError as error:
        print(f"Error de programa: {error}")


if __name__ == "__main__":
    main()
