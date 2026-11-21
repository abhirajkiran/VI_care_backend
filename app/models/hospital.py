from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, Table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Hospital(Base, TimestampMixin):
    __tablename__ = "hospitals"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    logo_url = Column(String(500), default="assets/images/logo.png")
    address = Column(String(300), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_open_now = Column(Boolean, default=True)
    working_hours = Column(String(150), default="Open 24/7 • Emergency & Critical Care")
    phone = Column(String(50), nullable=False)
    emergency_phone = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    about = Column(Text, nullable=True)
    departments = Column(ARRAY(String), default=list)
    branches = Column(ARRAY(String), default=list)
    department_count = Column(Integer, default=0)
    rating = Column(Float, default=4.8)
    review_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationships
    doctors = relationship("Doctor", back_populates="hospital", cascade="all, delete-orphan")
    services = relationship("HospitalService", back_populates="hospital", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="hospital")


class HospitalService(Base, TimestampMixin):
    __tablename__ = "hospital_services"

    id = Column(String(50), primary_key=True, index=True)
    hospital_id = Column(String(50), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    price = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True)

    hospital = relationship("Hospital", back_populates="services")
