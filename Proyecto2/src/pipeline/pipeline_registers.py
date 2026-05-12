"""Futuro modulo para registros entre etapas de pipeline.

Cuando se implemente pipeline, aqui deberian vivir estructuras simples
`dataclass` para IF/ID, ID/EX, EX/MEM y MEM/WB. Es importante que esas
estructuras puedan transportar Instruction y ControlSignals juntas.
"""
