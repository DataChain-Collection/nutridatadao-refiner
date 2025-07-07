import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set environment variables for local development
os.environ["INPUT_DIR"] = os.path.join(os.getcwd(), "input")
os.environ["OUTPUT_DIR"] = os.path.join(os.getcwd(), "output")

# Make sure the directories exist
os.makedirs(os.environ["INPUT_DIR"], exist_ok=True)
os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)

# Create a sample FHIR resource if input directory is empty
if not os.listdir(os.environ["INPUT_DIR"]) or not any(f.endswith('.json') for f in os.listdir(os.environ["INPUT_DIR"])):
    logging.info("No FHIR data found in input directory")

    # Check if create_test_data.py exists
    if os.path.exists("create_test_data.py"):
        logging.info("Generating test FHIR data using create_test_data.py...")
        try:
            import subprocess
            result = subprocess.run(["python", "create_test_data.py"], capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("Successfully generated test FHIR data")
            else:
                logging.error(f"Error generating test data: {result.stderr}")
        except Exception as e:
            logging.error(f"Failed to run create_test_data.py: {e}")
    else:
        logging.warning("create_test_data.py not found.")

        # Create a minimal sample as fallback
        logging.info("Creating minimal sample FHIR resource as fallback")
        sample_data = {
            "resourceType": "Patient",
            "id": "example-patient-1",
            "name": [
                {
                    "family": "Smith",
                    "given": ["John"]
                }
            ],
            "telecom": [
                {
                    "system": "phone",
                    "value": "555-1234",
                    "use": "home"
                }
            ]
        }
        with open(os.path.join(os.environ["INPUT_DIR"], "sample.json"), 'w') as f:
            json.dump(sample_data, f, indent=2)

# Now import the Refiner after setting the environment variables
from refiner.refine import Refiner

try:
    # Run the refiner
    refiner = Refiner()
    output = refiner.transform()

    # Print results
    print(f"Refinement URL: {output.refinement_url}")
    print(f"Schema name: {output.schema_content.name}")
    print(f"Schema version: {output.schema_content.version}")
    print(f"Tables: {[table['name'] for table in output.schema_content.tables]}")
    print(f"Relationships: {[rel['name'] for rel in output.schema_content.relationships]}")
except Exception as e:
    logging.error(f"Error running refiner: {e}", exc_info=True)
