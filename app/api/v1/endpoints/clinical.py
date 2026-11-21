import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.clinical import (
    LabOrderItem,
    LabTestCatalogItem,
    MedicalRecordItem,
    PrescriptionItem,
    VitalItem,
)

router = APIRouter()

# In-memory stores for clinical items
_MEDICAL_RECORDS: List[Dict[str, Any]] = [
    {
        "id": "rec_01",
        "patientId": "patient_01",
        "category": "consultation",
        "title": "Cardiology Follow-up Consultation",
        "doctorName": "Dr. Sreelatha Menon",
        "department": "Cardiology",
        "date": datetime.now(timezone.utc).isoformat(),
        "summary": "Regular hypertension checkup. Heart rhythm sinus regular. BP slightly elevated.",
        "findings": ["BP: 135/88 mmHg", "ECG: Normal sinus rhythm", "No chest pain or dyspnea reported"],
        "attachmentUrl": None,
        "fileType": "PDF",
    },
    {
        "id": "rec_02",
        "patientId": "patient_01",
        "category": "labReport",
        "title": "Comprehensive Metabolic Panel (CMP)",
        "doctorName": "Dr. Thomas Joseph",
        "department": "Diagnostics Lab",
        "date": datetime.now(timezone.utc).isoformat(),
        "summary": "Routine metabolic panel. Fasting glucose and HbA1c in optimal range.",
        "findings": ["Fasting Blood Sugar: 95 mg/dL", "HbA1c: 5.6%", "Serum Creatinine: 0.9 mg/dL"],
        "attachmentUrl": None,
        "fileType": "PDF",
    },
]

_PRESCRIPTIONS: List[Dict[str, Any]] = [
    {
        "id": "RX-10492",
        "patientId": "patient_01",
        "patientName": "Aravind Krishnan",
        "patientUhid": "PT-10001",
        "doctorId": "doc_01",
        "doctorName": "Dr. Sreelatha Menon",
        "department": "Cardiology",
        "date": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "medicineName": "Telmisartan 40mg",
                "dosage": "40 mg",
                "frequency": "Once daily (Morning)",
                "duration": "30 days",
                "instructions": "After breakfast",
            },
            {
                "medicineName": "Atorvastatin 10mg",
                "dosage": "10 mg",
                "frequency": "Once daily (Bedtime)",
                "duration": "30 days",
                "instructions": "After dinner",
            },
        ],
        "notes": "Low salt diet recommended. Review in 1 month.",
        "isDispensed": False,
        "hospitalId": "hosp_01",
        "hospitalName": "Vicare Apollo City Hospital",
    }
]

_LAB_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "test_cbc",
        "name": "Complete Blood Count (CBC)",
        "code": "CBC",
        "category": "Hematology",
        "price": 350.0,
        "tatHours": 6,
        "isFastingRequired": False,
        "normalRange": "Standard Reference Values",
    },
    {
        "id": "test_lft",
        "name": "Liver Function Test (LFT)",
        "code": "LFT",
        "category": "Biochemistry",
        "price": 750.0,
        "tatHours": 12,
        "isFastingRequired": True,
        "normalRange": "SGOT: 15-40 U/L, SGPT: 10-49 U/L",
    },
    {
        "id": "test_kft",
        "name": "Kidney Function Test (KFT)",
        "code": "KFT",
        "category": "Biochemistry",
        "price": 600.0,
        "tatHours": 8,
        "isFastingRequired": True,
        "normalRange": "Creatinine: 0.7-1.3 mg/dL, Urea: 15-40 mg/dL",
    },
    {
        "id": "test_lipid",
        "name": "Lipid Profile Panel",
        "code": "LIPID",
        "category": "Cardiology",
        "price": 800.0,
        "tatHours": 12,
        "isFastingRequired": True,
        "normalRange": "Cholesterol: <200 mg/dL, Triglycerides: <150 mg/dL",
    },
]

_LAB_ORDERS: List[Dict[str, Any]] = [
    {
        "id": "LO-8901",
        "patientId": "patient_01",
        "patientName": "Aravind Krishnan",
        "patientUHID": "PT-10001",
        "doctorId": "doc_01",
        "doctorName": "Dr. Sreelatha Menon",
        "department": "Diagnostics Lab",
        "testName": "Lipid Profile Panel",
        "date": datetime.now(timezone.utc).isoformat(),
        "status": "Completed",
        "results": [
            {"parameter": "Total Cholesterol", "value": "185", "unit": "mg/dL", "normalRange": "<200", "flag": "Normal"},
            {"parameter": "HDL (Good)", "value": "52", "unit": "mg/dL", "normalRange": ">40", "flag": "Normal"},
            {"parameter": "LDL (Bad)", "value": "110", "unit": "mg/dL", "normalRange": "<100", "flag": "High"},
        ],
        "remarks": "Fasting sample verified. Borderline high LDL. Lifestyle modification advised.",
    }
]

_VITALS: List[Dict[str, Any]] = [
    {
        "id": "vit_01",
        "patientId": "patient_01",
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "bloodPressure": "120/80",
        "heartRate": 74,
        "temperature": 98.4,
        "spo2": 99,
        "respiratoryRate": 16,
        "weight": 72.5,
        "height": 178.0,
        "recordedBy": "Nurse Priya Nair",
    }
]


# =========================================================================
# MEDICAL RECORDS
# =========================================================================

@router.get("/medical-records", response_model=List[MedicalRecordItem])
async def get_medical_records(patientId: Optional[str] = Query(None)):
    """Returns patient medical records & clinical timeline."""
    if patientId:
        return [MedicalRecordItem(**r) for r in _MEDICAL_RECORDS if r["patientId"] == patientId]
    return [MedicalRecordItem(**r) for r in _MEDICAL_RECORDS]


@router.post("/medical-records", response_model=MedicalRecordItem)
async def create_medical_record(data: Dict[str, Any]):
    """Creates a new medical record entry."""
    new_id = data.get("id") or f"rec_{uuid.uuid4().hex[:8]}"
    item = dict(data)
    item["id"] = new_id
    if "date" not in item:
        item["date"] = datetime.now(timezone.utc)
    _MEDICAL_RECORDS.insert(0, item)
    return MedicalRecordItem(**item)


# =========================================================================
# PRESCRIPTIONS
# =========================================================================

@router.get("/prescriptions", response_model=List[PrescriptionItem])
async def get_prescriptions(patientId: Optional[str] = Query(None)):
    """Returns patient prescriptions."""
    if patientId:
        return [PrescriptionItem(**p) for p in _PRESCRIPTIONS if p["patientId"] == patientId]
    return [PrescriptionItem(**p) for p in _PRESCRIPTIONS]


@router.post("/prescriptions", response_model=PrescriptionItem)
async def create_prescription(data: Dict[str, Any]):
    """Doctor prescription writer: issues prescription to patient."""
    new_id = data.get("id") or f"RX-{uuid.uuid4().int % 90000 + 10000}"
    item = dict(data)
    item["id"] = new_id
    if "date" not in item:
        item["date"] = datetime.now(timezone.utc)
    _PRESCRIPTIONS.insert(0, item)
    return PrescriptionItem(**item)


# =========================================================================
# LAB TESTS & ORDERS
# =========================================================================

@router.get("/lab/tests", response_model=List[LabTestCatalogItem])
@router.get("/lab-tests", response_model=List[LabTestCatalogItem])
async def get_lab_test_catalog():
    """Returns catalog of diagnostic tests."""
    return [LabTestCatalogItem(**t) for t in _LAB_CATALOG]


@router.get("/lab/orders", response_model=List[LabOrderItem])
@router.get("/lab-orders", response_model=List[LabOrderItem])
@router.get("/lab-reports", response_model=List[LabOrderItem])
async def get_lab_orders(patientId: Optional[str] = Query(None)):
    """Returns patient lab orders and completed diagnostic reports."""
    if patientId:
        return [LabOrderItem(**o) for o in _LAB_ORDERS if o["patientId"] == patientId]
    return [LabOrderItem(**o) for o in _LAB_ORDERS]


@router.post("/lab/orders", response_model=LabOrderItem)
@router.post("/lab-orders", response_model=LabOrderItem)
async def create_lab_order(data: Dict[str, Any]):
    """Orders a diagnostic lab test."""
    new_id = data.get("id") or f"LO-{uuid.uuid4().int % 9000 + 1000}"
    item = dict(data)
    item["id"] = new_id
    if "date" not in item:
        item["date"] = datetime.now(timezone.utc)
    _LAB_ORDERS.insert(0, item)
    return LabOrderItem(**item)


@router.patch("/lab/orders/{order_id}/status")
@router.patch("/lab-orders/{order_id}/status")
async def update_lab_order_status(order_id: str, data: Dict[str, Any]):
    """Lab technician updates test status & uploads parameters."""
    order = next((o for o in _LAB_ORDERS if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")

    order["status"] = data.get("status", order["status"])
    if "results" in data and data["results"] is not None:
        order["results"] = data["results"]
    if "remarks" in data and data["remarks"] is not None:
        order["remarks"] = data["remarks"]

    return {"success": True, "order": order}


# =========================================================================
# VITALS
# =========================================================================

@router.get("/vitals", response_model=List[VitalItem])
async def get_vitals(patientId: Optional[str] = Query(None)):
    """Returns recorded patient vital history."""
    if patientId:
        return [VitalItem(**v) for v in _VITALS if v["patientId"] == patientId]
    return [VitalItem(**v) for v in _VITALS]


@router.post("/vitals", response_model=VitalItem)
async def record_vital(data: Dict[str, Any]):
    """Records patient vitals (Nurse rounds / OPD triage)."""
    new_id = data.get("id") or f"vit_{uuid.uuid4().hex[:6]}"
    item = dict(data)
    item["id"] = new_id
    if "recordedAt" not in item:
        item["recordedAt"] = datetime.now(timezone.utc)
    _VITALS.insert(0, item)
    return VitalItem(**item)
