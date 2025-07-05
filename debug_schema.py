import os
import logging
from refiner.transformer.fhir_transformer import FHIRTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create a temporary database path
db_path = "temp_db.sqlite"

# Create a transformer
transformer = FHIRTransformer(db_path)

# Get the schema
schema_data = transformer.get_schema()

# Print the type and content of schema_data
print(f"Type of schema_data: {type(schema_data)}")
print(f"Content of schema_data: {schema_data}")

# Try to access the 'tables' key
try:
    tables = schema_data["tables"]
    print(f"Tables: {tables}")
except Exception as e:
    print(f"Error accessing 'tables': {e}")

# Clean up
if os.path.exists(db_path):
    os.remove(db_path)
