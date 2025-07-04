from refiner.refine import Refiner

# Ejecutar el refinador
refiner = Refiner()
output = refiner.transform()

# Imprimir resultados
print(f"Refinement URL: {output.refinement_url}")
print(f"Schema: {output.schema}")