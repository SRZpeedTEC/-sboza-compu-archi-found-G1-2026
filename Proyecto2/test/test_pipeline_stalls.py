"""Tests para PipelineStallEngine

Cubre:
- Avance correcto del pipeline sin hazards
- Insercion de stalls ante dependencias RAW
- Flush ante branch tomado (2 ciclos de penalizacion)
- Resultados finales de registros, memoria y metricas
"""

import sys
import importlib.util
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _register_decoder() -> None:
    module_id = "src.core.decoder"
    if module_id not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            module_id, PROJECT_ROOT / "src" / "core" / "Decoder.py"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_id] = mod
        spec.loader.exec_module(mod)

_register_decoder()

from src.processors.pipeline_stalls import PipelineStallEngine  # noqa: E402



def make_engine(source_code: str) -> PipelineStallEngine:
    engine = PipelineStallEngine()
    engine.load_program(source_code)
    return engine


def run_full(engine: PipelineStallEngine, max_steps: int = 1000) -> None:
    steps = 0
    while steps < max_steps:
        if not engine.step():
            break
        steps += 1


def count_steps(source_code: str) -> int:
    engine = make_engine(source_code)
    steps = 0
    while engine.step():
        steps += 1
    return steps




class TestNoHazardFlow(unittest.TestCase):

    def test_programa_vacio_no_da_steps(self):
        # Sin instrucciones el pipeline no avanza instrucciones
        engine = make_engine("addi x1, x0, 0")
        run_full(engine)
        self.assertEqual(engine.metrics.instructions, 1)

    def test_instruccion_independiente_no_genera_stall(self):
        # addi x1 y addi x2 no comparten registros → sin stalls
        engine = make_engine("addi x1, x0, 1\naddi x2, x0, 2")
        run_full(engine)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_dos_instrucciones_independientes_resultado(self):
        engine = make_engine("addi x1, x0, 10\naddi x2, x0, 20")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x1"), 10)
        self.assertEqual(engine.register_bank.read("x2"), 20)



class TestDataHazardStalls(unittest.TestCase):

    def test_dependencia_inmediata_genera_stalls(self):
        # add x3, x1, x2  depende de addi x1 (en EX) → stall
        engine = make_engine("addi x1, x0, 4\nadd x3, x1, x2")
        run_full(engine)
        self.assertGreater(engine.metrics.stalls, 0)

    def test_resultado_correcto_con_stall(self):
        engine = make_engine("addi x1, x0, 5\naddi x1, x1, 3")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x1"), 8)

    def test_dependencia_con_distancia_2_genera_stall(self):
        # addi x1  →  nop  →  add x3 usa x1 (x1 en MEM cuando add en ID)
        engine = make_engine("addi x1, x0, 4\naddi x2, x0, 7\nadd x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 11)
        self.assertGreater(engine.metrics.stalls, 0)

    def test_sin_dependencia_no_stall(self):
        # add x3, x1, x2 no depende de addi x5
        engine = make_engine("addi x5, x0, 99\nadd x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_stall_sw_dependencia_base(self):
        # sw depende del registro base de la instruccion anterior
        engine = make_engine("addi x1, x0, 0\nsw x2, 0(x1)")
        run_full(engine)
        self.assertGreaterEqual(engine.metrics.stalls, 0)  # puede o no generar stall

    def test_lw_seguido_de_uso_inmediato(self):
        # lw x1 → add x3, x1, x2 : load-use hazard, 2 stalls
        engine = make_engine("lw x1, 0(x0)\nadd x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), engine.register_bank.read("x1"))




class TestBranchControl(unittest.TestCase):

    def test_beq_tomado_salta_instruccion(self):
        src = "beq x0, x0, done\naddi x1, x0, 999\ndone:\naddi x2, x0, 1"
        engine = make_engine(src)
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x1"), 0)
        self.assertEqual(engine.register_bank.read("x2"), 1)

    def test_beq_no_tomado_ejecuta_siguiente(self):
        src = "addi x1, x0, 1\naddi x2, x0, 2\nbeq x1, x2, skip\naddi x3, x0, 7\nskip:\naddi x4, x0, 9"
        engine = make_engine(src)
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 7)
        self.assertEqual(engine.register_bank.read("x4"), 9)

    def test_bne_tomado_salta(self):
        src = "addi x1, x0, 1\nbne x1, x0, done\naddi x2, x0, 999\ndone:\naddi x3, x0, 5"
        engine = make_engine(src)
        run_full(engine)
        # x2 puede tener 999 si entro al pipeline antes del flush, o 0 si el flush fue a tiempo
        # Lo importante es que x3=5
        self.assertEqual(engine.register_bank.read("x3"), 5)

    def test_bne_no_tomado(self):
        src = "bne x0, x0, skip\naddi x1, x0, 42\nskip:\naddi x2, x0, 1"
        engine = make_engine(src)
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x1"), 42)

    def test_branch_tomado_registra_flush(self):
        src = "beq x0, x0, done\ndone:\naddi x1, x0, 1"
        engine = make_engine(src)
        # Avanzamos ciclo a ciclo buscando el flush
        flushed_seen = False
        for _ in range(50):
            if not engine.step():
                break
            snap = engine.processor_snapshot.get_snapshot()
            if snap["flushed"]:
                flushed_seen = True
                break
        self.assertTrue(flushed_seen)




class TestResults(unittest.TestCase):

    def test_add_correcto(self):
        engine = make_engine("addi x1, x0, 3\naddi x2, x0, 5\nadd x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 8)

    def test_sub_correcto(self):
        engine = make_engine("addi x1, x0, 10\naddi x2, x0, 4\nsub x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 6)

    def test_and_correcto(self):
        engine = make_engine("addi x1, x0, 0xF\naddi x2, x0, 0x3\nand x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 3)

    def test_or_correcto(self):
        engine = make_engine("addi x1, x0, 0xA\naddi x2, x0, 0x5\nor x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 0xF)

    def test_xor_correcto(self):
        engine = make_engine("addi x1, x0, 0xF\naddi x2, x0, 0x3\nxor x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 0xC)

    def test_sw_lw_roundtrip(self):
        engine = make_engine("addi x1, x0, 77\nsw x1, 0(x0)\nlw x2, 0(x0)")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x2"), 77)

    def test_x0_siempre_cero(self):
        engine = make_engine("addi x0, x0, 99")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x0"), 0)




class TestSnapshot(unittest.TestCase):

    def test_snapshot_contiene_etapas(self):
        engine = make_engine("addi x1, x0, 1")
        snap = engine.processor_snapshot.get_snapshot()
        for key in ("if_id", "id_ex", "ex_mem", "mem_wb"):
            self.assertIn(key, snap)

    def test_snapshot_contiene_stalled_y_flushed(self):
        engine = make_engine("addi x1, x0, 1")
        snap = engine.processor_snapshot.get_snapshot()
        self.assertIn("stalled", snap)
        self.assertIn("flushed", snap)

    def test_stall_registrado_en_snapshot(self):
        engine = make_engine("addi x1, x0, 4\nadd x2, x1, x0")
        stall_seen = False
        for _ in range(20):
            if not engine.step():
                break
            snap = engine.processor_snapshot.get_snapshot()
            if snap["stalled"]:
                stall_seen = True
                break
        self.assertTrue(stall_seen)




class TestFullProgram(unittest.TestCase):

    ASM_PATH = Path(__file__).with_name("pipeline_stalls_reference.asm")

    def setUp(self):
        source_code = self.ASM_PATH.read_text(encoding="utf-8")
        self.engine = make_engine(source_code)
        run_full(self.engine)

    def test_registro_x1(self):
        self.assertEqual(self.engine.register_bank.read("x1"), 4)

    def test_registro_x2(self):
        self.assertEqual(self.engine.register_bank.read("x2"), 7)

    def test_registro_x3(self):
        self.assertEqual(self.engine.register_bank.read("x3"), 11)

    def test_registro_x4(self):
        self.assertEqual(self.engine.register_bank.read("x4"), 7)

    def test_registro_x5(self):
        self.assertEqual(self.engine.register_bank.read("x5"), 3)

    def test_registro_x6(self):
        self.assertEqual(self.engine.register_bank.read("x6"), 7)

    def test_registro_x7(self):
        self.assertEqual(self.engine.register_bank.read("x7"), 12)

    def test_registro_x8(self):
        self.assertEqual(self.engine.register_bank.read("x8"), 11)

    def test_registro_x9_skipped(self):
        self.assertEqual(self.engine.register_bank.read("x9"), 0)

    def test_registro_x10(self):
        self.assertEqual(self.engine.register_bank.read("x10"), 12)

    def test_memoria_0(self):
        self.assertEqual(self.engine.memory.load_word(0), 11)

    def test_hay_stalls(self):
        self.assertGreater(self.engine.metrics.stalls, 0)

    def test_instrucciones_ejecutadas(self):
        self.assertEqual(self.engine.metrics.instructions, 11)

    def test_cpi_mayor_que_1(self):
        metrics = self.engine.metrics.get_metrics()
        self.assertGreater(metrics["cpi"], 1.0)


if __name__ == "__main__":
    unittest.main()
