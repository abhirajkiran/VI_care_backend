from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QueueTokenItem(BaseModel):
    id: str
    hospital_id: str = Field(alias="hospitalId")
    doctor_id: str = Field(alias="doctorId")
    patient_id: str = Field(alias="patientId")
    appointment_id: Optional[str] = Field(default=None, alias="appointmentId")
    token_number: str = Field(alias="tokenNumber")
    token_label: str = Field(alias="tokenLabel")
    patient_name: str = Field(alias="patientName")
    patient_phone: str = Field(default="+91 98765 43210", alias="patientPhone")
    scheduled_time: str = Field(default="10:00 AM", alias="scheduledTime")
    status: str
    is_emergency: bool = Field(default=False, alias="isEmergency")
    emergency_reason: Optional[str] = Field(default=None, alias="emergencyReason")
    is_walk_in: bool = Field(default=False, alias="isWalkIn")
    estimated_wait_minutes: int = Field(default=15, alias="estimatedWaitMinutes")
    room_number: Optional[str] = Field(default="OPD 101", alias="roomNumber")

    model_config = ConfigDict(populate_by_name=True)


class QueueSummaryResponse(BaseModel):
    doctor_id: str = Field(alias="doctorId")
    hospital_id: str = Field(alias="hospitalId")
    date: str
    is_paused: bool = Field(default=False, alias="isPaused")
    pause_reason: Optional[str] = Field(default=None, alias="pauseReason")
    delay_minutes: int = Field(default=0, alias="delayMinutes")
    active_patient: Optional[Dict[str, Any]] = Field(default=None, alias="activePatient")
    waiting_count: int = Field(default=0, alias="waitingCount")
    completed_count: int = Field(default=0, alias="completedCount")
    no_show_count: int = Field(default=0, alias="noShowCount")
    skipped_count: int = Field(default=0, alias="skippedCount")
    rolling_avg_minutes: int = Field(default=10, alias="rollingAvgMinutes")
    tokens: List[QueueTokenItem] = []

    model_config = ConfigDict(populate_by_name=True)


class QueueStartRequest(BaseModel):
    client_version: Optional[int] = Field(default=None, alias="clientVersion")


class QueueDoneRequest(BaseModel):
    notes: Optional[str] = None


class QueueSkipRequest(BaseModel):
    reason: Optional[str] = "Patient not present when called"


class QueueEmergencyRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Medical justification for emergency queue jump")


class QueueWalkInRequest(BaseModel):
    doctor_id: str = Field(alias="doctorId")
    hospital_id: str = Field(alias="hospitalId")
    patient_name: str = Field(alias="patientName")
    patient_phone: str = Field(alias="patientPhone")
    age: Optional[int] = 30
    gender: Optional[str] = "Other"

    model_config = ConfigDict(populate_by_name=True)


class QueuePauseRequest(BaseModel):
    doctor_id: str = Field(alias="doctorId")
    hospital_id: str = Field(alias="hospitalId")
    reason: Optional[str] = "Doctor Break"

    model_config = ConfigDict(populate_by_name=True)


class QueueResumeRequest(BaseModel):
    doctor_id: str = Field(alias="doctorId")
    hospital_id: str = Field(alias="hospitalId")

    model_config = ConfigDict(populate_by_name=True)


class QueueDelayRequest(BaseModel):
    doctor_id: str = Field(alias="doctorId")
    hospital_id: str = Field(alias="hospitalId")
    delay_minutes: int = Field(..., alias="delayMinutes", ge=0)

    model_config = ConfigDict(populate_by_name=True)
