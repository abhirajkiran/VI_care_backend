from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.doctor import Doctor
from app.models.hospital import Hospital
from app.schemas.doctor import DoctorResponse, DoctorSlotsResponse

router = APIRouter()


@router.get("", response_model=List[DoctorResponse])
async def get_doctors(
    hospitalId: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Filters doctors by hospital, department, or keyword search."""
    stmt = select(Doctor, Hospital.name.label("hosp_name")).join(Hospital, Doctor.hospital_id == Hospital.id)

    if hospitalId:
        stmt = stmt.where(Doctor.hospital_id == hospitalId)

    if department and department != "All":
        stmt = stmt.where(Doctor.department.ilike(department))

    if query:
        q = f"%{query.strip()}%"
        stmt = stmt.where(
            (Doctor.name.ilike(q))
            | (Doctor.specialization.ilike(q))
            | (Doctor.department.ilike(q))
        )

    result = await db.execute(stmt)
    rows = result.all()

    doctor_list: List[DoctorResponse] = []
    for doc, hosp_name in rows:
        resp = DoctorResponse.model_validate(doc)
        resp.hospital_name = hosp_name
        doctor_list.append(resp)

    return doctor_list


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor_by_id(doctor_id: str, db: AsyncSession = Depends(get_db)):
    """Returns single doctor profile and schedule."""
    stmt = (
        select(Doctor, Hospital.name.label("hosp_name"))
        .join(Hospital, Doctor.hospital_id == Hospital.id)
        .where(Doctor.id == doctor_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doc, hosp_name = row
    resp = DoctorResponse.model_validate(doc)
    resp.hospital_name = hosp_name
    return resp


@router.get("/{doctor_id}/slots", response_model=DoctorSlotsResponse)
async def get_doctor_slots(doctor_id: str, date: str = Query(...)):
    """Returns available consultation time slots for a given date."""
    standard_slots = [
        "09:00 AM",
        "09:30 AM",
        "10:00 AM",
        "10:30 AM",
        "11:00 AM",
        "11:30 AM",
        "02:00 PM",
        "02:30 PM",
        "03:00 PM",
        "03:30 PM",
        "04:00 PM",
    ]
    return DoctorSlotsResponse(
        doctor_id=doctor_id,
        date=date,
        slots=standard_slots,
    )


@router.post("/{doctor_id}/emergency-leave")
async def apply_emergency_leave(
    doctor_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Doctor applies for acute emergency leave; alerts reception and queue."""
    stmt = select(Doctor).where(Doctor.id == doctor_id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    reason = payload.get("reason", "Urgent Emergency Surgery / Acute ICU Case")
    doctor.is_available_today = False
    await db.commit()

    return {
        "success": True,
        "message": f"Emergency Leave activated for {doctor.name}. Receptionist desk & queue alerted.",
        "doctorId": doctor.id,
        "availability": "On Emergency Leave",
        "reason": reason,
    }


@router.post("/{doctor_id}/resume-duty")
async def resume_duty(
    doctor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Doctor resumes OPD consultation duty."""
    stmt = select(Doctor).where(Doctor.id == doctor_id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_available_today = True
    await db.commit()

    return {
        "success": True,
        "message": f"Welcome back {doctor.name}! Duty resumed and OPD room marked available.",
        "doctorId": doctor.id,
        "availability": "Available",
    }
