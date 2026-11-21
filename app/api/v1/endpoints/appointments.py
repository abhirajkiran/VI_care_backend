import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    CancelAppointmentRequest,
    CheckInRequest,
    QueueStatusResponse,
    RescheduleAppointmentRequest,
    UpdateAppointmentStatusRequest,
)
from app.services.token_service import generate_token

router = APIRouter()


@router.get("", response_model=List[AppointmentResponse])
async def get_appointments(
    patientId: Optional[str] = Query(None),
    doctorId: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_patient_id: str = Depends(get_current_user_id),
):
    """Returns patient visit appointments."""
    target_patient_id = patientId or current_patient_id
    stmt = select(Appointment)

    if target_patient_id:
        stmt = stmt.where(Appointment.patient_id == target_patient_id)
    if doctorId:
        stmt = stmt.where(Appointment.doctor_id == doctorId)

    stmt = stmt.order_by(Appointment.appointment_date.desc())
    result = await db.execute(stmt)
    appts = result.scalars().all()
    return [AppointmentResponse.model_validate(a) for a in appts]


@router.post("", response_model=AppointmentResponse)
async def book_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_patient_id: str = Depends(get_current_user_id),
):
    """Books doctor appointment and issues an atomic daily Token number."""
    # Fetch patient name
    stmt = select(Patient).where(Patient.id == current_patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    patient_name = patient.name if patient else "Aravind Krishnan"

    # Generate atomic daily token (e.g. A-14)
    token_str, seq = await generate_token(db, payload.doctor_id, payload.appointment_date)

    appt_id = f"APT-{uuid.uuid4().int % 90000 + 10000}"
    patients_ahead = max(0, seq - 1)
    est_wait = patients_ahead * 10 + 10

    appt = Appointment(
        id=appt_id,
        patient_id=current_patient_id,
        patient_name=patient_name,
        doctor_id=payload.doctor_id,
        doctor_name=payload.doctor_name,
        doctor_specialization=payload.doctor_specialization,
        department=payload.department,
        hospital_id=payload.hospital_id,
        hospital_name=payload.hospital_name,
        appointment_date=payload.appointment_date,
        time_slot=payload.time_slot,
        status="scheduled",
        token_number=token_str,
        now_serving_token="A-01",
        patients_ahead=patients_ahead,
        estimated_wait_minutes=est_wait,
        room_number=payload.room_number or "OPD 101",
        booking_date=datetime.now(timezone.utc),
        notes=payload.notes,
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)

    return AppointmentResponse.model_validate(appt)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_by_id(appointment_id: str, db: AsyncSession = Depends(get_db)):
    """Returns single appointment by ID."""
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return AppointmentResponse.model_validate(appt)


@router.post("/{appointment_id}/cancel")
@router.patch("/{appointment_id}/cancel")
@router.put("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    payload: CancelAppointmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cancels a scheduled appointment."""
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "cancelled"
    appt.notes = f"Cancelled: {payload.reason}"
    await db.commit()
    return {"success": True, "message": "Appointment cancelled successfully"}


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: str,
    payload: RescheduleAppointmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reschedules a scheduled appointment to a new date and time slot."""
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.appointment_date = payload.date
    appt.time_slot = payload.time_slot
    appt.status = "scheduled"
    await db.commit()
    await db.refresh(appt)
    return AppointmentResponse.model_validate(appt)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: str,
    payload: UpdateAppointmentStatusRequest,
    db: AsyncSession = Depends(get_db),
):
    """Updates appointment status (scheduled, in_progress, completed, cancelled, no_show)."""
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = payload.status
    await db.commit()
    await db.refresh(appt)
    return AppointmentResponse.model_validate(appt)


@router.post("/check-in", response_model=AppointmentResponse)
async def check_in(
    payload: CheckInRequest,
    db: AsyncSession = Depends(get_db),
):
    """Checks in patient on arrival and activates token queue position."""
    stmt = select(Appointment).where(Appointment.id == payload.appointment_id)
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "checkedIn"
    await db.commit()
    await db.refresh(appt)
    return AppointmentResponse.model_validate(appt)


@router.get("/{appointment_id}/queue", response_model=QueueStatusResponse)
async def get_queue_status(appointment_id: str, db: AsyncSession = Depends(get_db)):
    """Returns live queue status (now serving token and estimated wait time)."""
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return QueueStatusResponse(
        appointment_id=appt.id,
        token_number=appt.token_number,
        now_serving_token=appt.now_serving_token or "A-01",
        patients_ahead=appt.patients_ahead,
        estimated_wait_minutes=appt.estimated_wait_minutes,
    )
