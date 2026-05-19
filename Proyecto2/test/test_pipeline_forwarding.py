"""Suite exhaustiva para PipelineForwardingEngine.

La suite cubre tres niveles:
- unidad de forwarding,
- deteccion load-use,
- integracion ciclo a ciclo del engine.
"""

import importlib.util
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


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

from src.assembler import ControlSignals, Instruction  # noqa: E402
from src.core.decoder import Decoder  # noqa: E402
from src.pipeline.forwarding_unit import resolve_forwarding  # noqa: E402
from src.pipeline.hazard_detection import detect_load_use_hazard  # noqa: E402
from src.pipeline.pipeline_registers import IF_ID, ID_EX, EX_MEM, MEM_WB  # noqa: E402
from src.processors.pipeline_forwarding import PipelineForwardingEngine  # noqa: E402
from src.processors.pipeline_stalls import PipelineStallEngine  # noqa: E402


def make_engine(source_code: str) -> PipelineForwardingEngine:
    engine = PipelineForwardingEngine()
    engine.load_program(source_code)
    return engine


def run_full(engine, max_steps: int = 1000) -> int:
    steps = 0
    while steps < max_steps:
        if not engine.step():
            return steps
        steps += 1
    raise AssertionError(f"El engine no termino despues de {max_steps} ciclos.")


def collect_snapshots(engine, max_steps: int = 1000) -> list[dict]:
    snapshots = []
    steps = 0
    while steps < max_steps:
        if not engine.step():
            return snapshots
        snapshots.append(engine.processor_snapshot.get_snapshot())
        steps += 1
    raise AssertionError(f"El engine no termino despues de {max_steps} ciclos.")


def count_flag(snapshots: list[dict], flag: str) -> int:
    return sum(1 for snap in snapshots if snap[flag])


def saw_forwarding(snapshots: list[dict], operand: str, source: str) -> bool:
    key = f"forward_{operand}"
    return any(snap[key] == source for snap in snapshots)


def instr(opcode: str, rd=None, rs1=None, rs2=None, imm=None) -> Instruction:
    return Instruction(opcode=opcode, rd=rd, rs1=rs1, rs2=rs2, imm=imm)


def reg_write() -> ControlSignals:
    return ControlSignals(reg_write=True, result_src="alu", alu_control="ADD")


def load_ctrl() -> ControlSignals:
    return ControlSignals(
        reg_write=True,
        mem_read=True,
        alu_src="imm",
        result_src="memory",
        alu_control="ADD",
    )


def store_ctrl() -> ControlSignals:
    return ControlSignals(mem_write=True, alu_src="imm", result_src="none")


class TestForwardingUnit(unittest.TestCase):

    def test_burbuja_conserva_operandos_y_fuentes_default(self):
        decision = resolve_forwarding(ID_EX(a=11, b=22), EX_MEM(), MEM_WB())

        self.assertEqual(decision.a, 11)
        self.assertEqual(decision.b, 22)
        self.assertEqual(decision.forward_a, "ID/EX")
        self.assertEqual(decision.forward_b, "ID/EX")

    def test_forwarding_desde_ex_mem_para_ambos_operandos(self):
        id_ex = ID_EX(
            instruction=instr("add", rd="x9", rs1="x1", rs2="x1"),
            control=reg_write(),
            a=0,
            b=0,
            rs1="x1",
            rs2="x1",
        )
        ex_mem = EX_MEM(
            instruction=instr("addi", rd="x1", rs1="x0", imm=7),
            control=reg_write(),
            alu_result=7,
            rd="x1",
        )

        decision = resolve_forwarding(id_ex, ex_mem, MEM_WB())

        self.assertEqual(decision.a, 7)
        self.assertEqual(decision.b, 7)
        self.assertEqual(decision.forward_a, "EX/MEM")
        self.assertEqual(decision.forward_b, "EX/MEM")

    def test_forwarding_desde_mem_wb_usa_mem_data_para_lw(self):
        id_ex = ID_EX(
            instruction=instr("add", rd="x3", rs1="x1", rs2="x2"),
            control=reg_write(),
            a=0,
            b=9,
            rs1="x1",
            rs2="x2",
        )
        mem_wb = MEM_WB(
            instruction=instr("lw", rd="x1", rs1="x0", imm=0),
            control=load_ctrl(),
            alu_result=0,
            mem_data=42,
            rd="x1",
        )

        decision = resolve_forwarding(id_ex, EX_MEM(), mem_wb)

        self.assertEqual(decision.a, 42)
        self.assertEqual(decision.b, 9)
        self.assertEqual(decision.forward_a, "MEM/WB")
        self.assertEqual(decision.forward_b, "ID/EX")

    def test_ex_mem_tiene_prioridad_sobre_mem_wb(self):
        id_ex = ID_EX(
            instruction=instr("add", rd="x2", rs1="x1", rs2="x0"),
            control=reg_write(),
            a=0,
            b=0,
            rs1="x1",
            rs2="x0",
        )
        ex_mem = EX_MEM(
            instruction=instr("addi", rd="x1", rs1="x1", imm=2),
            control=reg_write(),
            alu_result=3,
            rd="x1",
        )
        mem_wb = MEM_WB(
            instruction=instr("addi", rd="x1", rs1="x0", imm=1),
            control=reg_write(),
            alu_result=1,
            rd="x1",
        )

        decision = resolve_forwarding(id_ex, ex_mem, mem_wb)

        self.assertEqual(decision.a, 3)
        self.assertEqual(decision.forward_a, "EX/MEM")

    def test_no_forwarding_desde_ex_mem_para_lw_ni_desde_x0(self):
        id_ex = ID_EX(
            instruction=instr("add", rd="x3", rs1="x1", rs2="x0"),
            control=reg_write(),
            a=5,
            b=0,
            rs1="x1",
            rs2="x0",
        )
        ex_mem = EX_MEM(
            instruction=instr("lw", rd="x1", rs1="x0", imm=0),
            control=load_ctrl(),
            alu_result=100,
            rd="x1",
        )
        mem_wb = MEM_WB(
            instruction=instr("addi", rd="x0", rs1="x0", imm=99),
            control=reg_write(),
            alu_result=99,
            rd="x0",
        )

        decision = resolve_forwarding(id_ex, ex_mem, mem_wb)

        self.assertEqual(decision.a, 5)
        self.assertEqual(decision.b, 0)
        self.assertEqual(decision.forward_a, "ID/EX")
        self.assertEqual(decision.forward_b, "ID/EX")

    def test_no_forwarding_desde_instruccion_que_no_escribe_registro(self):
        id_ex = ID_EX(
            instruction=instr("add", rd="x3", rs1="x1", rs2="x2"),
            control=reg_write(),
            a=4,
            b=5,
            rs1="x1",
            rs2="x2",
        )
        ex_mem = EX_MEM(
            instruction=instr("sw", rs1="x0", rs2="x1", imm=0),
            control=store_ctrl(),
            alu_result=0,
            b=99,
            rd=None,
        )

        decision = resolve_forwarding(id_ex, ex_mem, MEM_WB())

        self.assertEqual(decision.a, 4)
        self.assertEqual(decision.b, 5)
        self.assertEqual(decision.forward_a, "ID/EX")
        self.assertEqual(decision.forward_b, "ID/EX")


class TestLoadUseHazardUnit(unittest.TestCase):

    def setUp(self):
        self.decoder = Decoder()

    def test_detecta_load_use_en_rs1(self):
        if_id = IF_ID("add x2 x1 x0")
        id_ex = ID_EX(
            instruction=instr("lw", rd="x1", rs1="x0", imm=0),
            control=load_ctrl(),
            rd="x1",
        )

        self.assertTrue(detect_load_use_hazard(if_id, id_ex, self.decoder))

    def test_detecta_load_use_en_rs2_y_store_data(self):
        if_id = IF_ID("sw x1 4(x0)")
        id_ex = ID_EX(
            instruction=instr("lw", rd="x1", rs1="x0", imm=0),
            control=load_ctrl(),
            rd="x1",
        )

        self.assertTrue(detect_load_use_hazard(if_id, id_ex, self.decoder))

    def test_no_detecta_si_productor_no_es_lw(self):
        if_id = IF_ID("add x2 x1 x0")
        id_ex = ID_EX(
            instruction=instr("addi", rd="x1", rs1="x0", imm=1),
            control=reg_write(),
            rd="x1",
        )

        self.assertFalse(detect_load_use_hazard(if_id, id_ex, self.decoder))

    def test_no_detecta_si_consumidor_no_usa_rd(self):
        if_id = IF_ID("add x2 x3 x4")
        id_ex = ID_EX(
            instruction=instr("lw", rd="x1", rs1="x0", imm=0),
            control=load_ctrl(),
            rd="x1",
        )

        self.assertFalse(detect_load_use_hazard(if_id, id_ex, self.decoder))

    def test_no_detecta_x0_o_burbujas(self):
        if_id = IF_ID("add x2 x0 x0")
        id_ex = ID_EX(
            instruction=instr("lw", rd="x0", rs1="x0", imm=0),
            control=load_ctrl(),
            rd="x0",
        )

        self.assertFalse(detect_load_use_hazard(if_id, id_ex, self.decoder))
        self.assertFalse(detect_load_use_hazard(IF_ID(), id_ex, self.decoder))
        self.assertFalse(detect_load_use_hazard(if_id, ID_EX(), self.decoder))


class TestPipelineForwardingBasicFlow(unittest.TestCase):

    def test_instrucciones_independientes_no_generan_stalls(self):
        engine = make_engine("addi x1, x0, 1\naddi x2, x0, 2")
        run_full(engine)

        self.assertEqual(engine.metrics.instructions, 2)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertEqual(engine.metrics.hazards, 0)
        self.assertEqual(engine.register_bank.read("x1"), 1)
        self.assertEqual(engine.register_bank.read("x2"), 2)

    def test_snapshot_contiene_campos_de_pipeline_y_forwarding(self):
        engine = make_engine("addi x1, x0, 1")
        snap = engine.processor_snapshot.get_snapshot()

        for key in ("if_id", "id_ex", "ex_mem", "mem_wb"):
            self.assertIn(key, snap)
        for key in ("forward_a", "forward_b", "stalled", "flushed"):
            self.assertIn(key, snap)

    def test_pipeline_drena_despues_de_la_ultima_instruccion(self):
        engine = make_engine("addi x1, x0, 9")
        steps = run_full(engine)
        snap = engine.processor_snapshot.get_snapshot()

        self.assertEqual(engine.register_bank.read("x1"), 9)
        self.assertEqual(engine.metrics.instructions, 1)
        self.assertGreater(steps, 1)
        self.assertIsNone(snap["if_id"]["instruction"])
        self.assertIsNone(snap["id_ex"]["opcode"])
        self.assertIsNone(snap["ex_mem"]["opcode"])
        self.assertIsNone(snap["mem_wb"]["opcode"])


class TestALUForwardingIntegration(unittest.TestCase):

    def test_ex_mem_forwarding_para_rs1_y_rs2_mismo_registro(self):
        engine = make_engine("addi x1, x0, 7\nadd x2, x1, x1")
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 14)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertTrue(saw_forwarding(snapshots, "a", "EX/MEM"))
        self.assertTrue(saw_forwarding(snapshots, "b", "EX/MEM"))

    def test_mem_wb_forwarding_con_una_instruccion_intermedia(self):
        engine = make_engine(
            "addi x1, x0, 5\n"
            "addi x7, x0, 0\n"
            "add x2, x1, x0"
        )
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 5)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertTrue(saw_forwarding(snapshots, "a", "MEM/WB"))

    def test_forwarding_prioriza_resultado_mas_reciente(self):
        engine = make_engine(
            "addi x1, x0, 1\n"
            "addi x1, x1, 2\n"
            "add x2, x1, x0"
        )
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x1"), 3)
        self.assertEqual(engine.register_bank.read("x2"), 3)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertTrue(saw_forwarding(snapshots, "a", "EX/MEM"))

    def test_cadena_larga_de_dependencias_alu_no_inserta_stalls(self):
        engine = make_engine(
            "addi x1, x0, 1\n"
            "addi x2, x1, 2\n"
            "addi x3, x2, 3\n"
            "addi x4, x3, 4\n"
            "add x5, x4, x3"
        )
        run_full(engine)

        self.assertEqual(engine.register_bank.read("x1"), 1)
        self.assertEqual(engine.register_bank.read("x2"), 3)
        self.assertEqual(engine.register_bank.read("x3"), 6)
        self.assertEqual(engine.register_bank.read("x4"), 10)
        self.assertEqual(engine.register_bank.read("x5"), 16)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_forwarding_con_inmediato_negativo(self):
        engine = make_engine("addi x1, x0, -3\nadd x2, x1, x1")
        run_full(engine)

        self.assertEqual(engine.register_bank.read("x1"), -3)
        self.assertEqual(engine.register_bank.read("x2"), -6)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_x0_no_se_forwardea_ni_se_modifica(self):
        engine = make_engine("addi x0, x0, 99\nadd x1, x0, x0")
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x0"), 0)
        self.assertEqual(engine.register_bank.read("x1"), 0)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertFalse(saw_forwarding(snapshots, "a", "EX/MEM"))
        self.assertFalse(saw_forwarding(snapshots, "b", "EX/MEM"))


class TestLoadUseIntegration(unittest.TestCase):

    def test_lw_uso_inmediato_inserta_exactamente_un_stall(self):
        engine = make_engine("lw x1, 0(x0)\nadd x2, x1, x0")
        engine.memory.store_word(0, 42)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x1"), 42)
        self.assertEqual(engine.register_bank.read("x2"), 42)
        self.assertEqual(engine.metrics.stalls, 1)
        self.assertEqual(count_flag(snapshots, "stalled"), 1)
        self.assertTrue(saw_forwarding(snapshots, "a", "MEM/WB"))

    def test_lw_con_instruccion_intermedia_no_inserta_stall(self):
        engine = make_engine(
            "lw x1, 0(x0)\n"
            "addi x3, x0, 9\n"
            "add x2, x1, x0"
        )
        engine.memory.store_word(0, 31)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 31)
        self.assertEqual(engine.register_bank.read("x3"), 9)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertTrue(saw_forwarding(snapshots, "a", "MEM/WB"))

    def test_lw_a_sw_data_inserta_un_stall_y_guarda_valor_cargado(self):
        engine = make_engine("lw x1, 0(x0)\nsw x1, 4(x0)")
        engine.memory.store_word(0, 77)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.memory.load_word(4), 77)
        self.assertEqual(engine.metrics.stalls, 1)
        self.assertEqual(count_flag(snapshots, "stalled"), 1)
        self.assertTrue(saw_forwarding(snapshots, "b", "MEM/WB"))

    def test_lw_a_sw_base_inserta_un_stall_y_usa_base_cargada(self):
        engine = make_engine("lw x1, 0(x0)\nsw x2, 0(x1)")
        engine.memory.store_word(0, 8)
        engine.register_bank.write("x2", 55)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.memory.load_word(8), 55)
        self.assertEqual(engine.metrics.stalls, 1)
        self.assertTrue(saw_forwarding(snapshots, "a", "MEM/WB"))

    def test_dos_load_use_consecutivos_cuentan_dos_stalls(self):
        engine = make_engine(
            "lw x1, 0(x0)\n"
            "add x2, x1, x0\n"
            "lw x3, 4(x0)\n"
            "add x4, x3, x2"
        )
        engine.memory.store_word(0, 10)
        engine.memory.store_word(4, 20)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 10)
        self.assertEqual(engine.register_bank.read("x4"), 30)
        self.assertEqual(engine.metrics.stalls, 2)
        self.assertEqual(count_flag(snapshots, "stalled"), 2)


class TestStoreLoadMemoryIntegration(unittest.TestCase):

    def test_alu_a_sw_data_se_resuelve_sin_stall(self):
        engine = make_engine("addi x1, x0, 77\nsw x1, 0(x0)")
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.memory.load_word(0), 77)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertTrue(saw_forwarding(snapshots, "b", "EX/MEM"))

    def test_alu_a_sw_base_y_data_se_resuelve_sin_stall(self):
        engine = make_engine(
            "addi x1, x0, 4\n"
            "addi x2, x0, 88\n"
            "sw x2, 0(x1)"
        )
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.memory.load_word(4), 88)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertTrue(saw_forwarding(snapshots, "a", "MEM/WB"))
        self.assertTrue(saw_forwarding(snapshots, "b", "EX/MEM"))

    def test_alu_a_lw_base_se_resuelve_sin_stall(self):
        engine = make_engine("addi x1, x0, 4\nlw x2, 0(x1)")
        engine.memory.store_word(4, 123)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 123)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertTrue(saw_forwarding(snapshots, "a", "EX/MEM"))

    def test_store_load_roundtrip_con_direccion_forwardeada(self):
        engine = make_engine(
            "addi x1, x0, 12\n"
            "addi x2, x0, 66\n"
            "sw x2, 0(x1)\n"
            "lw x3, 0(x1)"
        )
        run_full(engine)

        self.assertEqual(engine.memory.load_word(12), 66)
        self.assertEqual(engine.register_bank.read("x3"), 66)
        self.assertEqual(engine.metrics.stalls, 0)


class TestBranchAndFlushIntegration(unittest.TestCase):

    def test_beq_tomado_limpia_instruccion_especulativa(self):
        engine = make_engine("beq x0, x0, done\naddi x1, x0, 99\ndone:\naddi x2, x0, 1")
        snapshots = collect_snapshots(engine)

        self.assertEqual(count_flag(snapshots, "flushed"), 1)
        self.assertEqual(engine.register_bank.read("x1"), 0)
        self.assertEqual(engine.register_bank.read("x2"), 1)

    def test_beq_no_tomado_no_hace_flush(self):
        engine = make_engine(
            "addi x1, x0, 1\n"
            "addi x2, x0, 2\n"
            "beq x1, x2, skip\n"
            "addi x3, x0, 7\n"
            "skip:\n"
            "addi x4, x0, 9"
        )
        snapshots = collect_snapshots(engine)

        self.assertEqual(count_flag(snapshots, "flushed"), 0)
        self.assertEqual(engine.register_bank.read("x3"), 7)
        self.assertEqual(engine.register_bank.read("x4"), 9)
        self.assertEqual(engine.metrics.stalls, 0)

    def test_branch_tomado_usa_forwarding_desde_ex_mem(self):
        engine = make_engine(
            "addi x1, x0, 1\n"
            "bne x1, x0, done\n"
            "addi x2, x0, 99\n"
            "done:\n"
            "addi x3, x0, 5"
        )
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 0)
        self.assertEqual(engine.register_bank.read("x3"), 5)
        self.assertEqual(engine.metrics.stalls, 0)
        self.assertEqual(count_flag(snapshots, "flushed"), 1)
        self.assertTrue(saw_forwarding(snapshots, "a", "EX/MEM"))

    def test_branch_no_tomado_usa_forwarding_desde_ex_mem(self):
        engine = make_engine(
            "addi x1, x0, 1\n"
            "beq x1, x0, skip\n"
            "addi x2, x0, 9\n"
            "skip:\n"
            "addi x3, x0, 4"
        )
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 9)
        self.assertEqual(engine.register_bank.read("x3"), 4)
        self.assertEqual(count_flag(snapshots, "flushed"), 0)
        self.assertTrue(saw_forwarding(snapshots, "a", "EX/MEM"))

    def test_branch_load_use_inserta_stall_y_luego_forwarding(self):
        engine = make_engine(
            "lw x1, 0(x0)\n"
            "beq x1, x0, done\n"
            "addi x2, x0, 99\n"
            "done:\n"
            "addi x3, x0, 5"
        )
        engine.memory.store_word(0, 0)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x2"), 0)
        self.assertEqual(engine.register_bank.read("x3"), 5)
        self.assertEqual(engine.metrics.stalls, 1)
        self.assertEqual(count_flag(snapshots, "stalled"), 1)
        self.assertEqual(count_flag(snapshots, "flushed"), 1)
        self.assertTrue(saw_forwarding(snapshots, "a", "MEM/WB"))


class TestFullProgramsAndMetrics(unittest.TestCase):

    ASM_PATH = Path(__file__).with_name("pipeline_stalls_reference.asm")

    def test_programa_completo_resultados_metricas_y_menos_stalls(self):
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

        forwarding_metrics = forwarding_engine.metrics.get_metrics()
        stall_metrics = stall_engine.metrics.get_metrics()

        self.assertEqual(forwarding_engine.memory.load_word(0), 11)
        self.assertEqual(forwarding_engine.metrics.instructions, 11)
        self.assertEqual(forwarding_engine.metrics.stalls, 1)
        self.assertEqual(forwarding_engine.metrics.hazards, 0)
        self.assertLess(forwarding_engine.metrics.stalls, stall_engine.metrics.stalls)
        self.assertLess(forwarding_metrics["cycles"], stall_metrics["cycles"])
        self.assertLess(forwarding_metrics["cpi"], stall_metrics["cpi"])
        self.assertGreater(forwarding_metrics["ipc"], stall_metrics["ipc"])

    def test_programa_mixto_con_varios_forwardings_y_load_use(self):
        source = (
            "addi x1, x0, 4\n"
            "addi x2, x0, 8\n"
            "add x3, x1, x2\n"
            "sw x3, 0(x1)\n"
            "lw x4, 0(x1)\n"
            "add x5, x4, x3\n"
            "bne x5, x0, done\n"
            "addi x6, x0, 99\n"
            "done:\n"
            "xor x7, x5, x3"
        )
        engine = make_engine(source)
        snapshots = collect_snapshots(engine)

        self.assertEqual(engine.register_bank.read("x3"), 12)
        self.assertEqual(engine.memory.load_word(4), 12)
        self.assertEqual(engine.register_bank.read("x4"), 12)
        self.assertEqual(engine.register_bank.read("x5"), 24)
        self.assertEqual(engine.register_bank.read("x6"), 0)
        self.assertEqual(engine.register_bank.read("x7"), 20)
        self.assertEqual(engine.metrics.stalls, 1)
        self.assertEqual(count_flag(snapshots, "flushed"), 1)
        self.assertTrue(any(snap["forward_a"] != "ID/EX" for snap in snapshots))
        self.assertTrue(any(snap["forward_b"] != "ID/EX" for snap in snapshots))


if __name__ == "__main__":
    unittest.main(verbosity=2)
