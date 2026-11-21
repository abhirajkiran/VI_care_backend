from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordItem(BaseModel):
    id: str
    patient_id: str = Field(alias="patientId")
    category: str = "consultation"
    title: str
    doctor_name: str = Field(alias="doctorName")
    department: str
    date: datetime = Field(default_factory=datetime.utcnow)
    summary: str
    findings: List[str] = []
    attachment_url: Optional[str] = Field(default=None, alias="attachmentUrl")
    file_type: str = Field(default="PDF", alias="fileType")

    model_config = ConfigDict(populate_by_name=True)


class PrescriptionMedicineItem(BaseModel):
    medicine_name: str = Field(alias="medicineName")
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = "After food"

    model_config = ConfigDict(populate_by_name=True)


class PrescriptionItem(BaseModel):
    id: str
    patient_id: str = Field(alias="patientId")
    patient_name: str = Field(alias="patientName")
    patient_uhid: Optional[str] = Field(default=None, alias="patientUhid")
    doctor_id: str = Field(alias="doctorId")
    doctor_name: str = Field(alias="doctorName")
    department: str
    date: datetime = Field(default_factory=datetime.utcnow)
    items: List[PrescriptionMedicineItem] = []
    notes: Optional[str] = ""
    is_dispensed: bool = Field(default=False, alias="isDispensed")
    hospital_id: Optional[str] = Field(default=None, alias="hospitalId")
    hospital_name: Optional[str] = Field(default=None, alias="hospitalName")

    model_config = ConfigDict(populate_by_name=True)


class LabTestCatalogItem(BaseModel):
    id: str
    name: str
    code: str
    category: str
    price: float
    tat_hours: int = Field(default=24, alias="tatHours")
    is_fasting_required: bool = Field(default=False, alias="isFastingRequired")
    normal_range: Optional[str] = Field(default="", alias="normalRange")

    model_config = ConfigDict(populate_by_name=True)


class LabOrderItem(BaseModel):
    id: str
    patient_id: str = Field(alias="patientId")
    patient_name: str = Field(alias="patientName")
    patient_uhid: Optional[str] = Field(default="PT-10001", alias="patientUHID")
    doctor_id: Optional[str] = Field(default="doc_01", alias="doctorId")
    doctor_name: str = Field(alias="doctorName")
    department: Optional[str] = "Diagnostics Lab"
    test_name: str = Field(alias="testName")
    date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "Ordered"  # Ordered, In Progress, Completed
    results: Optional[List[Dict[str, Any]]] = []
    remarks: Optional[str] = None
    technician_remarks: Optional[str] = Field(default=None, alias="technicianRemarks")

    model_config = ConfigDict(populate_by_name=True)


class VitalItem(BaseModel):
    id: str
    patient_id: str = Field(alias="patientId")
    recorded_at: datetime = Field(default_factory=datetime.utcnow, alias="recordedAt")
    blood_pressure: str = Field(default="120/80", alias="bloodPressure")
    heart_rate: int = Field(default=72, alias="heartRate")
    temperature: float = 98.6
    spo2: int = 98
    respiratory_rate: int = Field(default=16, alias="respiratoryRate")
    weight: float = 70.0
    height: Optional[float] = 175.0
    recorded_by: str = Field(default="Staff Nurse", alias="recordedBy")

    model_config = ConfigDict(populate_by_name=True)
