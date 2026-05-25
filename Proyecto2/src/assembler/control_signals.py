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

    # Senales especificas del datapath multiciclo. En uniciclo/pipeline quedan
    # en None para no mezclar ciclos de control que esas arquitecturas no usan.
    pc_write: bool | None = None
    adr_src: str | None = None
    ir_write: bool | None = None
    alu_src_a: str | None = None
    alu_src_b: str | None = None
        

    def get_snapshot(self) -> dict[str, bool | str | None]:
        """Entrega una copia serializable para UI, pruebas o snapshots."""
        return asdict(self)
