from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    category = Column(String(50), default="appointment", nullable=False)
    action_route = Column(String(100), nullable=True)
    related_id = Column(String(50), nullable=True)

    patient = relationship("Patient", back_populates="notifications")
