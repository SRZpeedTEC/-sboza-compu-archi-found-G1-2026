import unittest
from pathlib import Path
import sys

# Permite ejecutar este archivo directamente desde la carpeta test sin perder
# acceso al paquete src del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.assembler import Parser
from src.core import ControlUnit, Decoder, InstructionMemory, Memory, RegisterBank


class CoreFlowTests(unittest.TestCase):
    def test_parser_returns_clean_strings_and_labels(self) -> None:
        code = """
            # comentario
            loop:
            ADD x1, x2, x3
            LW x4, 8(x1)
        """

        instructions, labels = Parser().parse_text(code)

        self.assertEqual(instructions, ["add x1 x2 x3", "lw x4 8(x1)"])
        self.assertEqual(labels, {"loop": 0})

    def test_parser_rejects_duplicated_labels(self) -> None:
        code = """
            loop: add x1, x2, x3
            loop: sub x1, x2, x3
        """

        with self.assertRaisesRegex(ValueError, "duplicada"):
            Parser().parse_text(code)

    def test_instruction_memory_fetches_raw_strings_by_pc(self) -> None:
        memory = InstructionMemory()
        memory.load_program(["add x1 x2 x3", "sub x4 x5 x6"])

        self.assertEqual(memory.fetch(4), "sub x4 x5 x6")

    def test_decoder_supports_memory_operands_and_branches(self) -> None:
        decoder = Decoder(labels={"loop": 0})

        load = decoder.decode("lw x1 12(x2)")
        branch = decoder.decode("beq x1 x2 loop")

        self.assertEqual(load.rd, "x1")
        self.assertEqual(load.rs1, "x2")
        self.assertEqual(load.imm, 12)
        self.assertEqual(branch.imm, 0)

    def test_decoder_rejects_invalid_register_and_memory_operand(self) -> None:
        decoder = Decoder()

        with self.assertRaisesRegex(ValueError, "Registro invalido"):
            decoder.decode("add x32 x1 x2")

        with self.assertRaisesRegex(ValueError, "Operando de memoria invalido"):
            decoder.decode("lw x1 0x2")

    def test_control_unit_generates_signals(self) -> None:
        instruction = Decoder().decode("sw x3 0(x4)")
        signals = ControlUnit().generate_control_signals(instruction)

        self.assertTrue(signals.mem_write)
        self.assertEqual(signals.result_src, "none")
        self.assertEqual(signals.alu_src, "imm")

    def test_register_zero_and_memory_validation(self) -> None:
        registers = RegisterBank()
        registers.write("x0", 99)
        registers.write("r1", 7)

        memory = Memory(word_count=4)
        memory.store_word(0, registers.read("r1"))

        self.assertEqual(registers.read("x0"), 0)
        self.assertEqual(memory.load_word(0), 7)

        with self.assertRaisesRegex(ValueError, "alineada"):
            memory.load_word(2)


if __name__ == "__main__":
    unittest.main()
