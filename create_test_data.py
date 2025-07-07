import os
import json
import random
from datetime import datetime, timedelta

# Create input directory if it does not exist
input_dir = os.path.join(os.getcwd(), "input")
os.makedirs(input_dir, exist_ok=True)

# Create a sample FHIR Patient
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
        },
        {
            "system": "email",
            "value": "john.smith@example.com"
        }
    ],
    "gender": "male",
    "birthDate": "1970-01-01",
    "address": [
        {
            "use": "home",
            "line": ["123 Main St"],
            "city": "Anytown",
            "state": "CA",
            "postalCode": "12345",
            "country": "USA"
        }
    ]
}

# Create a second patient
patient_example2 = {
    "resourceType": "Patient",
    "id": "example-patient-2",
    "name": [
        {
            "use": "official",
            "family": "Johnson",
            "given": ["Sarah"]
        }
    ],
    "telecom": [
        {
            "system": "phone",
            "value": "555-5678"
        },
        {
            "system": "email",
            "value": "sarah.johnson@example.com"
        }
    ],
    "gender": "female",
    "birthDate": "1985-05-15"
}

# Common medications with RxNorm codes
medications = [
    {
        "code": "1049502",
        "display": "Acetaminophen 325 MG Oral Tablet",
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm"
    },
    {
        "code": "197319",
        "display": "Amoxicillin 500 MG Oral Capsule",
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm"
    },
    {
        "code": "197318",
        "display": "Ibuprofen 200 MG Oral Tablet",
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm"
    },
    {
        "code": "310965",
        "display": "Lisinopril 10 MG Oral Tablet",
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm"
    },
    {
        "code": "314076",
        "display": "Simvastatin 20 MG Oral Tablet",
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm"
    }
]

# Create multiple MedicationStatement examples for the first patient
medication_examples = []
for i in range(3):
    med = random.choice(medications)
    medication_examples.append({
        "resourceType": "MedicationStatement",
        "id": f"med-{i+1}",
        "subject": {
            "reference": "Patient/example-patient-1"
        },
        "status": "active",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": med["system"],
                    "code": med["code"],
                    "display": med["display"]
                }
            ],
            "text": med["display"]
        },
        "effectiveDateTime": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dateAsserted": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dosage": [
            {
                "text": f"Take 1 tablet by mouth {random.choice(['daily', 'twice daily', 'as needed'])}",
                "timing": {
                    "repeat": {
                        "frequency": random.choice([1, 2]),
                        "period": 1,
                        "periodUnit": "d"
                    }
                },
                "route": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "26643006",
                            "display": "Oral route"
                        }
                    ]
                }
            }
        ]
    })

# Create a medication for the second patient
med = random.choice(medications)
medication_examples.append({
    "resourceType": "MedicationStatement",
    "id": "med-4",
    "subject": {
        "reference": "Patient/example-patient-2"
    },
    "status": "active",
    "medicationCodeableConcept": {
        "coding": [
            {
                "system": med["system"],
                "code": med["code"],
                "display": med["display"]
            }
        ],
        "text": med["display"]
    }
})

# # Save the patient files to the input directory
# with open(os.path.join(input_dir, "patient1.json"), "w") as f:
#     json.dump(patient_example, f, indent=2)
# 
# with open(os.path.join(input_dir, "patient2.json"), "w") as f:
#     json.dump(patient_example2, f, indent=2)
# 
# # Save each medication to a separate file
# for i, med in enumerate(medication_examples):
#     with open(os.path.join(input_dir, f"medication{i+1}.json"), "w") as f:
#         json.dump(med, f, indent=2)

# Create a bundle with all resources for testing bulk processing
bundle = {
    "resourceType": "Bundle",
    "type": "collection",
    "entry": [
        {"resource": patient_example},
        {"resource": patient_example2}
    ]
}

# Add medications to bundle
for med in medication_examples:
    bundle["entry"].append({"resource": med})

# Save the bundle
with open(os.path.join(input_dir, "bundle.json"), "w") as f:
    json.dump(bundle, f, indent=2)

print(f"Created {len(medication_examples)} medication files in {input_dir}")
print(f"Created {2} patient files in {input_dir}")
print(f"Created bundle with {len(bundle['entry'])} resources in {os.path.join(input_dir, 'bundle.json')}")
print(f"Sample files created in {input_dir}")