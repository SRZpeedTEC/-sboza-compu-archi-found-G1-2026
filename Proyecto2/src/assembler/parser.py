class Parser:
    def parse_text(self, code: str):
        instructions = []
        labels = {}

        lines = code.splitlines()

        for line in lines:
            line = line.split("#")[0].strip()  # Remover comentarios y espacios en blanco

            if not line:
                continue  # Saltar espacios en blanco

            if ":" in line:
                
                label_part, rest = line.split(":", 1)
                label_name = label_part.strip()


                # La etiqueta apunta a la posición actual del programa
                labels[label_name] = len(instructions) * 4

                # Puede existir una instrucción después de la etiqueta
                line = rest.strip()

                if not line:
                    continue
            
            line = " ".join(line.replace(",", " ").split())  # Normalize whitespace
            line = line.lower()  # Convertir a minúsculas para consistencia

            instructions.append(line)

        return instructions, labels
    
