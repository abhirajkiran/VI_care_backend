from datetime import date
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id = Column(String(50), primary_key=True, index=True)
    uhid = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False, index=True)
    date_of_birth = Column(Date, default=date(1990, 1, 1), nullable=False)
    gender = Column(String(20), default="Male", nullable=False)
    blood_group = Column(String(10), default="O+", nullable=False)
    phone = Column(String(30), unique=True, index=True, nullable=False)
    email = Column(String(100), default="", nullable=False)
    address = Column(String(300), default="", nullable=False)
    avatar_url = Column(String(500), nullable=True)
    emergency_contact_name = Column(String(150), default="")
    emergency_contact_phone = Column(String(50), default="")
    emergency_contact_relation = Column(String(50), default="")
    allergies = Column(ARRAY(String), default=list)
    chronic_conditions = Column(ARRAY(String), default=list)

    # Relationships
    family_members = relationship("FamilyMember", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient")
    notifications = relationship("Notification", back_populates="patient", cascade="all, delete-orphan")


class FamilyMember(Base, TimestampMixin):
    __tablename__ = "family_members"

    id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    relation = Column(String(50), nullable=False)
    uhid = Column(String(50), nullable=False)
    age = Column(String(10), nullable=True)
    gender = Column(String(20), nullable=True)

    patient = relationship("Patient", back_populates="family_members")
