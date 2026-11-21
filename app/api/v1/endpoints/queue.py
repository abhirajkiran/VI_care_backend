import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.hospital import Hospital
from app.models.patient import Patient
from app.schemas.queue import (
    QueueDelayRequest,
    QueueDoneRequest,
    QueueEmergencyRequest,
    QueuePauseRequest,
    QueueResumeRequest,
    QueueSkipRequest,
    QueueStartRequest,
    QueueSummaryResponse,
    QueueTokenItem,
    QueueWalkInRequest,
)

router = APIRouter()

# In-memory session delay/pause states for active doctors
_DOCTOR_QUEUE_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _get_session(doctor_id: str, hospital_id: str) -> Dict[str, Any]:
    key = f"{doctor_id}:{hospital_id}"
    if key not in _DOCTOR_QUEUE_SESSIONS:
        _DOCTOR_QUEUE_SESSIONS[key] = {
            "doctorId": doctor_id,
            "hospitalId": hospital_id,
            "isPaused": False,
            "pauseReason": None,
            "delayMinutes": 0,
            "currentActiveTokenId": None,
        }
    return _DOCTOR_QUEUE_SESSIONS[key]


@router.get("/patient/{id_or_token}/position")
async def get_patient_queue_position(
    id_or_token: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Returns real-time queue position, now serving token, and estimated wait minutes."""
    stmt = select(Appointment).where(
        or_(
            Appointment.id == id_or_token,
            Appointment.token_number == id_or_token,
        )
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()

    if not appt:
        raise HTTPException(status_code=404, detail="Queue token or appointment not found")

    session = _get_session(appt.doctor_id, appt.hospital_id)
    est_wait = max(0, (appt.patients_ahead * 10) + session.get("delayMinutes", 0))

    return {
        "success": True,
        "appointmentId": appt.id,
        "tokenId": appt.id,
        "tokenNumber": appt.token_number,
        "nowServingToken": appt.now_serving_token or "A-01",
        "patientsAhead": max(0, appt.patients_ahead),
        "estimatedWaitMinutes": est_wait,
        "status": appt.status,
        "roomNumber": appt.room_number or "OPD 101",
        "doctorName": appt.doctor_name,
        "isDoctorPaused": session.get("isPaused", False),
        "doctorDelayMinutes": session.get("delayMinutes", 0),
        "appointmentDate": appt.appointment_date.isoformat() if appt.appointment_date else None,
    }


@router.post("/patient/{token_id}/rejoin")
async def rejoin_queue(
    token_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Allows a skipped patient to rejoin the queue with a new position."""
    stmt = select(Appointment).where(
        or_(
            Appointment.id == token_id,
            Appointment.token_number == token_id,
        )
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()

    if not appt:
        raise HTTPException(status_code=404, detail="Token not found")

    appt.status = "scheduled"
    appt.patients_ahead = 3
    appt.estimated_wait_minutes = 20
    await db.commit()
    await db.refresh(appt)

    return {
        "success": True,
        "message": f"Token {appt.token_number} rejoined queue",
        "tokenNumber": appt.token_number,
        "status": appt.status,
        "patientsAhead": appt.patients_ahead,
    }


async def _generate_queue_summary(
    doc_id: str,
    hosp_id: str,
    date_str: Optional[str],
    db: AsyncSession,
) -> QueueSummaryResponse:
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    session = _get_session(doc_id, hosp_id)

    # Fetch appointments
    stmt = (
        select(Appointment)
        .where(
            Appointment.doctor_id == doc_id,
            Appointment.appointment_date == target_date,
        )
        .order_by(Appointment.token_number)
    )
    result = await db.execute(stmt)
    appts = result.scalars().all()

    waiting = [a for a in appts if a.status in ("scheduled", "checkedIn")]
    completed = [a for a in appts if a.status in ("completed", "Completed")]
    in_progress = next((a for a in appts if a.status in ("inProgress", "in_progress", "In Consultation")), None)
    no_show = [a for a in appts if a.status in ("no_show", "No-show")]
    skipped = [a for a in appts if a.status in ("skipped", "Skipped")]

    token_items = [
        QueueTokenItem(
            id=a.id,
            hospital_id=a.hospital_id,
            doctor_id=a.doctor_id,
            patient_id=a.patient_id,
            appointment_id=a.id,
            token_number=a.token_number,
            token_label=f"#{a.token_number}",
            patient_name=a.patient_name,
            scheduled_time=a.time_slot,
            status=a.status,
            is_emergency=getattr(a, "is_emergency", False) or False,
            emergency_reason=getattr(a, "emergency_reason", None),
            is_walk_in=getattr(a, "is_walk_in", False) or False,
            estimated_wait_minutes=a.estimated_wait_minutes or 15,
            room_number=a.room_number,
        )
        for a in appts
    ]

    active_dict = None
    if in_progress:
        active_dict = {
            "id": in_progress.id,
            "tokenNumber": in_progress.token_number,
            "patientName": in_progress.patient_name,
            "timeSlot": in_progress.time_slot,
            "status": "In Consultation",
        }

    return QueueSummaryResponse(
        doctor_id=doc_id,
        hospital_id=hosp_id,
        date=target_date.isoformat(),
        is_paused=session.get("isPaused", False),
        pause_reason=session.get("pauseReason"),
        delay_minutes=session.get("delayMinutes", 0),
        active_patient=active_dict,
        waiting_count=len(waiting),
        completed_count=len(completed),
        no_show_count=len(no_show),
        skipped_count=len(skipped),
        rolling_avg_minutes=10,
        tokens=token_items,
    )


@router.get("/summary", response_model=QueueSummaryResponse)
async def get_queue_summary_query(
    doctorId: Optional[str] = Query(None),
    hospitalId: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """High-level OPD queue summary with query parameters."""
    return await _generate_queue_summary(
        doc_id=doctorId or "doc_01",
        hosp_id=hospitalId or "hosp_01",
        date_str=date,
        db=db,
    )


@router.get("/doctor/{doctor_id}/summary", response_model=QueueSummaryResponse)
async def get_doctor_queue_summary_path(
    doctor_id: str,
    hospitalId: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """High-level OPD queue summary with path parameter."""
    return await _generate_queue_summary(
        doc_id=doctor_id,
        hosp_id=hospitalId or "hosp_01",
        date_str=date,
        db=db,
    )


@router.get("/doctor/{doctor_id}/live")
async def get_doctor_live_queue(
    doctor_id: str,
    date_str: Optional[str] = Query(None, alias="date"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Returns live OPD queue screen for doctor/nurse dashboard."""
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    doc_stmt = select(Doctor).where(Doctor.id == doctor_id)
    doc_res = await db.execute(doc_stmt)
    doctor = doc_res.scalar_one_or_none()

    appt_stmt = (
        select(Appointment)
        .where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == target_date,
        )
        .order_by(Appointment.token_number)
    )
    appt_res = await db.execute(appt_stmt)
    appts = appt_res.scalars().all()

    waiting = [a for a in appts if a.status in ("scheduled", "checkedIn")]
    completed = [a for a in appts if a.status in ("completed", "Completed")]
    in_progress = next((a for a in appts if a.status in ("inProgress", "in_progress", "In Consultation")), None)

    now_serving = in_progress.token_number if in_progress else (waiting[0].token_number if waiting else "None")

    return {
        "success": True,
        "doctorId": doctor_id,
        "doctorName": doctor.name if doctor else "Doctor",
        "date": target_date.isoformat(),
        "nowServingToken": now_serving,
        "totalPatientsToday": len(appts),
        "waitingCount": len(waiting),
        "completedCount": len(completed),
        "averageConsultationMinutes": 10,
        "tokens": [
            {
                "id": a.id,
                "tokenNumber": a.token_number,
                "patientId": a.patient_id,
                "patientName": a.patient_name,
                "status": a.status,
                "timeSlot": a.time_slot,
                "roomNumber": a.room_number,
                "isEmergency": getattr(a, "is_emergency", False) or False,
            }
            for a in appts
        ],
    }


# =========================================================================
# QUEUE ACTIONS (Doctor & Staff Console)
# =========================================================================

@router.post("/tokens/{token_id}/start")
async def start_consultation(
    token_id: str,
    payload: QueueStartRequest = QueueStartRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Starts consultation. Validates only one patient is in consultation at a time per doctor."""
    stmt = select(Appointment).where(
        or_(Appointment.id == token_id, Appointment.token_number == token_id)
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Token/Appointment not found")

    # Check if another patient is in consultation
    active_stmt = select(Appointment).where(
        Appointment.doctor_id == appt.doctor_id,
        Appointment.appointment_date == appt.appointment_date,
        Appointment.status.in_(["inProgress", "in_progress", "In Consultation"]),
        Appointment.id != appt.id,
    )
    active_res = await db.execute(active_stmt)
    active_other = active_res.scalar_one_or_none()
    if active_other:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Doctor already has an active consultation in progress (Token #{active_other.token_number}). Mark it Done or Skip before starting another.",
        )

    appt.status = "In Consultation"
    appt.now_serving_token = appt.token_number
    if hasattr(appt, "started_at"):
        appt.started_at = datetime.now(timezone.utc)

    session = _get_session(appt.doctor_id, appt.hospital_id)
    session["currentActiveTokenId"] = appt.id

    await db.commit()
    await db.refresh(appt)

    return {
        "success": True,
        "message": f"Consultation started for Token #{appt.token_number}",
        "tokenId": appt.id,
        "tokenNumber": appt.token_number,
        "status": appt.status,
    }


@router.post("/tokens/{token_id}/done")
async def mark_done(
    token_id: str,
    payload: QueueDoneRequest = QueueDoneRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Marks consultation as Completed."""
    stmt = select(Appointment).where(
        or_(Appointment.id == token_id, Appointment.token_number == token_id)
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Token/Appointment not found")

    appt.status = "Completed"
    if payload.notes:
        appt.notes = f"{appt.notes or ''} | Consultation: {payload.notes}".strip(" |")
    if hasattr(appt, "completed_at"):
        appt.completed_at = datetime.now(timezone.utc)

    session = _get_session(appt.doctor_id, appt.hospital_id)
    if session.get("currentActiveTokenId") == appt.id:
        session["currentActiveTokenId"] = None

    await db.commit()
    await db.refresh(appt)

    return {
        "success": True,
        "message": f"Consultation completed for Token #{appt.token_number}",
        "tokenId": appt.id,
        "tokenNumber": appt.token_number,
        "status": appt.status,
    }


@router.post("/tokens/{token_id}/skip")
async def skip_patient(
    token_id: str,
    payload: QueueSkipRequest = QueueSkipRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Skips patient (called but not present)."""
    stmt = select(Appointment).where(
        or_(Appointment.id == token_id, Appointment.token_number == token_id)
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Token/Appointment not found")

    appt.status = "Skipped"
    appt.notes = f"Skipped: {payload.reason}"

    session = _get_session(appt.doctor_id, appt.hospital_id)
    if session.get("currentActiveTokenId") == appt.id:
        session["currentActiveTokenId"] = None

    await db.commit()
    await db.refresh(appt)

    return {
        "success": True,
        "message": f"Patient skipped for Token #{appt.token_number}",
        "tokenId": appt.id,
        "tokenNumber": appt.token_number,
        "status": appt.status,
    }


@router.post("/tokens/{token_id}/no-show")
async def mark_no_show(
    token_id: str,
    payload: QueueSkipRequest = QueueSkipRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Marks patient as No-show."""
    stmt = select(Appointment).where(
        or_(Appointment.id == token_id, Appointment.token_number == token_id)
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Token/Appointment not found")

    appt.status = "No-show"
    appt.notes = f"No-show: {payload.reason}"

    session = _get_session(appt.doctor_id, appt.hospital_id)
    if session.get("currentActiveTokenId") == appt.id:
        session["currentActiveTokenId"] = None

    await db.commit()
    await db.refresh(appt)

    return {
        "success": True,
        "message": f"Patient marked as No-show for Token #{appt.token_number}",
        "tokenId": appt.id,
        "tokenNumber": appt.token_number,
        "status": appt.status,
    }


@router.post("/tokens/{token_id}/emergency")
async def bump_emergency_patient(
    token_id: str,
    payload: QueueEmergencyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Bumps emergency patient to front of waiting queue with mandatory medical reason."""
    stmt = select(Appointment).where(
        or_(Appointment.id == token_id, Appointment.token_number == token_id)
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Token/Appointment not found")

    if hasattr(appt, "is_emergency"):
        appt.is_emergency = True
        appt.emergency_reason = payload.reason
    appt.notes = f"EMERGENCY OVERRIDE: {payload.reason}"
    appt.patients_ahead = 0
    appt.estimated_wait_minutes = 0

    await db.commit()
    await db.refresh(appt)

    return {
        "success": True,
        "message": f"Emergency priority granted for Token #{appt.token_number}",
        "tokenId": appt.id,
        "tokenNumber": appt.token_number,
        "isEmergency": True,
        "reason": payload.reason,
    }


@router.post("/walk-in")
async def add_walk_in_patient(
    payload: QueueWalkInRequest,
    db: AsyncSession = Depends(get_db),
):
    """Receptionist: Issues instant walk-in token directly at hospital counter."""
    # Find doctor & hospital
    doc_stmt = select(Doctor).where(Doctor.id == payload.doctor_id)
    doc_res = await db.execute(doc_stmt)
    doctor = doc_res.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    hosp_stmt = select(Hospital).where(Hospital.id == payload.hospital_id)
    hosp_res = await db.execute(hosp_stmt)
    hospital = hosp_res.scalar_one_or_none()
    hosp_name = hospital.name if hospital else "Hospital OPD"

    # Find or create patient
    pat_stmt = select(Patient).where(Patient.phone == payload.patient_phone)
    pat_res = await db.execute(pat_stmt)
    patient = pat_res.scalar_one_or_none()

    if not patient:
        pat_id = f"pat_{uuid.uuid4().hex[:8]}"
        patient = Patient(
            id=pat_id,
            uhid=f"PT-{uuid.uuid4().int % 90000 + 10000}",
            name=payload.patient_name,
            phone=payload.patient_phone,
            gender=payload.gender or "Other",
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)

    # Count today's walk-ins
    today = date.today()
    count_stmt = (
        select(Appointment)
        .where(
            Appointment.doctor_id == payload.doctor_id,
            Appointment.appointment_date == today,
        )
    )
    count_res = await db.execute(count_stmt)
    existing = len(count_res.scalars().all())

    token_number = f"W-{existing + 1:02d}"
    appt_id = f"APT-W-{uuid.uuid4().int % 90000 + 10000}"

    appt = Appointment(
        id=appt_id,
        patient_id=patient.id,
        patient_name=payload.patient_name,
        doctor_id=payload.doctor_id,
        doctor_name=doctor.name,
        doctor_specialization=doctor.specialization,
        department=doctor.department,
        hospital_id=payload.hospital_id,
        hospital_name=hosp_name,
        appointment_date=today,
        time_slot="Walk-in OPD",
        status="Checked-in",
        token_number=token_number,
        now_serving_token="A-01",
        patients_ahead=existing,
        estimated_wait_minutes=existing * 10 + 10,
        room_number=doctor.room_number or "OPD 101",
        notes="Counter Walk-in Registration",
        is_walk_in=True,
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)

    return {
        "success": True,
        "message": f"Walk-in token {token_number} issued for {payload.patient_name}",
        "tokenId": appt.id,
        "tokenNumber": token_number,
        "patientId": patient.id,
        "patientName": payload.patient_name,
        "status": appt.status,
    }


@router.post("/session/pause")
async def pause_queue_session(payload: QueuePauseRequest):
    """Doctor Pause Queue (Break / Emergency)."""
    session = _get_session(payload.doctor_id, payload.hospital_id)
    session["isPaused"] = True
    session["pauseReason"] = payload.reason
    return {
        "success": True,
        "message": f"Queue paused: {payload.reason}",
        "session": session,
    }


@router.post("/session/resume")
async def resume_queue_session(payload: QueueResumeRequest):
    """Doctor Resume Queue."""
    session = _get_session(payload.doctor_id, payload.hospital_id)
    session["isPaused"] = False
    session["pauseReason"] = None
    return {
        "success": True,
        "message": "Queue resumed",
        "session": session,
    }


@router.post("/session/delay")
async def set_queue_delay(payload: QueueDelayRequest):
    """Doctor reported running late by X minutes; adjusts estimated wait times."""
    session = _get_session(payload.doctor_id, payload.hospital_id)
    session["delayMinutes"] = payload.delay_minutes
    return {
        "success": True,
        "message": f"Doctor delay set to {payload.delay_minutes} minutes",
        "session": session,
    }
