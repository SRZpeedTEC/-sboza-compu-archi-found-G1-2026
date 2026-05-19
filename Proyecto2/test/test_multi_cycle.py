"""Tests unitarios para MultiCycleEngine.

Verifica que cada tipo de instruccion:
  - Transite por las etapas correctas
  - Tome el numero exacto de ciclos
  - Produzca el resultado correcto en registros y memoria
  - Reporte las metricas correctas (ciclos, instrucciones, CPI)
"""

import sys
import importlib.util
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Python 3.13 trata los nombres de modulo con distincion de mayusculas/minusculas
# incluso en Windows. Decoder.py debe registrarse como src.core.decoder antes de
# que src/core/__init__.py lo intente importar.
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

from src.processors.multi_cycle import MultiCycleEngine, Stage  # noqa: E402



def make_engine(source_code: str) -> MultiCycleEngine:
    engine = MultiCycleEngine()
    engine.load_program(source_code)
    return engine


def step_n(engine: MultiCycleEngine, n: int) -> None:
    for _ in range(n):
        engine.step()


def run_full(engine: MultiCycleEngine, max_steps: int = 500) -> None:
    steps = 0
    while steps < max_steps:
        if not engine.step():
            break
        steps += 1


class TestStageTransitions(unittest.TestCase):

    def test_initial_stage_is_fetch(self):
        engine = make_engine("add x1, x2, x3")
        self.assertEqual(engine._stage, Stage.FETCH)

    def test_r_type_stage_sequence(self):
        engine = make_engine("add x1, x2, x3")
        expected = [Stage.DECODE, Stage.EXECUTE, Stage.WRITEBACK, Stage.FETCH]
        for expected_stage in expected:
            engine.step()
            self.assertEqual(engine._stage, expected_stage)

    def test_addi_stage_sequence(self):
        engine = make_engine("addi x1, x0, 5")
        expected = [Stage.DECODE, Stage.EXECUTE, Stage.WRITEBACK, Stage.FETCH]
        for expected_stage in expected:
            engine.step()
            self.assertEqual(engine._stage, expected_stage)

    def test_lw_stage_sequence(self):
        engine = make_engine("lw x1, 0(x0)")
        expected = [Stage.DECODE, Stage.EXECUTE, Stage.MEMORY, Stage.WRITEBACK, Stage.FETCH]
        for expected_stage in expected:
            engine.step()
            self.assertEqual(engine._stage, expected_stage)

    def test_sw_stage_sequence(self):
        engine = make_engine("sw x1, 0(x0)")
        expected = [Stage.DECODE, Stage.EXECUTE, Stage.MEMORY, Stage.FETCH]
        for expected_stage in expected:
            engine.step()
            self.assertEqual(engine._stage, expected_stage)

    def test_beq_taken_stage_sequence(self):
        # x0 == x0 siempre, beq se toma
        engine = make_engine("beq x0, x0, done\ndone:\naddi x1, x0, 1")
        expected = [Stage.DECODE, Stage.EXECUTE, Stage.FETCH]
        for expected_stage in expected:
            engine.step()
            self.assertEqual(engine._stage, expected_stage)

    def test_bne_not_taken_stage_sequence(self):
        # x0 != x0 es False, bne no se toma
        engine = make_engine("bne x0, x0, skip\nskip:\naddi x1, x0, 1")
        expected = [Stage.DECODE, Stage.EXECUTE, Stage.FETCH]
        for expected_stage in expected:
            engine.step()
            self.assertEqual(engine._stage, expected_stage)




class TestCyclesPerInstruction(unittest.TestCase):

    def _cycles_for(self, source_code: str) -> int:
        engine = make_engine(source_code)
        run_full(engine)
        return engine.metrics.cycles

    def test_r_type_add_takes_4_cycles(self):
        self.assertEqual(self._cycles_for("add x1, x2, x3"), 4)

    def test_r_type_sub_takes_4_cycles(self):
        self.assertEqual(self._cycles_for("sub x1, x2, x3"), 4)

    def test_r_type_and_takes_4_cycles(self):
        self.assertEqual(self._cycles_for("and x1, x2, x3"), 4)

    def test_r_type_or_takes_4_cycles(self):
        self.assertEqual(self._cycles_for("or x1, x2, x3"), 4)

    def test_r_type_xor_takes_4_cycles(self):
        self.assertEqual(self._cycles_for("xor x1, x2, x3"), 4)

    def test_addi_takes_4_cycles(self):
        self.assertEqual(self._cycles_for("addi x1, x0, 10"), 4)

    def test_sw_takes_4_cycles(self):
        self.assertEqual(self._cycles_for("sw x0, 0(x0)"), 4)

    def test_lw_takes_5_cycles(self):
        self.assertEqual(self._cycles_for("lw x1, 0(x0)"), 5)

    def test_beq_taken_takes_3_cycles_for_branch(self):
        # beq x0, x0 siempre tomado: 3 ciclos de branch + 4 del addi posterior
        engine = make_engine("beq x0, x0, done\ndone:\naddi x1, x0, 1")
        run_full(engine)
        self.assertEqual(engine.metrics.cycles, 3 + 4)

    def test_beq_not_taken_takes_3_cycles_for_branch(self):
        # addi(4) + addi(4) + beq no tomado(3) + addi(4) = 15
        engine = make_engine("addi x1, x0, 1\naddi x2, x0, 2\nbeq x1, x2, skip\nskip:\naddi x3, x0, 0")
        run_full(engine)
        self.assertEqual(engine.metrics.cycles, 4 + 4 + 3 + 4)

    def test_bne_taken_takes_3_cycles_for_branch(self):
        # addi(4) + bne tomado(3) + addi destino(4) = 11
        engine = make_engine("addi x1, x0, 1\nbne x1, x0, done\ndone:\naddi x2, x0, 2")
        run_full(engine)
        self.assertEqual(engine.metrics.cycles, 4 + 3 + 4)

    def test_bne_not_taken_takes_3_cycles_for_branch(self):
        # bne no tomado(3) + addi(4) = 7
        engine = make_engine("bne x0, x0, skip\nskip:\naddi x1, x0, 1")
        run_full(engine)
        self.assertEqual(engine.metrics.cycles, 3 + 4)




class TestRegisterResults(unittest.TestCase):

    def test_addi_escribe_valor_correcto(self):
        engine = make_engine("addi x1, x0, 42")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x1"), 42)

    def test_add_suma_registros(self):
        engine = make_engine("addi x1, x0, 10\naddi x2, x0, 20\nadd x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 30)

    def test_sub_resta_registros(self):
        engine = make_engine("addi x1, x0, 15\naddi x2, x0, 6\nsub x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 9)

    def test_and_bit_a_bit(self):
        engine = make_engine("addi x1, x0, 0xF\naddi x2, x0, 0x3\nand x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 0xF & 0x3)

    def test_or_bit_a_bit(self):
        engine = make_engine("addi x1, x0, 0xA\naddi x2, x0, 0x5\nor x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 0xF)

    def test_xor_bit_a_bit(self):
        engine = make_engine("addi x1, x0, 0xF\naddi x2, x0, 0x3\nxor x3, x1, x2")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 0xF ^ 0x3)

    def test_x0_siempre_cero(self):
        engine = make_engine("addi x0, x0, 99")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x0"), 0)

    def test_lw_carga_desde_memoria(self):
        engine = make_engine("addi x1, x0, 7\nsw x1, 0(x0)\nlw x2, 0(x0)")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x2"), 7)




class TestMemoryResults(unittest.TestCase):

    def test_sw_almacena_valor(self):
        engine = make_engine("addi x1, x0, 55\nsw x1, 0(x0)")
        run_full(engine)
        self.assertEqual(engine.memory.load_word(0), 55)

    def test_sw_lw_ida_y_vuelta(self):
        engine = make_engine("addi x1, x0, 123\nsw x1, 4(x0)\nlw x2, 4(x0)")
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x2"), 123)

    def test_sw_con_offset(self):
        engine = make_engine("addi x1, x0, 8\naddi x2, x0, 99\nsw x2, 0(x1)")
        run_full(engine)
        self.assertEqual(engine.memory.load_word(8), 99)




class TestBranches(unittest.TestCase):

    def test_beq_tomado_salta_instruccion(self):
        src = "beq x0, x0, done\naddi x1, x0, 999\ndone:\naddi x2, x0, 1"
        engine = make_engine(src)
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x1"), 0)   # skipped
        self.assertEqual(engine.register_bank.read("x2"), 1)   # ejecutado

    def test_beq_no_tomado_ejecuta_siguiente(self):
        src = "addi x1, x0, 1\naddi x2, x0, 2\nbeq x1, x2, skip\naddi x3, x0, 7\nskip:\naddi x4, x0, 9"
        engine = make_engine(src)
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x3"), 7)   # no skipped
        self.assertEqual(engine.register_bank.read("x4"), 9)

    def test_bne_tomado_salta_instruccion(self):
        src = "addi x1, x0, 1\nbne x1, x0, done\naddi x2, x0, 999\ndone:\naddi x3, x0, 5"
        engine = make_engine(src)
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x2"), 0)   # skipped
        self.assertEqual(engine.register_bank.read("x3"), 5)

    def test_bne_no_tomado_ejecuta_siguiente(self):
        src = "bne x0, x0, skip\naddi x1, x0, 42\nskip:\naddi x2, x0, 1"
        engine = make_engine(src)
        run_full(engine)
        self.assertEqual(engine.register_bank.read("x1"), 42)  # no skipped




class TestMetrics(unittest.TestCase):

    def test_conteo_instrucciones_una(self):
        engine = make_engine("addi x1, x0, 1")
        run_full(engine)
        self.assertEqual(engine.metrics.instructions, 1)

    def test_conteo_ciclos_addi(self):
        engine = make_engine("addi x1, x0, 1")
        run_full(engine)
        self.assertEqual(engine.metrics.cycles, 4)

    def test_cpi_r_type(self):
        engine = make_engine("add x1, x2, x3")
        run_full(engine)
        self.assertAlmostEqual(engine.metrics.get_metrics()["cpi"], 4.0)

    def test_cpi_lw(self):
        engine = make_engine("lw x1, 0(x0)")
        run_full(engine)
        self.assertAlmostEqual(engine.metrics.get_metrics()["cpi"], 5.0)

    def test_cpi_mezcla_beq_addi(self):
        # beq=3 ciclos, addi=4 ciclos → total=7 ciclos, 2 instrucciones → CPI=3.5
        engine = make_engine("beq x0, x0, done\ndone:\naddi x1, x0, 1")
        run_full(engine)
        self.assertAlmostEqual(engine.metrics.get_metrics()["cpi"], 7 / 2)

    def test_step_retorna_false_al_terminar(self):
        engine = make_engine("addi x1, x0, 1")
        for _ in range(4):
            self.assertTrue(engine.step())
        self.assertFalse(engine.step())



class TestSnapshot(unittest.TestCase):

    def test_snapshot_contiene_stage(self):
        engine = make_engine("add x1, x2, x3")
        snap = engine.processor_snapshot.get_snapshot()
        self.assertIn("stage", snap)
        self.assertEqual(snap["stage"], "FETCH")

    def test_snapshot_stage_avanza_tras_step(self):
        engine = make_engine("add x1, x2, x3")
        engine.step()
        snap = engine.processor_snapshot.get_snapshot()
        self.assertEqual(snap["stage"], "DECODE")

    def test_snapshot_alu_out_tras_execute(self):
        engine = make_engine("addi x1, x0, 7")
        step_n(engine, 3)  # FETCH → DECODE → EXECUTE
        snap = engine.processor_snapshot.get_snapshot()
        self.assertEqual(snap["alu_out"], 7)

    def test_snapshot_ir_se_fija_tras_fetch(self):
        engine = make_engine("addi x1, x0, 5")
        engine.step()  # FETCH
        snap = engine.processor_snapshot.get_snapshot()
        self.assertIsNotNone(snap["ir"])

    def test_snapshot_mdr_tras_stage_memory_en_lw(self):
        # addi(4) + sw(4) + lw[FETCH+DECODE+EXECUTE+MEMORY] = 4+4+4=12 steps
        engine = make_engine("addi x1, x0, 99\nsw x1, 0(x0)\nlw x2, 0(x0)")
        step_n(engine, 12)
        snap = engine.processor_snapshot.get_snapshot()
        self.assertEqual(snap["stage"], "WRITEBACK")
        self.assertEqual(snap["mdr"], 99)

    def test_snapshot_contiene_pc_y_metricas(self):
        engine = make_engine("addi x1, x0, 1")
        snap = engine.processor_snapshot.get_snapshot()
        self.assertIn("pc", snap)
        self.assertIn("metrics", snap)
        self.assertIn("control_signals", snap)




class TestFullProgram(unittest.TestCase):

    ASM_PATH = Path(__file__).with_name("multi_cycle_reference.asm")

    def setUp(self):
        source_code = self.ASM_PATH.read_text(encoding="utf-8")
        self.engine = make_engine(source_code)
        run_full(self.engine)

    def test_valores_de_registros(self):
        expected = {
            "x1": 4, "x2": 7, "x3": 11, "x4": 7, "x5": 3,
            "x6": 7, "x7": 12, "x8": 11, "x9": 0, "x10": 12,
        }
        for reg, value in expected.items():
            with self.subTest(reg=reg):
                self.assertEqual(self.engine.register_bank.read(reg), value)

    def test_valor_en_memoria(self):
        self.assertEqual(self.engine.memory.load_word(0), 11)

    def test_conteo_instrucciones(self):
        self.assertEqual(self.engine.metrics.instructions, 11)

    def test_conteo_ciclos(self):
        # addi(4)×3 + add(4) + sub(4) + and(4) + or(4) + xor(4) + sw(4) + lw(5) + beq(3) + addi(4) = 44
        self.assertEqual(self.engine.metrics.cycles, 44)

    def test_cpi_del_programa(self):
        metrics = self.engine.metrics.get_metrics()
        self.assertAlmostEqual(metrics["cpi"], 44 / 11)


if __name__ == "__main__":
    unittest.main()
