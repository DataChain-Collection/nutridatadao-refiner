import os

# Set environment variables for local development
os.environ["INPUT_DIR"] = os.path.join(os.getcwd(), "input")
os.environ["OUTPUT_DIR"] = os.path.join(os.getcwd(), "output")

# Make sure the directories exist
os.makedirs(os.environ["INPUT_DIR"], exist_ok=True)
os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)

# Now import the Refiner after setting the environment variables
from refiner.refine import Refiner

# Run the refiner
refiner = Refiner()
output = refiner.transform()

# Print results
print(f"Refinement URL: {output.refinement_url}")
print(f"Schema name: {output.schema.name}")
print(f"Schema version: {output.schema.version}")
print(f"Tables: {[table.name for table in output.schema.tables]}")
print(f"Relationships: {[rel.name for rel in output.schema.relationships]}")