from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DepartmentResponse(BaseModel):
    id: str
    hospital_id: Optional[str] = Field(default=None, alias="hospitalId")
    name: str
    code: str
    head_doctor: Optional[str] = Field(default="Dr. Chief of Department", alias="headDoctor")
    doctors_count: int = Field(default=4, alias="doctorsCount")
    staff_count: int = Field(default=12, alias="staffCount")
    total_beds: int = Field(default=30, alias="totalBeds")
    available_beds: int = Field(default=8, alias="availableBeds")
    active_appointments: int = Field(default=5, alias="activeAppointments")
    description: Optional[str] = ""

    model_config = ConfigDict(populate_by_name=True)
