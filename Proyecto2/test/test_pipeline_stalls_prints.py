import sys
import importlib.util
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

ASM_PATH = Path(__file__).with_name("pipeline_stalls_reference.asm")


def _opcode(stage_dict: dict) -> str:
    op = stage_dict.get("opcode") or stage_dict.get("instruction")
    return str(op)[:18] if op else "bubble"


def run_reference_report() -> None:
    source_code = ASM_PATH.read_text(encoding="utf-8")
    engine = PipelineStallEngine()
    engine.load_program(source_code)

    print(f"Archivo ASM : {ASM_PATH}")
    print(f"Instrucciones: {engine.instruction_memory.get_snapshot()}")
    print()
    print(
        f"{'Ciclo':>5} | {'IF/ID':<22} {'ID/EX':<12} {'EX/MEM':<12} {'MEM/WB':<12} | {'Info'}"
    )
    print("-" * 90)

    cycle = 0
    max_steps = 300
    while cycle < max_steps:
        if not engine.step():
            break
        cycle += 1
        snap = engine.processor_snapshot.get_snapshot()

        if_id_str = snap["if_id"]["instruction"] or "bubble"
        id_ex_str = _opcode(snap["id_ex"])
        ex_mem_str = _opcode(snap["ex_mem"])
        mem_wb_str = _opcode(snap["mem_wb"])

        info = ""
        if snap["stalled"]:
            info = "STALL"
        elif snap["flushed"]:
            info = "FLUSH"

        print(
            f"{cycle:>5} | {if_id_str:<22} {id_ex_str:<12} {ex_mem_str:<12} {mem_wb_str:<12} | {info}"
        )

    print()
    print("=" * 65)
    print("Resumen final")
    print("=" * 65)

    expected_registers = {
        "x1": 4, "x2": 7, "x3": 11, "x4": 7, "x5": 3,
        "x6": 7, "x7": 12, "x8": 11, "x9": 0, "x10": 12,
    }
    expected_memory = {0: 11}

    all_ok = True
    for reg, expected in expected_registers.items():
        actual = engine.register_bank.read(reg)
        ok = actual == expected
        all_ok = all_ok and ok
        print(f"  {'OK ' if ok else 'ERR'} {reg}: esperado={expected}, actual={actual}")

    for addr, expected in expected_memory.items():
        actual = engine.memory.load_word(addr)
        ok = actual == expected
        all_ok = all_ok and ok
        print(f"  {'OK ' if ok else 'ERR'} memoria[{addr}]: esperado={expected}, actual={actual}")

    metrics = engine.metrics.get_metrics()
    print()
    print(f"  Ciclos      : {metrics['cycles']}")
    print(f"  Instrucciones: {metrics['instructions']}")
    print(f"  Stalls      : {metrics['stalls']}")
    print(f"  CPI         : {metrics['cpi']:.4f}")
    print(f"  IPC         : {metrics['ipc']:.4f}")
    print()
    print("Resultado:", "TODOS OK" if all_ok else "HAY ERRORES")


if __name__ == "__main__":
    run_reference_report()
