from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Query
from app.schemas.staff import AuditLogItem, StaffMemberItem

router = APIRouter()

_STAFF_MEMBERS: List[dict] = [
    {
        "id": "EMP-401",
        "hospitalId": "hosp_01",
        "name": "Priya Nair",
        "role": "Head Nurse",
        "department": "Cardiology",
        "phone": "+91 98450 12345",
        "email": "priya.nair@vicare.internal",
        "joiningDate": "2023-04-10",
        "shift": "Morning",
        "status": "Active",
    },
    {
        "id": "EMP-402",
        "hospitalId": "hosp_01",
        "name": "Rahul Verma",
        "role": "Reception Lead",
        "department": "Reception Desk",
        "phone": "+91 98450 54321",
        "email": "rahul.verma@vicare.internal",
        "joiningDate": "2023-08-01",
        "shift": "Morning",
        "status": "Active",
    },
    {
        "id": "EMP-403",
        "hospitalId": "hosp_01",
        "name": "Anjali Menon",
        "role": "OPD Nurse",
        "department": "General Medicine",
        "phone": "+91 98450 99887",
        "email": "anjali.menon@vicare.internal",
        "joiningDate": "2024-01-15",
        "shift": "Evening",
        "status": "Active",
    },
]

_AUDIT_LOGS: List[dict] = [
    {
        "id": "AUD-1001",
        "hospitalId": "hosp_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "Status Changed",
        "module": "Doctor Queue",
        "recordId": "QTOK-01",
        "ipAddress": "192.168.1.10",
        "userName": "Dr. Sreelatha Menon",
        "userRole": "Doctor",
        "details": "Consultation started for Token A-01",
    },
    {
        "id": "AUD-1002",
        "hospitalId": "hosp_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "Created",
        "module": "Appointments",
        "recordId": "APT-1002",
        "ipAddress": "192.168.1.15",
        "userName": "Rahul Verma",
        "userRole": "Receptionist",
        "details": "Walk-in patient registered token W-01",
    },
]


@router.get("/staff", response_model=List[StaffMemberItem])
async def get_staff_members(
    hospitalId: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
):
    """Returns staff roster for hospital administration."""
    staff = _STAFF_MEMBERS
    if hospitalId:
        staff = [s for s in staff if s.get("hospitalId") == hospitalId]
    if department:
        staff = [s for s in staff if s.get("department", "").lower() == department.lower()]
    return [StaffMemberItem(**s) for s in staff]


@router.get("/audit-logs", response_model=List[AuditLogItem])
async def get_audit_logs(
    hospitalId: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
):
    """Compliance & operational audit logs."""
    logs = _AUDIT_LOGS
    if hospitalId:
        logs = [l for l in logs if l.get("hospitalId") == hospitalId]
    if module:
        logs = [l for l in logs if l.get("module", "").lower() == module.lower()]
    return [AuditLogItem(**l) for l in logs]
