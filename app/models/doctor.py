from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"

    id = Column(String(50), primary_key=True, index=True)
    hospital_id = Column(String(50), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    specialization = Column(String(150), nullable=False)
    qualifications = Column(String(200), nullable=False)
    experience_years = Column(Integer, default=5)
    department = Column(String(100), nullable=False, index=True)
    languages = Column(ARRAY(String), default=lambda: ["English"])
    consultation_fee = Column(Float, default=500.0)
    hospital_location = Column(String(150), default="OPD Room 101")
    available_schedule = Column(String(150), default="Mon - Fri (09:00 AM - 01:00 PM)")
    available_days = Column(ARRAY(String), default=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"])
    rating = Column(Float, default=4.8)
    review_count = Column(Integer, default=0)
    photo_url = Column(String(500), nullable=True)
    next_available_slot = Column(String(100), default="Today • 10:00 AM")
    is_active = Column(Boolean, default=True)

    # Relationships
    hospital = relationship("Hospital", back_populates="doctors")
    appointments = relationship("Appointment", back_populates="doctor")
