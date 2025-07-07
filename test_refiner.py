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

    # Create a sample FHIR patient file
    patient_example = {
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

    # Create a sample FHIR medication statement
    medication_example = {
        "resourceType": "MedicationStatement",
        "id": "med-1",
        "subject": {
            "reference": "Patient/example-patient-1"
        },
        "status": "active",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "1049502",
                    "display": "Acetaminophen 325 MG Oral Tablet"
                }
            ],
            "text": "Acetaminophen 325 MG Oral Tablet"
        }
    }

    # Create a FHIR bundle with both resources
    bundle_example = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": patient_example},
            {"resource": medication_example}
        ]
    }

    # Write individual files
    with open("test_input/patient.json", "w") as f:
        json.dump(patient_example, f)

    with open("test_input/medication.json", "w") as f:
        json.dump(medication_example, f)

    # Write bundle file
    with open("test_input/bundle.json", "w") as f:
        json.dump(bundle_example, f)

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

    # Verify that the output.json file exists in the correct directory
    output_path = os.path.join("output", "output.json")
    assert os.path.exists(output_path), f"Output file not found at {output_path}"

    # Verify that the output has the refinement URL
    assert output.refinement_url is not None
    assert output.refinement_url.startswith(settings.IPFS_GATEWAY_URL)

    # Verify that the schema was generated correctly
    assert output.schema_content is not None
    assert output.schema_content.name == settings.SCHEMA_NAME
    assert output.schema_content.version == settings.SCHEMA_VERSION

    print(f"Refinement URL: {output.refinement_url}")
    print(f"Schema: {output.schema_content}")

    # Check the contents of the output.json file
    with open(output_path, "r") as f:
        output_json = json.load(f)
        assert "refinement_url" in output_json
        assert "schema" in output_json

def test_refiner_database_content(setup_test_environment):
    """Test that the database contains the expected data."""
    # Ejecutar el refinador
    refiner = Refiner()
    output = refiner.transform()

    # Importar SQLite para verificar contenido
    import sqlite3

    # Conectar a la base de datos
    db_path = os.path.join("test_output", "db.libsql")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar pacientes
    cursor.execute("SELECT id, family_name FROM patient")
    patients = cursor.fetchall()

    # Debería haber 1 paciente (los archivos individuales y el bundle comparten el mismo ID)
    assert len(patients) == 1, f"Expected 1 patient, found {len(patients)}"
    assert patients[0][0] == "example-patient-1"
    assert patients[0][1] == "Smith"

    # Verificar medicamentos
    cursor.execute("SELECT id, patient_id, code, display FROM medication")
    medications = cursor.fetchall()

    # Debería haber 1 medicamento (mismo ID en ambos archivos)
    assert len(medications) == 1, f"Expected 1 medication, found {len(medications)}"
    assert medications[0][0] == "med-1"
    assert medications[0][1] == "example-patient-1"
    assert medications[0][2] == "1049502"
    assert medications[0][3] == "Acetaminophen 325 MG Oral Tablet"

    # Cerrar conexión
    conn.close()

def test_refiner_bundle_processing(setup_test_environment):
    """Test that the refiner can process a FHIR bundle."""
    # Run the refiner
    refiner = Refiner()
    output = refiner.transform()

    # Import SQLite to check database content
    import sqlite3

    # Connect to the database
    db_path = os.path.join("test_output", "db.libsql")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check that both resources from the bundle were processed
    cursor.execute("SELECT COUNT(*) FROM patient")
    patient_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM medication")
    medication_count = cursor.fetchone()[0]

    # We expect at least one of each since we have individual files and a bundle
    assert patient_count >= 1, f"Expected at least 1 patient, found {patient_count}"
    assert medication_count >= 1, f"Expected at least 1 medication, found {medication_count}"

    # Close the connection
    conn.close()

def test_refiner_schema_structure(setup_test_environment):
    """Test that the generated schema has the expected structure."""
    # Run the refiner
    refiner = Refiner()
    output = refiner.transform()

    # Load the schema.json file
    with open(os.path.join("test_output", "schema.json"), "r") as f:
        schema = json.load(f)

    # Check that the schema has the expected tables
    tables = [table["name"] for table in schema["tables"]]
    assert "patient" in tables, "Schema should include patient table"
    assert "medication" in tables, "Schema should include medication table"

    # Check that the schema has the expected relationships
    relationships = schema.get("relationships", [])
    relationship_names = [rel["name"] for rel in relationships]
    assert "patient_medications" in relationship_names, "Schema should include patient_medications relationship"

    # Find the medication table and check its columns
    medication_table = next((table for table in schema["tables"] if table["name"] == "medication"), None)
    assert medication_table is not None

    # Check that the medication table has the expected columns
    column_names = [col["name"] for col in medication_table["columns"]]
    expected_columns = ["id", "patient_id", "resource_type", "code", "display", "system", "text"]
    for col in expected_columns:
        assert col in column_names, f"Medication table should have {col} column"