from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processors.single_cycle import SingleCycleEngine


ASM_PATH = Path(__file__).with_name("single_cycle_reference.asm")


def print_registers(engine: SingleCycleEngine, registers: list[str]) -> None:
    values = ", ".join(
        f"{register}={engine.register_bank.read(register)}" for register in registers
    )
    print(f"    registros: {values}")


def run_debug_program() -> None:
    source_code = ASM_PATH.read_text(encoding="utf-8")
    engine = SingleCycleEngine()
    engine.load_program(source_code)

    print(f"Archivo ASM: {ASM_PATH}")
    print(f"Instrucciones limpias: {engine.instruction_memory.get_snapshot()}")
    print(f"Labels: {engine.labels}")
    print()

    max_steps = 50
    step_number = 0

    while not engine.is_program_finished() and step_number < max_steps:
        raw_instruction = engine.instruction_memory.fetch(engine.pc)
        print(f"Paso {step_number + 1}: pc={engine.pc}, instr='{raw_instruction}'")
        engine.step()
        print(f"    pc despues={engine.pc}")
        print_registers(engine, ["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9", "x10"])
        print(f"    memoria[0]={engine.memory.load_word(0)}")
        print(f"    metricas={engine.metrics.get_metrics()}")
        print()
        step_number += 1

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
    expected_metrics = {"cycles": 11, "instructions": 11, "cpi": 1.0, "ipc": 1.0}

    print("Resumen final")
    for register, expected_value in expected_registers.items():
        actual_value = engine.register_bank.read(register)
        status = "OK" if actual_value == expected_value else "ERROR"
        print(f"  {status} {register}: esperado={expected_value}, actual={actual_value}")

    for address, expected_value in expected_memory.items():
        actual_value = engine.memory.load_word(address)
        status = "OK" if actual_value == expected_value else "ERROR"
        print(f"  {status} memoria[{address}]: esperado={expected_value}, actual={actual_value}")

    metrics = engine.metrics.get_metrics()
    for metric, expected_value in expected_metrics.items():
        actual_value = metrics[metric]
        status = "OK" if actual_value == expected_value else "ERROR"
        print(f"  {status} {metric}: esperado={expected_value}, actual={actual_value}")

    if step_number >= max_steps:
        print(f"  ERROR se alcanzo el limite de {max_steps} pasos; posible loop infinito.")


if __name__ == "__main__":
    run_debug_program()
