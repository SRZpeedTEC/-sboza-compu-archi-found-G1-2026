import unittest
from pathlib import Path
import sys

# Permite ejecutar este archivo directamente desde la carpeta test sin perder
# acceso al paquete src del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.assembler.parser import Parser


class TestParser(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_instrucciones_basicas(self):
        code = """
            add x1, x2, x3
            sub x4, x5, x6
        """

        instructions, labels = self.parser.parse_text(code)

        self.assertEqual(instructions, [
            "add x1 x2 x3",
            "sub x4 x5 x6"
        ])
        self.assertEqual(labels, {})

    def test_comentarios_mayusculas_y_espacios(self):
        code = """
            # comentario completo

            ADD X1, X2, X3     # suma
            SUB   X4,    X5, X6
        """

        instructions, labels = self.parser.parse_text(code)

        self.assertEqual(instructions, [
            "add x1 x2 x3",
            "sub x4 x5 x6"
        ])
        self.assertEqual(labels, {})

    def test_labels_en_linea_separada(self):
        code = """
            start:
                addi x1, x0, 5
            loop:
                addi x1, x1, 1
                beq x1, x2, loop
            end:
                add x3, x1, x2
        """

        instructions, labels = self.parser.parse_text(code)

        self.assertEqual(instructions, [
            "addi x1 x0 5",
            "addi x1 x1 1",
            "beq x1 x2 loop",
            "add x3 x1 x2"
        ])

        self.assertEqual(labels, {
            "start": 0,
            "loop": 4,
            "end": 12
        })

    def test_etiqueta_duplicada(self):
        code = """
            loop: addi x1, x1, 1
            loop: addi x2, x2, 1
        """

        with self.assertRaises(ValueError):
            self.parser.parse_text(code)

    def test_etiqueta_invalida(self):
        code = """
            1loop: addi x1, x0, 5
        """

        with self.assertRaises(ValueError):
            self.parser.parse_text(code)

    def test_entrada_no_string(self):
        with self.assertRaises(ValueError):
            self.parser.parse_text(12345)


if __name__ == "__main__":
    unittest.main()
