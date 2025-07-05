import os
import logging
from typing import Dict, Any, List, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from refiner.models.fihr import Base, PatientDB, MedicationDB
from refiner.models.fihr import Patient, MedicationKnowledge
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

    def transform(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List:
        """
        Transform FHIR resource(s) into SQLAlchemy model instances.
    
        Args:
            data: Raw FHIR resource data (single resource dict or list of resource dicts)
    
        Returns:
            List of SQLAlchemy model instances
        """
        models = []

        # Handle both single resources and lists of resources
        if isinstance(data, list):
            # Process each resource in the list
            for resource in data:
                models.extend(self._transform_resource(resource))
        elif isinstance(data, dict):
            # Process a single resource
            models.extend(self._transform_resource(data))
        else:
            logger.warning(f"Unsupported data type: {type(data)}")

        return models

    def _transform_resource(self, resource: Dict[str, Any]) -> List:
        """
        Transform a single FHIR resource dict into SQLAlchemy model instances.

        Args:
            resource: Raw FHIR resource data

        Returns:
            List of SQLAlchemy model instances
        """
        if not resource or not isinstance(resource, dict):
            logger.warning(f"Invalid resource: {resource}")
            return []

        resource_type = resource.get("resourceType")
        if not resource_type:
            logger.warning(f"Resource missing resourceType: {resource}")
            return []

        models = []

        # Handle Bundle resources by extracting and processing each entry
        if resource_type == "Bundle":
            for entry in resource.get("entry", []):
                if "resource" in entry and isinstance(entry["resource"], dict):
                    entry_models = self._transform_resource(entry["resource"])
                    models.extend(entry_models)
            return models

        if resource_type == "Patient":
            try:
                patient = Patient(**resource)
                patient_db = PatientDB(
                    id=patient.id,
                    resource_type=patient.resourceType,
                    family_name=patient.name[0].family if patient.name else "",
                    given_names=[name.model_dump() for name in patient.name] if patient.name else [],
                    contact_info=[cp.model_dump() for cp in (patient.telecom or [])] if patient.telecom else []
                )
                models.append(patient_db)
                logger.info(f"Transformed Patient with ID: {patient.id}")
            except Exception as e:
                logger.error(f"Error transforming Patient: {e}")
                # Continue processing other resources

        elif resource_type == "MedicationKnowledge":
            try:
                medication = MedicationKnowledge(**resource)
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
                logger.info(f"Transformed MedicationKnowledge with ID: {medication.id}")
            except Exception as e:
                logger.error(f"Error transforming MedicationKnowledge: {e}")
                # Continue processing other resources

        elif resource_type == "MedicationStatement":
            # Handle MedicationStatement resources
            try:
                # Extract medication details
                med_concept = resource.get("medicationCodeableConcept", {})
                coding = med_concept.get("coding", [{}])[0] if med_concept.get("coding") else {}

                # Extract patient reference
                subject_ref = resource.get("subject", {}).get("reference", "")
                patient_id = subject_ref.split("/")[-1] if subject_ref else "unknown"

                # Create medication database model
                medication_db = MedicationDB(
                    id=resource.get("id", ""),
                    patient_id=patient_id,
                    resource_type="MedicationKnowledge",  # Map to our model type
                    code=coding.get("code", ""),
                    display=coding.get("display", ""),
                    system=coding.get("system", ""),
                    text=med_concept.get("text", "")
                )
                models.append(medication_db)
                logger.info(f"Transformed MedicationStatement with ID: {resource.get('id')}")
            except Exception as e:
                logger.error(f"Error transforming MedicationStatement: {e}")
                # Continue processing other resources
        else:
            logger.warning(f"Unsupported resource type: {resource_type}")

        return models

    def get_schema(self) -> Dict[str, Any]:
        """
        Override the base get_schema method to return a dictionary instead of a string.
        
        Returns:
            Dictionary containing the schema definition
        """
        # Define schema as a Python dictionary
        schema_dict = {
            "tables": [
                {
                    "name": "patient",
                    "columns": [
                        {"name": "id", "type": "TEXT", "primary_key": True, "nullable": False},
                        {"name": "resource_type", "type": "TEXT", "nullable": False},
                        {"name": "family_name", "type": "TEXT", "nullable": False},
                        {"name": "given_names", "type": "JSON", "nullable": False},
                        {"name": "contact_info", "type": "JSON", "nullable": True}
                    ]
                },
                {
                    "name": "medication",
                    "columns": [
                        {"name": "id", "type": "TEXT", "primary_key": True, "nullable": False},
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
                    "source_table": "patient",
                    "target_table": "medication",
                    "source_column": "id",
                    "target_column": "patient_id",
                    "type": "one-to-many"
                }
            ]
        }

        return schema_dict

    def process(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """
        Transform and save FHIR resource(s) to the database.
        
        Args:
            data: Raw FHIR resource data (single resource dict or list of resource dicts)
        """
        models = self.transform(data)
        session = self.Session()
        try:
            for model in models:
                session.add(model)
            session.commit()
            logger.info(f"Saved {len(models)} models to database")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to database: {e}")
            raise
        finally:
            session.close()