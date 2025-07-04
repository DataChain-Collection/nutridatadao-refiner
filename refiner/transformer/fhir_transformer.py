from typing import Dict, Any, List, Optional
import json
import logging

from refiner.models.fhir import (
    PatientDB, MedicationDB, 
    Patient, MedicationKnowledge
)

logger = logging.getLogger(__name__)

class FHIRTransformer:
    def __init__(self, db_path: str):
        """
        Initialize the transformer with database path.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.patients = {}  # Cache of patient IDs
        
    def process(self, data: Dict[str, Any]) -> None:
        """
        Process a FHIR resource and add it to the database.
        
        Args:
            data: Raw FHIR resource data
        """
        resource_type = data.get("resourceType")
        
        if resource_type == "Patient":
            self._process_patient(data)
        elif resource_type == "MedicationKnowledge":
            self._process_medication(data)
        else:
            logger.warning(f"Unsupported resource type: {resource_type}")
    
    def _process_patient(self, data: Dict[str, Any]) -> None:
        """Process Patient resource"""
        try:
            # Validate with Pydantic model
            patient = Patient(**data)
            
            # Extract primary name
            primary_name = patient.name[0] if patient.name else None
            if not primary_name:
                raise ValueError("Patient must have at least one name")
            
            # Create database model
            patient_db = PatientDB(
                id=patient.id,
                resource_type="Patient",
                family_name=primary_name.family,
                given_names=json.dumps([name for name in primary_name.given]),
                contact_info=json.dumps([{
                    "system": contact.system,
                    "value": contact.value
                } for contact in (patient.telecom or [])])
            )
            
            # Add to database
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(f"sqlite:///{self.db_path}")
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                session.add(patient_db)
                session.commit()
                # Cache patient ID for later use with medications
                self.patients[patient.id] = True
            except Exception as e:
                session.rollback()
                logger.error(f"Error adding patient to database: {e}")
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error processing patient: {e}")
    
    def _process_medication(self, data: Dict[str, Any]) -> None:
        """Process MedicationKnowledge resource"""
        try:
            # Add patient ID if not present
            patient_id = data.get("patientId")
            
            # Validate with Pydantic model
            medication = MedicationKnowledge(**data)
            
            # Extract primary coding
            primary_coding = medication.code.coding[0] if medication.code.coding else None
            if not primary_coding:
                raise ValueError("Medication must have at least one coding")
            
            # Create database model
            medication_db = MedicationDB(
                id=medication.id,
                patient_id=patient_id or "unknown",  # Use provided patient ID or default
                resource_type="MedicationKnowledge",
                code=primary_coding.code,
                display=primary_coding.display,
                system=primary_coding.system,
                text=medication.code.text
            )
            
            # Add to database
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(f"sqlite:///{self.db_path}")
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                session.add(medication_db)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Error adding medication to database: {e}")
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error processing medication: {e}")
    
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