from src.assembler import parser
from src.core.Decoder import Decoder

# Example usage
code = """
    # This is a comment
    loop:
    ADD R1, R2, R3  # Another comment
    SUB R4, R5, R6
"""

parse = parser.Parser()

instructions, labels = parse.parse_text(code)
print("Instructions:", instructions)
print("Labels:", labels)


decoder = Decoder(labels)

for instr in instructions:
    decoded = decoder.decode(instr)
    print(decoded)