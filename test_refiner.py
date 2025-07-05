import os
import json
import shutil
import pytest
from refiner.refine import Refiner
from refiner.config import settings

@pytest.fixture
def setup_test_environment():
    """Prepare the test environment with sample data."""
    # Create test directories
    os.makedirs("test_input", exist_ok=True)
    os.makedirs("test_output", exist_ok=True)

    # Create a sample FHIR file
    fhir_example = {
        "resourceType": "Patient",
        "id": "example-patient-1",
        "name": [
            {
                "use": "official",
                "family": "Smith",
                "given": ["John"]
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "555-1234"
            }
        ]
    }
    
    with open("test_input/patient.json", "w") as f:
        json.dump(fhir_example, f)

    # Save original settings
    original_input = settings.INPUT_DIR
    original_output = settings.OUTPUT_DIR

    # Modify configuration for testing
    settings.INPUT_DIR = "test_input"
    settings.OUTPUT_DIR = "test_output"
    
    yield

    # Restore original settings
    settings.INPUT_DIR = original_input
    settings.OUTPUT_DIR = original_output

    # Clean up test directories
    shutil.rmtree("test_input", ignore_errors=True)
    shutil.rmtree("test_output", ignore_errors=True)

def test_refiner_transform(setup_test_environment):
    """Test the complete transformation flow."""
    # Run the refiner
    refiner = Refiner()
    output = refiner.transform()

    # Verify that the expected files were generated
    assert os.path.exists(os.path.join("test_output", "schema.json"))
    assert os.path.exists(os.path.join("test_output", "db.libsql"))
    assert os.path.exists(os.path.join("test_output", "db.libsql.pgp"))
    assert os.path.exists(os.path.join("test_output", "output.json"))

    # Verify that the output has the refinement URL
    assert output.refinement_url is not None
    assert output.refinement_url.startswith(settings.IPFS_GATEWAY_URL)

    # Verify that the schema was generated correctly
    assert output.schema is not None
    assert output.schema.name == settings.SCHEMA_NAME
    assert output.schema.version == settings.SCHEMA_VERSION
    
    print(f"Refinement URL: {output.refinement_url}")
    print(f"Schema: {output.schema}")

    # Optional: Check the contents of the output.json file
    with open(os.path.join("test_output", "output.json"), "r") as f:
        output_json = json.load(f)
        assert "refinement_url" in output_json
        assert "schema" in output_json