import os

# Set environment variables for local development
os.environ["INPUT_DIR"] = os.path.join(os.getcwd(), "input")
os.environ["OUTPUT_DIR"] = os.path.join(os.getcwd(), "output")

# Asegúrate de que los directorios existan
os.makedirs(os.environ["INPUT_DIR"], exist_ok=True)
os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)

# Ahora importa el Refiner después de configurar las variables de entorno
from refiner.refine import Refiner

# Ejecutar el refinador
refiner = Refiner()
output = refiner.transform()

# Imprimir resultados
print(f"Refinement URL: {output.refinement_url}")
print(f"Schema: {output.schema}")