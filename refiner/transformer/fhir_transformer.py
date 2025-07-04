from typing import Dict, Any, List, Optional
import logging

from refiner.models.fihr import (
    PatientDB, MedicationDB,
    Patient, MedicationKnowledge,
    HumanName, ContactPoint, CodeableConcept, Coding
)
from refiner.transformer.base_transformer import DataTransformer
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class FHIRTransformer(DataTransformer):
    """
    Transformer for FHIR resources (Patient, MedicationKnowledge, MedicationStatement).
    """

    def transform(self, data: Dict[str, Any]) -> List:
        """
        Transform a FHIR resource dict into SQLAlchemy model instances.

        Args:
            data: Raw FHIR resource data

        Returns:
            List of SQLAlchemy model instances
        """
        resource_type = data.get("resourceType")
        models = []

        if resource_type == "Patient":
            try:
                patient = Patient(**data)

                # Extract names correctly
                names_data = []
                for name in patient.name:
                    name_data = {
                        "use": name.use,
                        "family": name.family,
                        "given": name.given
                    }
                    names_data.append(name_data)

                # Extract telecom contact points
                telecom_data = []
                if patient.telecom:
                    for cp in patient.telecom:
                        telecom_data.append({
                            "system": cp.system,
                            "value": cp.value
                        })

                patient_db = PatientDB(
                    id=patient.id,
                    resource_type=patient.resourceType,
                    family_name=patient.name[0].family if patient.name else "",
                    given_names=names_data,
                    contact_info=telecom_data if telecom_data else None
                )
                models.append(patient_db)
                logger.info(f"Transformed Patient with ID: {patient.id}")
            except ValidationError as ve:
                logger.error(f"Validation error transforming Patient: {ve}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error transforming Patient: {e}")
                raise

        elif resource_type in ("MedicationStatement", "MedicationKnowledge"):
            try:
                # Common medication processing
                if resource_type == "MedicationStatement":
                    # Extract medication coding from MedicationStatement
                    med_concept = data.get("medicationCodeableConcept", {})
                    codings = med_concept.get("coding", [{}])
                    first_coding = codings[0] if codings else {}

                    # Build CodeableConcept
                    codeable_concept = CodeableConcept(
                        coding=[Coding(
                            system=first_coding.get("system", ""),
                            code=first_coding.get("code", ""),
                            display=first_coding.get("display", "")
                        )],
                        text=med_concept.get("text", "")
                    )

                    # Extract patient reference
                    patient_ref = data.get("subject", {}).get("reference", "")
                    patient_id = patient_ref.split("/")[-1] if patient_ref else None

                    medication = MedicationKnowledge(
                        resourceType="MedicationKnowledge",
                        id=data.get("id"),
                        code=codeable_concept,
                        patientId=patient_id
                    )
                else:  # MedicationKnowledge
                    # Preprocess to ensure required fields
                    code_data = data.get("code", {})
                    if "coding" not in code_data or not code_data["coding"]:
                        code_data["coding"] = [{}]
                    if "text" not in code_data:
                        code_data["text"] = ""

                    # Extract patient ID if present
                    patient_id = data.get("patientId")
                    if patient_id and isinstance(patient_id, str) and "/" in patient_id:
                        data["patientId"] = patient_id.split("/")[-1]

                    medication = MedicationKnowledge(**data)

                # Validate we have at least one coding
                if not medication.code.coding:
                    medication.code.coding.append(Coding(system="", code="", display=""))

                first_coding = medication.code.coding[0]

                medication_db = MedicationDB(
                    id=medication.id,
                    patient_id=medication.patientId or "unknown",
                    resource_type=medication.resourceType,
                    code=first_coding.code,
                    display=first_coding.display,
                    system=first_coding.system,
                    text=medication.code.text
                )
                models.append(medication_db)
                logger.info(f"Transformed {resource_type} with ID: {medication.id}")
            except ValidationError as ve:
                logger.error(f"Validation error transforming {resource_type}: {ve}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error transforming {resource_type}: {e}")
                raise
        else:
            logger.warning(f"Unsupported resource type: {resource_type}")

        return models

    def get_schema(self) -> str:
        """
        Generate database schema definition.
        
        Returns:
            String containing the schema definition
        """
        schema_dict = {
            "tables": [
                {
                    "name": "patient",
                    "columns": [
                        {"name": "id", "type": "TEXT", "primary_key": True},
                        {"name": "resource_type", "type": "TEXT", "nullable": False},
                        {"name": "family_name", "type": "TEXT", "nullable": False},
                        {"name": "given_names", "type": "JSON", "nullable": False},
                        {"name": "contact_info", "type": "JSON", "nullable": True}
                    ]
                },
                {
                    "name": "medication",
                    "columns": [
                        {"name": "id", "type": "TEXT", "primary_key": True},
                        {"name": "patient_id", "type": "TEXT", "nullable": False, "foreign_key": "patient.id"},
                        {"name": "resource_type", "type": "TEXT", "nullable": False},
                        {"name": "code", "type": "TEXT", "nullable": False},
                        {"name": "display", "type": "TEXT", "nullable": False},
                        {"name": "system", "type": "TEXT", "nullable": False},
                        {"name": "text", "type": "TEXT", "nullable": False}
                    ]
                }
            ],
            "relationships": [
                {
                    "name": "patient_medications",
                    "type": "one_to_many",
                    "from_table": "patient",
                    "to_table": "medication",
                    "from_column": "id",
                    "to_column": "patient_id"
                }
            ]
        }

        import json
        return json.dumps(schema_dict, indent=2)