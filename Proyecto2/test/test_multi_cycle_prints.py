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

from src.processors.multi_cycle import MultiCycleEngine  # noqa: E402

ASM_PATH = Path(__file__).with_name("multi_cycle_reference.asm")


def run_debug_program() -> None:
    source_code = ASM_PATH.read_text(encoding="utf-8")
    engine = MultiCycleEngine()
    engine.load_program(source_code)

    print(f"Archivo ASM : {ASM_PATH}")
    print(f"Instrucciones: {engine.instruction_memory.get_snapshot()}")
    print(f"Labels      : {engine.labels}")
    print()

    max_steps = 200
    step_number = 0

    while True:
        snap_before = engine.processor_snapshot.get_snapshot()
        stage_before = snap_before["stage"]
        pc_before = engine.pc

        if not engine.step():
            break

        snap = engine.processor_snapshot.get_snapshot()
        print(
            f"Ciclo {step_number + 1:3d} | "
            f"{stage_before:<10} -> {snap['stage']:<10} | "
            f"pc={pc_before}"
        )
        print(
            f"          IR={snap['ir']!r:<35} "
            f"A={snap['a']:6}  B={snap['b']:6}  "
            f"ALUOut={snap['alu_out']:8}  MDR={snap['mdr']:6}"
        )

        step_number += 1
        if step_number >= max_steps:
            print(f"ERROR: limite de {max_steps} pasos alcanzado.")
            break

    print()
    print("=" * 65)
    print("Resumen final")
    print("=" * 65)

    expected_registers = {
        "x1": 4, "x2": 7, "x3": 11, "x4": 7, "x5": 3,
        "x6": 7, "x7": 12, "x8": 11, "x9": 0, "x10": 12,
    }
    expected_memory = {0: 11}
    expected_metrics = {
        "cycles": 44, "instructions": 11,
        "cpi": 44 / 11, "ipc": 11 / 44,
    }

    all_ok = True

    for reg, expected in expected_registers.items():
        actual = engine.register_bank.read(reg)
        ok = actual == expected
        all_ok = all_ok and ok
        print(f"  {'OK ' if ok else 'ERR'} {reg}: esperado={expected}, actual={actual}")

    for address, expected in expected_memory.items():
        actual = engine.memory.load_word(address)
        ok = actual == expected
        all_ok = all_ok and ok
        print(f"  {'OK ' if ok else 'ERR'} memoria[{address}]: esperado={expected}, actual={actual}")

    metrics = engine.metrics.get_metrics()
    for key, expected in expected_metrics.items():
        actual = metrics[key]
        ok = abs(actual - expected) < 1e-9
        all_ok = all_ok and ok
        print(f"  {'OK ' if ok else 'ERR'} {key}: esperado={expected:.4f}, actual={actual:.4f}")

    print()
    print("Resultado:", "TODOS OK" if all_ok else "HAY ERRORES")


if __name__ == "__main__":
    run_debug_program()
