import sys
import unittest
from pathlib import Path

# Permite ejecutar este archivo directamente desde la carpeta test sin perder
# acceso al paquete src del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.assembler.parser import Parser
from src.core.Decoder import Decoder


class ParserDecoderSmokeTests(unittest.TestCase):
    def test_parser_y_decoder_resuelven_labels(self) -> None:
        code = """
            start: addi, x1, x0, 5
            loop:
                addi x1, x1, 1
                beq x1, x2, loop
            end:
                add x3, x1, x2
        """

        instructions, labels = Parser().parse_text(code)
        decoder = Decoder(labels)
        decoded = [decoder.decode(instr) for instr in instructions]

        self.assertEqual(labels, {"start": 0, "loop": 4, "end": 12})
        self.assertEqual(decoded[2].opcode, "beq")
        self.assertEqual(decoded[2].imm, 4)


if __name__ == "__main__":
    unittest.main()
