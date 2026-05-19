"""Tests para PipelineForwardingEngine."""

import importlib.util
import sys
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

from src.processors.pipeline_forwarding import PipelineForwardingEngine  # noqa: E402
from src.processors.pipeline_stalls import PipelineStallEngine  # noqa: E402


def make_engine(source_code: str) -> PipelineForwardingEngine:
    engine = PipelineForwardingEngine()
    engine.load_program(source_code)
    return engine


def run_full(engine, max_steps: int = 1000) -> None:
    steps = 0
    while steps < max_steps:
        if not engine.step():
            break
        steps += 1


class TestForwardingBasicFlow(unittest.TestCase):

    def test_instrucciones_independientes_no_generan_stalls(self):
        engine = make_engine("addi x1, x0, 1\naddi x2, x0, 2")
        run_full(engine)

        self.assertEqual(engine.metrics.stalls, 0)
        self.assertEqual(engine.register_bank.read("x1"), 1)
        self.assertEqual(engine.register_bank.read("x2"), 2)

    def test_snapshot_contiene_forwarding(self):
        engine = make_engine("addi x1, x0, 1")
        snap = engine.processor_snapshot.get_snapshot()

        self.assertIn("forward_a", snap)
        self.assertIn("forward_b", snap)
        self.assertIn("stalled", snap)
        self.assertIn("flushed", snap)


class TestRawForwarding(unittest.TestCase):

    def test_alu_a_alu_se_resuelve_sin_stall(self):
        engine = make_engine("addi x1, x0, 5\nadd x2, x1, x0")
        run_full(engine)

        self.assertEqual(engine.register_bank.read("x2"), 5)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_prioriza_resultado_mas_reciente(self):
        engine = make_engine(
            "addi x1, x0, 1\n"
            "addi x1, x1, 2\n"
            "add x2, x1, x0"
        )
        run_full(engine)

        self.assertEqual(engine.register_bank.read("x1"), 3)
        self.assertEqual(engine.register_bank.read("x2"), 3)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_alu_a_branch_se_resuelve_con_forwarding(self):
        source = (
            "addi x1, x0, 1\n"
            "bne x1, x0, done\n"
            "addi x2, x0, 99\n"
            "done:\n"
            "addi x3, x0, 5"
        )
        engine = make_engine(source)
        run_full(engine)

        self.assertEqual(engine.register_bank.read("x2"), 0)
        self.assertEqual(engine.register_bank.read("x3"), 5)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_alu_a_sw_data_se_resuelve_con_forwarding(self):
        engine = make_engine("addi x1, x0, 77\nsw x1, 0(x0)")
        run_full(engine)

        self.assertEqual(engine.memory.load_word(0), 77)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_alu_a_sw_base_y_data_se_resuelve_con_forwarding(self):
        source = (
            "addi x1, x0, 4\n"
            "addi x2, x0, 88\n"
            "sw x2, 0(x1)"
        )
        engine = make_engine(source)
        run_full(engine)

        self.assertEqual(engine.memory.load_word(4), 88)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_snapshot_muestra_forwarding_desde_ex_mem(self):
        engine = make_engine("addi x1, x0, 5\nadd x2, x1, x0")
        saw_forward = False

        for _ in range(20):
            if not engine.step():
                break
            snap = engine.processor_snapshot.get_snapshot()
            if snap["forward_a"] == "EX/MEM":
                saw_forward = True
                break

        self.assertTrue(saw_forward)


class TestLoadUseStall(unittest.TestCase):

    def test_lw_uso_inmediato_inserta_un_stall(self):
        engine = make_engine("lw x1, 0(x0)\nadd x2, x1, x0")
        engine.memory.store_word(0, 42)
        run_full(engine)

        self.assertEqual(engine.register_bank.read("x1"), 42)
        self.assertEqual(engine.register_bank.read("x2"), 42)
        self.assertEqual(engine.metrics.stalls, 1)

    def test_lw_con_instruccion_intermedia_no_inserta_stall(self):
        engine = make_engine(
            "lw x1, 0(x0)\n"
            "addi x3, x0, 9\n"
            "add x2, x1, x0"
        )
        engine.memory.store_word(0, 31)
        run_full(engine)

        self.assertEqual(engine.register_bank.read("x2"), 31)
        self.assertEqual(engine.register_bank.read("x3"), 9)
        self.assertEqual(engine.metrics.stalls, 0)


class TestBranchFlush(unittest.TestCase):

    def test_branch_tomado_registra_flush(self):
        engine = make_engine("beq x0, x0, done\naddi x1, x0, 99\ndone:\naddi x2, x0, 1")
        flushed_seen = False

        for _ in range(50):
            if not engine.step():
                break
            snap = engine.processor_snapshot.get_snapshot()
            if snap["flushed"]:
                flushed_seen = True
                break

        run_full(engine)
        self.assertTrue(flushed_seen)
        self.assertEqual(engine.register_bank.read("x1"), 0)
        self.assertEqual(engine.register_bank.read("x2"), 1)


class TestFullProgram(unittest.TestCase):

    ASM_PATH = Path(__file__).with_name("pipeline_stalls_reference.asm")

    def test_programa_completo_y_menos_stalls_que_pipeline_stall(self):
        source_code = self.ASM_PATH.read_text(encoding="utf-8")

        forwarding_engine = make_engine(source_code)
        run_full(forwarding_engine)

        stall_engine = PipelineStallEngine()
        stall_engine.load_program(source_code)
        run_full(stall_engine)

        expected_registers = {
            "x1": 4,
            "x2": 7,
            "x3": 11,
            "x4": 7,
            "x5": 3,
            "x6": 7,
            "x7": 12,
            "x8": 11,
            "x9": 0,
            "x10": 12,
        }
        for reg, expected in expected_registers.items():
            self.assertEqual(forwarding_engine.register_bank.read(reg), expected)

        self.assertEqual(forwarding_engine.memory.load_word(0), 11)
        self.assertEqual(forwarding_engine.metrics.instructions, 11)
        self.assertLess(forwarding_engine.metrics.stalls, stall_engine.metrics.stalls)


if __name__ == "__main__":
    unittest.main()
