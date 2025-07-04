from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# SQLAlchemy models for database
Base = declarative_base()

class MedicationDB(Base):
    __tablename__ = "medication"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey('patient.id'), nullable=False)
    resource_type = Column(String, default="MedicationKnowledge", nullable=False)
    code = Column(String, nullable=False)
    display = Column(String, nullable=False)
    system = Column(String, nullable=False)
    text = Column(String, nullable=False)

    # Relationship with patient
    patient = relationship("PatientDB", back_populates="medications")

class PatientDB(Base):
    __tablename__ = "patient"

    id = Column(String, primary_key=True)
    resource_type = Column(String, default="Patient", nullable=False)
    family_name = Column(String, nullable=False)
    given_names = Column(JSON, nullable=False)  # Stored as JSON array
    contact_info = Column(JSON, nullable=True)  # Stored as JSON array

    # Relationship with medications - one-to-many
    medications = relationship("MedicationDB", back_populates="patient")

# Pydantic models for input validation
class HumanName(BaseModel):
    use: Optional[str] = None
    family: str
    given: List[str]

class ContactPoint(BaseModel):
    system: str
    value: str

class Patient(BaseModel):
    resourceType: str = "Patient"
    id: str
    name: List[HumanName]
    telecom: Optional[List[ContactPoint]] = None

class Coding(BaseModel):
    system: str
    code: str
    display: str

class CodeableConcept(BaseModel):
    coding: List[Coding]
    text: str

class MedicationKnowledge(BaseModel):
    resourceType: str = "MedicationKnowledge"
    id: str
    code: CodeableConcept
    patientId: Optional[str] = None  # Added to link medication to patient