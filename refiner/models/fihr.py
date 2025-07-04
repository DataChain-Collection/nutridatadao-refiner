from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List, Optional

# Base para modelos SQLAlchemy
Base = declarative_base()

# === MODELOS SQLALCHEMY ===

class PatientDB(Base):
    __tablename__ = "patient"  # Asegúrate de que este nombre coincida con el usado en el transformador

    id = Column(String, primary_key=True)
    resource_type = Column(String, default="Patient", nullable=False)
    family_name = Column(String, nullable=False)
    given_names = Column(JSON, nullable=False)  # Almacena una lista de objetos {use, family, given}
    contact_info = Column(JSON, nullable=True)  # Almacena una lista de objetos {system, value}

    # Relación con MedicationDB
    medications = relationship("MedicationDB", back_populates="patient")


class MedicationDB(Base):
    __tablename__ = "medication"  # Asegúrate de que este nombre coincida con el usado en el transformador

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patient.id"), nullable=False)
    resource_type = Column(String, default="MedicationKnowledge", nullable=False)
    code = Column(String, nullable=False)
    display = Column(String, nullable=False)
    system = Column(String, nullable=False)
    text = Column(String, nullable=False)

    # Relación con PatientDB
    patient = relationship("PatientDB", back_populates="medications")


# === MODELOS PYDANTIC ===

class HumanName(BaseModel):
    use: Optional[str] = None
    family: str
    given: List[str]


class ContactPoint(BaseModel):
    system: str
    value: str


class Coding(BaseModel):
    system: str
    code: str
    display: str


class CodeableConcept(BaseModel):
    coding: List[Coding]
    text: str


class Patient(BaseModel):
    resourceType: str = "Patient"
    id: str
    name: List[HumanName]
    telecom: Optional[List[ContactPoint]] = None


class MedicationKnowledge(BaseModel):
    resourceType: str = "MedicationKnowledge"
    id: str
    code: CodeableConcept
    patientId: Optional[str] = None