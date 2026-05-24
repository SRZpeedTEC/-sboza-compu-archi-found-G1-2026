from pathlib import Path
import sys


# Permite ejecutar este archivo directamente desde la carpeta test sin perder
# acceso al paquete src del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.assembler.parser import Parser
from src.core.Decoder import Decoder
from src.assembler.instruction import Instruction

def test_parser():

    code = """
                start: addi, x1, x0, 5
                loop:
                    addi x1, x1, 1
                    beq x1, x2, loop
                end:
                    add x3, x1, x2
            """

    parser = Parser()
    instructions, labels = parser.parse_text(code)
    print("Instrucciones:", instructions)
    print("Labels:", labels)

    decoder = Decoder(labels)
    [print(f"Decoded: {decoder.decode(instr)}") for instr in instructions]
    

test_parser()


