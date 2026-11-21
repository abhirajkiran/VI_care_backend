from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DoctorBase(BaseModel):
    id: str
    name: str
    specialization: str
    qualifications: str
    experience_years: int = Field(default=5, alias="experienceYears")
    department: str
    languages: List[str] = ["English"]
    consultation_fee: float = Field(default=500.0, alias="consultationFee")
    hospital_id: str = Field(alias="hospitalId")
    hospital_name: str = Field(default="", alias="hospitalName")
    distance_km: float = Field(default=0.0, alias="distanceKm")
    hospital_location: str = Field(default="OPD Room 101", alias="hospitalLocation")
    available_schedule: str = Field(default="Mon - Fri", alias="availableSchedule")
    available_days: List[str] = Field(default=["Mon", "Tue", "Wed", "Thu", "Fri"], alias="availableDays")
    rating: float = 4.8
    review_count: int = Field(default=0, alias="reviewCount")
    photo_url: Optional[str] = Field(default="", alias="photoUrl")
    next_available_slot: str = Field(default="Today • 10:00 AM", alias="nextAvailableSlot")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class DoctorResponse(DoctorBase):
    pass


class DoctorSlotsResponse(BaseModel):
    doctor_id: str
    date: str
    slots: List[str]
