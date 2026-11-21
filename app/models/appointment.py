from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_name = Column(String(150), nullable=False)
    doctor_id = Column(String(50), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(150), nullable=False)
    doctor_specialization = Column(String(150), nullable=False)
    department = Column(String(100), nullable=False)
    hospital_id = Column(String(50), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    hospital_name = Column(String(200), nullable=False)
    appointment_date = Column(Date, nullable=False, index=True)
    time_slot = Column(String(50), nullable=False)
    status = Column(String(30), default="scheduled", nullable=False, index=True)  # scheduled, completed, cancelled, in_progress, no_show, skipped
    token_number = Column(String(20), nullable=False)
    now_serving_token = Column(String(20), default="A-01")
    patients_ahead = Column(Integer, default=0)
    estimated_wait_minutes = Column(Integer, default=15)
    room_number = Column(String(50), default="OPD 101")
    booking_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)
    is_emergency = Column(Boolean, default=False)
    emergency_reason = Column(String(255), nullable=True)
    is_walk_in = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    hospital = relationship("Hospital", back_populates="appointments")
