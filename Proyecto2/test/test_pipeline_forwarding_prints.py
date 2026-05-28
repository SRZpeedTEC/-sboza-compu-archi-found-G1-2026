import importlib.util
import os
import sys
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

from src.processors.pipeline_forwarding import PipelineForwardingEngine  # noqa: E402
from src.processors.pipeline_stalls import PipelineStallEngine  # noqa: E402

ASM_PATH = Path(__file__).with_name("pipeline_stalls_reference.asm")


def _opcode(stage_dict: dict) -> str:
    op = stage_dict.get("opcode") or stage_dict.get("instruction")
    return str(op)[:18] if op else "bubble"


def _format_info(snap: dict) -> str:
    info = []
    if snap["stalled"]:
        info.append("STALL")
    if snap["flushed"]:
        info.append("FLUSH")
    if snap["forward_a"] != "ID/EX":
        info.append(f"A<-{snap['forward_a']}")
    if snap["forward_b"] != "ID/EX":
        info.append(f"B<-{snap['forward_b']}")
    return ", ".join(info)


def _run_engine(engine, max_steps: int = 300) -> int:
    cycle = 0
    while cycle < max_steps:
        if not engine.step():
            break
        cycle += 1
        snap = engine.processor_snapshot.get_snapshot()

        if_id_str = snap["if_id"]["instruction"] or "bubble"
        id_ex_str = _opcode(snap["id_ex"])
        ex_mem_str = _opcode(snap["ex_mem"])
        mem_wb_str = _opcode(snap["mem_wb"])

        print(
            f"{cycle:>5} | "
            f"{if_id_str:<22} "
            f"{id_ex_str:<12} "
            f"{ex_mem_str:<12} "
            f"{mem_wb_str:<12} | "
            f"{_format_info(snap)}"
        )
    return cycle


def _run_without_prints(engine, max_steps: int = 300) -> None:
    steps = 0
    while steps < max_steps:
        if not engine.step():
            break
        steps += 1


def _print_summary(forwarding_engine: PipelineForwardingEngine) -> None:
    print()
    print("=" * 72)
    print("Resumen final - Pipeline con forwarding")
    print("=" * 72)

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
    expected_memory = {0: 11}

    all_ok = True
    for reg, expected in expected_registers.items():
        actual = forwarding_engine.register_bank.read(reg)
        ok = actual == expected
        all_ok = all_ok and ok
        print(f"  {'OK ' if ok else 'ERR'} {reg}: esperado={expected}, actual={actual}")

    for addr, expected in expected_memory.items():
        actual = forwarding_engine.memory.load_word(addr)
        ok = actual == expected
        all_ok = all_ok and ok
        print(f"  {'OK ' if ok else 'ERR'} memoria[{addr}]: esperado={expected}, actual={actual}")

    metrics = forwarding_engine.metrics.get_metrics()
    print()
    print(f"  Ciclos        : {metrics['cycles']}")
    print(f"  Instrucciones : {metrics['instructions']}")
    print(f"  Stalls        : {metrics['stalls']}")
    print(f"  CPI           : {metrics['cpi']:.4f}")
    print(f"  IPC           : {metrics['ipc']:.4f}")
    print()
    print("Resultado:", "TODOS OK" if all_ok else "HAY ERRORES")


def _print_comparison(source_code: str, forwarding_engine: PipelineForwardingEngine) -> None:
    stall_engine = PipelineStallEngine()
    stall_engine.load_program(source_code)
    _run_without_prints(stall_engine)

    forwarding_metrics = forwarding_engine.metrics.get_metrics()
    stall_metrics = stall_engine.metrics.get_metrics()

    print()
    print("=" * 72)
    print("Comparacion contra pipeline con stalls")
    print("=" * 72)
    print(f"  Forwarding - ciclos: {forwarding_metrics['cycles']}, stalls: {forwarding_metrics['stalls']}, CPI: {forwarding_metrics['cpi']:.4f}")
    print(f"  Stalls     - ciclos: {stall_metrics['cycles']}, stalls: {stall_metrics['stalls']}, CPI: {stall_metrics['cpi']:.4f}")
    print()
    print("Lectura:")
    print("  - A<-EX/MEM o B<-EX/MEM significa que EX recibio un resultado recien calculado.")
    print("  - A<-MEM/WB o B<-MEM/WB significa que EX recibio un valor que estaba por escribirse.")
    print("  - STALL aparece solo cuando forwarding no alcanza, por ejemplo load-use.")
    print("  - FLUSH aparece cuando un branch tomado limpia instrucciones especulativas.")


def run_reference_report() -> None:
    source_code = ASM_PATH.read_text(encoding="utf-8")
    engine = PipelineForwardingEngine()
    engine.load_program(source_code)

    print(f"Archivo ASM : {ASM_PATH}")
    print(f"Instrucciones: {engine.instruction_memory.get_snapshot()}")
    print()
    print(
        f"{'Ciclo':>5} | "
        f"{'IF/ID':<22} "
        f"{'ID/EX':<12} "
        f"{'EX/MEM':<12} "
        f"{'MEM/WB':<12} | "
        f"{'Info'}"
    )
    print("-" * 100)

    _run_engine(engine)
    _print_summary(engine)
    _print_comparison(source_code, engine)


if __name__ == "__main__":
    run_reference_report()
