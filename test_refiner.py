import os
import json
import shutil
import pytest
from refiner.refine import Refiner
from refiner.config import settings

@pytest.fixture
def setup_test_environment():
    """Prepara el entorno de prueba con datos de ejemplo."""
    # Crear directorios de prueba
    os.makedirs("test_input", exist_ok=True)
    os.makedirs("test_output", exist_ok=True)
    
    # Crear un archivo FHIR de ejemplo
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
    
    # Guardar configuración original
    original_input = settings.INPUT_DIR
    original_output = settings.OUTPUT_DIR
    
    # Modificar configuración para pruebas
    settings.INPUT_DIR = "test_input"
    settings.OUTPUT_DIR = "test_output"
    
    yield
    
    # Restaurar configuración original
    settings.INPUT_DIR = original_input
    settings.OUTPUT_DIR = original_output
    
    # Limpiar directorios de prueba
    shutil.rmtree("test_input", ignore_errors=True)
    shutil.rmtree("test_output", ignore_errors=True)

def test_refiner_transform(setup_test_environment):
    """Prueba el flujo completo de transformación."""
    # Ejecutar el refinador
    refiner = Refiner()
    output = refiner.transform()
    
    # Verificar que se generaron los archivos esperados
    assert os.path.exists(os.path.join("test_output", "schema.json"))
    assert os.path.exists(os.path.join("test_output", "db.libsql"))
    assert os.path.exists(os.path.join("test_output", "db.libsql.pgp"))
    assert os.path.exists(os.path.join("test_output", "output.json"))
    
    # Verificar que el output tiene la URL de refinamiento
    assert output.refinement_url is not None
    assert output.refinement_url.startswith(settings.IPFS_GATEWAY_URL)
    
    # Verificar que el schema se generó correctamente
    assert output.schema is not None
    assert output.schema.name == settings.SCHEMA_NAME
    assert output.schema.version == settings.SCHEMA_VERSION
    
    print(f"Refinement URL: {output.refinement_url}")
    print(f"Schema: {output.schema}")
    
    # Opcional: verificar el contenido del archivo output.json
    with open(os.path.join("test_output", "output.json"), "r") as f:
        output_json = json.load(f)
        assert "refinement_url" in output_json
        assert "schema" in output_json