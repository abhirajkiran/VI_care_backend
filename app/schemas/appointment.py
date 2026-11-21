from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    doctor_id: str = Field(alias="doctorId")
    doctor_name: str = Field(alias="doctorName")
    doctor_specialization: str = Field(alias="doctorSpecialization")
    department: str
    hospital_id: str = Field(alias="hospitalId")
    hospital_name: str = Field(alias="hospitalName")
    appointment_date: date = Field(alias="appointmentDate")
    time_slot: str = Field(alias="timeSlot")
    room_number: Optional[str] = Field(default="OPD 101", alias="roomNumber")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AppointmentResponse(BaseModel):
    id: str
    patient_id: str = Field(alias="patientId")
    patient_name: str = Field(alias="patientName")
    doctor_id: str = Field(alias="doctorId")
    doctor_name: str = Field(alias="doctorName")
    doctor_specialization: str = Field(alias="doctorSpecialization")
    department: str
    hospital_id: str = Field(alias="hospitalId")
    hospital_name: str = Field(alias="hospitalName")
    appointment_date: date = Field(alias="appointmentDate")
    time_slot: str = Field(alias="timeSlot")
    status: str
    token_number: str = Field(alias="tokenNumber")
    now_serving_token: str = Field(default="A-01", alias="nowServingToken")
    patients_ahead: int = Field(default=0, alias="patientsAhead")
    estimated_wait_minutes: int = Field(default=15, alias="estimatedWaitMinutes")
    room_number: Optional[str] = Field(default="OPD 101", alias="roomNumber")
    booking_date: Optional[datetime] = Field(default=None, alias="bookingDate")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class QueueStatusResponse(BaseModel):
    appointment_id: str = Field(alias="appointmentId")
    token_number: str = Field(alias="tokenNumber")
    now_serving_token: str = Field(alias="nowServingToken")
    patients_ahead: int = Field(alias="patientsAhead")
    estimated_wait_minutes: int = Field(alias="estimatedWaitMinutes")

    model_config = ConfigDict(populate_by_name=True)


class CancelAppointmentRequest(BaseModel):
    reason: Optional[str] = "Patient request"


class RescheduleAppointmentRequest(BaseModel):
    date: date
    time_slot: str = Field(alias="timeSlot")

    model_config = ConfigDict(populate_by_name=True)


class CheckInRequest(BaseModel):
    appointment_id: str = Field(alias="appointmentId")

    model_config = ConfigDict(populate_by_name=True)


class UpdateAppointmentStatusRequest(BaseModel):
    status: str
