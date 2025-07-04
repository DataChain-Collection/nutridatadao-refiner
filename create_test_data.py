import os
import json

# Crear directorio input si no existe
input_dir = os.path.join(os.getcwd(), "input")
os.makedirs(input_dir, exist_ok=True)

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

# Crear un ejemplo de MedicationStatement
medication_example = {
    "resourceType": "MedicationStatement",
    "id": "med-1",
    "subject": {
        "reference": "Patient/example-patient-1"
    },
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

# Guardar los archivos en el directorio input
with open(os.path.join(input_dir, "patient.json"), "w") as f:
    json.dump(fhir_example, f, indent=2)

print(f"Archivo de ejemplo creado en {os.path.join(input_dir, 'patient.json')}")