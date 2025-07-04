from typing import Dict, Any, List
import logging

from refiner.models.fihr import (
    PatientDB, MedicationDB, 
    Patient, MedicationKnowledge
)
from refiner.transformer.base_transformer import DataTransformer

logger = logging.getLogger(__name__)

class FHIRTransformer(DataTransformer):
    """
    Transformer for FHIR resources (Patient, MedicationKnowledge).
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
            patient = Patient(**data)
            patient_db = PatientDB(
                id=patient.id,
                resource_type=patient.resourceType,
                family_name=patient.name[0].family if patient.name else "",
                given_names=[name.model_dump() for name in patient.name] if patient.name else [],
                contact_info=[cp.model_dump() for cp in (patient.telecom or [])] if patient.telecom else []
            )
            models.append(patient_db)

        elif resource_type == "MedicationKnowledge":
            medication = MedicationKnowledge(**data)
            primary_coding = medication.code.coding[0] if medication.code.coding else None
            if not primary_coding:
                raise ValueError("Medication must have at least one coding")
            medication_db = MedicationDB(
                id=medication.id,
                patient_id=medication.patientId or "unknown",
                resource_type=medication.resourceType,
                code=primary_coding.code,
                display=primary_coding.display,
                system=primary_coding.system,
                text=medication.code.text
            )
            models.append(medication_db)
        else:
            logger.warning(f"Unsupported resource type: {resource_type}")

        return models

    def process(self, data: Dict[str, Any]) -> None:
        """
        Transform and save FHIR resource(s) to the database.
        """
        models = self.transform(data)
        session = self.Session()
        try:
            for model in models:
                session.add(model)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to database: {e}")
        finally:
            session.close()

    def get_schema(self) -> Dict[str, Any]:
        """
        Generate database schema definition.
        
        Returns:
            Dict containing the schema definition
        """
        return {
            "tables": [
                {
                    "name": "patients",
                    "columns": [
                        {"name": "id", "type": "TEXT", "primary_key": True},
                        {"name": "resource_type", "type": "TEXT", "nullable": False},
                        {"name": "family_name", "type": "TEXT", "nullable": False},
                        {"name": "given_names", "type": "JSON", "nullable": False},
                        {"name": "contact_info", "type": "JSON", "nullable": True}
                    ]
                },
                {
                    "name": "medications",
                    "columns": [
                        {"name": "id", "type": "TEXT", "primary_key": True},
                        {"name": "patient_id", "type": "TEXT", "nullable": False, "foreign_key": "patients.id"},
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
                    "from_table": "patients",
                    "to_table": "medications",
                    "from_column": "id",
                    "to_column": "patient_id"
                }
            ]
        }