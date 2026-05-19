# Programa de referencia para validar MultiCycleEngine.
# Cubre todos los tipos de instruccion: R-type, ADDI, SW, LW, BEQ (tomado).
# Resultados esperados al finalizar:
#   x1=4, x2=7, x3=11, x4=7, x5=3, x6=7, x7=12
#   x8=11, x9=0 (skipped), x10=12
#   memoria[0]=11
#   ciclos=44, instrucciones=11, CPI=4.0

addi x1, x0, 4
addi x2, x0, 7
add x3, x1, x2
sub x4, x3, x1
and x5, x3, x2
or x6, x1, x2
xor x7, x3, x2
sw x3, 0(x0)
lw x8, 0(x0)
beq x8, x3, done
addi x9, x0, 999
done:
addi x10, x8, 1
