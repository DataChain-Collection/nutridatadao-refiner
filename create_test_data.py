import os
import json

# Create input directory if it does not exist
input_dir = os.path.join(os.getcwd(), "input")
os.makedirs(input_dir, exist_ok=True)

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

# Create an example MedicationStatement
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

# Save the files to the input directory
with open(os.path.join(input_dir, "patient.json"), "w") as f:
    json.dump(fhir_example, f, indent=2)

print(f"Sample file created in {os.path.join(input_dir, 'patient.json')}")