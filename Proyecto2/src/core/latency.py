"""Latencias de los componentes del datapath RISC-V (en picosegundos).

Tabla de referencia del proyecto:
  PC (lectura)                      30 ps
  Instruction Memory (IM)          200 ps
  Register File (lectura)          150 ps
  Register File (escritura)        100 ps
  Immediate Generator / Sign Extend  20 ps
  ALU                              200 ps
  Data Memory (lectura)            250 ps
  Data Memory (escritura)          250 ps
  MUX                               25 ps
  Control Unit / Decode             30 ps
  Branch Comparator                 50 ps
  Sumador PC+4 / Branch Target      30 ps
"""

# ---------------------------------------------------------------------------
# Latencias individuales de componentes (ps)
# ---------------------------------------------------------------------------

PC_READ             = 30
INSTRUCTION_MEMORY  = 200
REGISTER_FILE_READ  = 150
REGISTER_FILE_WRITE = 100
IMMEDIATE_GEN       = 20
ALU                 = 200
DATA_MEMORY_READ    = 250
DATA_MEMORY_WRITE   = 250
MUX                 = 25
CONTROL_UNIT        = 30
BRANCH_COMPARATOR   = 50
PC_ADDER            = 30

# ---------------------------------------------------------------------------
# Caminos criticos usados para fijar el periodo del procesador UNICICLO
#
# Convencion: los MUX de seleccion (ALUSrcA, ALUSrcB, ResultSrc, PCsrc)
# se incluyen en el camino porque cada etapa espera a todos sus inputs.
# El control unit y el ImmGen corren en paralelo con el banco de registros
# (ambos arrancan tras la salida de IM), por lo que no se suman al camino
# critico cuando son mas rapidos que RegFile_read (150 ps > 20 ps, 30 ps).
# ---------------------------------------------------------------------------

# R-type (add, sub, and, or, xor):
#   PC -> IM -> RegFile_read -> ALUSrcB_MUX -> ALU -> ResultSrc_MUX -> RegFile_write
_PATH_RTYPE = (
    PC_READ
    + INSTRUCTION_MEMORY
    + REGISTER_FILE_READ
    + MUX
    + ALU
    + MUX
    + REGISTER_FILE_WRITE
)  # 730 ps

# I-type aritmetico (addi): RegFile_read (150) domina sobre ImmGen (20).
_PATH_ITYPE = _PATH_RTYPE  # 730 ps

# lw:
#   PC -> IM -> RegFile_read -> ALUSrcB_MUX -> ALU -> DataMem_read
#      -> ResultSrc_MUX -> RegFile_write
_PATH_LW = (
    PC_READ
    + INSTRUCTION_MEMORY
    + REGISTER_FILE_READ
    + MUX
    + ALU
    + DATA_MEMORY_READ
    + MUX
    + REGISTER_FILE_WRITE
)  # 980 ps

# sw:
#   PC -> IM -> RegFile_read -> ALUSrcB_MUX -> ALU -> DataMem_write
_PATH_SW = (
    PC_READ
    + INSTRUCTION_MEMORY
    + REGISTER_FILE_READ
    + MUX
    + ALU
    + DATA_MEMORY_WRITE
)  # 855 ps

# beq / bne:
#   Camino condicion: PC -> IM -> RegFile_read -> BranchComp -> PCsrc_MUX
#   Camino destino:   PC -> IM -> ImmGen -> PC_Adder -> PCsrc_MUX
_PATH_BRANCH_COND = (
    PC_READ
    + INSTRUCTION_MEMORY
    + REGISTER_FILE_READ
    + BRANCH_COMPARATOR
    + MUX
)  # 455 ps
_PATH_BRANCH_TARGET = (
    PC_READ
    + INSTRUCTION_MEMORY
    + IMMEDIATE_GEN
    + PC_ADDER
    + MUX
)  # 305 ps
_PATH_BRANCH = max(_PATH_BRANCH_COND, _PATH_BRANCH_TARGET)  # 455 ps

# Periodo del reloj uniciclo = camino critico mas largo (dominado por lw).
CLOCK_PERIOD_SINGLE_CYCLE: int = max(
    _PATH_RTYPE,
    _PATH_ITYPE,
    _PATH_LW,
    _PATH_SW,
    _PATH_BRANCH,
)  # 980 ps

# ---------------------------------------------------------------------------
# Latencias de etapa para MULTICICLO y PIPELINE
#
# En ambas arquitecturas el periodo del reloj lo fija la etapa mas lenta.
#
# Etapa IF:  AdrSrc_MUX + IM
# Etapa ID:  RegFile_read  (domina sobre ImmGen y ControlUnit)
# Etapa EX:  ALUSrcA_MUX + ALU  (ALUSrcB_MUX corre en paralelo)
# Etapa MEM: AdrSrc_MUX + DataMem_read   <- etapa critica
# Etapa WB:  ResultSrc_MUX + RegFile_write
# ---------------------------------------------------------------------------

STAGE_IF_PS  = MUX + INSTRUCTION_MEMORY    # 225 ps
STAGE_ID_PS  = REGISTER_FILE_READ          # 150 ps
STAGE_EX_PS  = MUX + ALU                   # 225 ps
STAGE_MEM_PS = MUX + DATA_MEMORY_READ      # 275 ps
STAGE_WB_PS  = MUX + REGISTER_FILE_WRITE   # 125 ps

CLOCK_PERIOD_MULTICYCLE: int = max(
    STAGE_IF_PS,
    STAGE_ID_PS,
    STAGE_EX_PS,
    STAGE_MEM_PS,
    STAGE_WB_PS,
)  # 275 ps

# Pipeline usa el mismo periodo porque comparte la etapa critica de MEM.
CLOCK_PERIOD_PIPELINE: int = CLOCK_PERIOD_MULTICYCLE  # 275 ps

# ---------------------------------------------------------------------------
# Tiempo acumulado en Metrics.time_ps
# ---------------------------------------------------------------------------
#
# Todos los procesadores suman tiempo por ciclo de reloj ejecutado:
#   Uniciclo:   1 ciclo por instruccion, periodo 980 ps.
#   Multiciclo: 1 ciclo por etapa, periodo 275 ps.
#   Pipeline:   1 ciclo por avance del pipeline, periodo 275 ps.
# Las diferencias entre instrucciones se reflejan en la cantidad de ciclos, no
# en una latencia especial por tipo de instruccion.
PIPELINE_LATENCY_PS: int = CLOCK_PERIOD_PIPELINE

# ---------------------------------------------------------------------------
# Utilidad: formato legible
# ---------------------------------------------------------------------------

def fmt_time(ps: int | float) -> str:
    """Convierte picosegundos a cadena legible.

    < 1000 ps  ->  "N ps"
    >= 1000 ps ->  "X.NNN ns"  (sin ceros finales)
    """
    if ps == 0:
        return "0 ps"
    if ps < 1_000:
        return f"{int(ps)} ps"
    ns = ps / 1_000
    if ns == int(ns):
        return f"{int(ns)} ns"
    # Eliminar ceros finales: 12.100 -> 12.1, 3.025 -> 3.025
    return f"{ns:.3f}".rstrip("0").rstrip(".") + " ns"
