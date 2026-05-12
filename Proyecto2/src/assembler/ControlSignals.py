from dataclasses import asdict, dataclass


@dataclass(slots=True)
class ControlSignals:
    """Senales de control generadas para una instruccion.

    Se guardan como datos simples para que puedan viajar junto a la instruccion
    en futuros registros de pipeline sin depender de variables globales.
    """

    reg_write: bool = False
    mem_read: bool = False
    mem_write: bool = False
    alu_src: str = "reg"  # "reg" o "imm"
    result_src: str = "alu"  # "alu", "memory", "pc_plus_4", "none"
    pc_src: str = "pc_plus_4"  # "pc_plus_4", "branch"
    branch: bool = False
    branch_condition: str | None = None  # "beq", "bne" o None
    alu_control: str = "ADD"

    def dump(self) -> dict[str, bool | str | None]:
        """Entrega una copia serializable para UI, pruebas o snapshots."""
        return asdict(self)
