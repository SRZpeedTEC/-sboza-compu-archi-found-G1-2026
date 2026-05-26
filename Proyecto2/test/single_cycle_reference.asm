# Programa de referencia para validar SingleCycleEngine con prints.
# Evita directivas como .data porque el parser actual las trata como instrucciones.

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
