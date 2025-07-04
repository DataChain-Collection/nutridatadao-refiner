import os
import json
import logging
from typing import Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from refiner.models.fihr import Base, PatientDB, MedicationDB
from refiner.models.fihr import Patient, MedicationKnowledge, HumanName, ContactPoint, CodeableConcept, Coding
from refiner.transformer.base_transformer import DataTransformer

logger = logging.getLogger(__name__)

class FHIRTransformer(DataTransformer):
    """
    Transformer for FHIR resources (Patient, MedicationKnowledge).
    """
    
    def _initialize_database(self) -> None:
        """
        Initialize or recreate the database and its tables.
        Override to use FHIR models.
        """
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logging.info(f"Deleted existing database at {self.db_path}")
        
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)  # Usa Base de fihr.py
        self.Session = sessionmaker(bind=self.engine)
        
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
                # Convertir a modelo Pydantic para validación
                patient = Patient(**data)
                
                # Convertir a modelo SQLAlchemy
                patient_db = PatientDB(
                    id=patient.id,
                    resource_type=patient.resourceType,
                    family_name=patient.name[0].family if patient.name else "",
                    given_names=[name.model_dump() for name in patient.name],
                    contact_info=[cp.model_dump() for cp in patient.telecom] if patient.telecom else []
                )
                models.append(patient_db)
                logger.info(f"Transformed Patient with ID: {patient.id}")
            except Exception as e:
                logger.error(f"Error transforming Patient: {e}")
                raise

        elif resource_type == "MedicationStatement":
            try:
                # Convertir MedicationStatement a formato compatible con MedicationKnowledge
                med_concept = data.get("medicationCodeableConcept", {})
                coding = med_concept.get("coding", [{}])[0] if med_concept.get("coding") else {}
                
                # Crear un CodeableConcept con Coding
                codeable_concept = CodeableConcept(
                    coding=[
                        Coding(
                            system=coding.get("system", ""),
                            code=coding.get("code", ""),
                            display=coding.get("display", "")
                        )
                    ],
                    text=med_concept.get("text", "")
                )
                
                # Extraer patient_id del subject.reference
                patient_ref = data.get("subject", {}).get("reference", "")
                patient_id = patient_ref.split("/")[-1] if patient_ref else "unknown"
                
                # Crear MedicationKnowledge
                medication = MedicationKnowledge(
                    resourceType="MedicationKnowledge",
                    id=data.get("id", ""),
                    code=codeable_concept,
                    patientId=patient_id
                )
                
                # Convertir a modelo SQLAlchemy
                medication_db = MedicationDB(
                    id=medication.id,
                    patient_id=medication.patientId,
                    resource_type=medication.resourceType,
                    code=medication.code.coding[0].code,
                    display=medication.code.coding[0].display,
                    system=medication.code.coding[0].system,
                    text=medication.code.text
                )
                models.append(medication_db)
                logger.info(f"Transformed MedicationStatement with ID: {medication.id}")
            except Exception as e:
                logger.error(f"Error transforming MedicationStatement: {e}")
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