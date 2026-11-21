import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.patient import FamilyMember, Patient
from app.schemas.patient import (
    FamilyMemberCreate,
    FamilyMemberResponse,
    PatientResponse,
    PatientUpdate,
)

router = APIRouter()


@router.get("", response_model=List[PatientResponse])
async def get_patients(
    query: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Patient directory for Web Portal & Staff search."""
    stmt = select(Patient).options(selectinload(Patient.family_members))
    if query:
        q = f"%{query.strip().lower()}%"
        stmt = stmt.where(
            Patient.name.ilike(q) | Patient.phone.ilike(q) | Patient.uhid.ilike(q)
        )
    result = await db.execute(stmt)
    patients = result.scalars().all()
    return [PatientResponse.model_validate(p) for p in patients]


@router.get("/me", response_model=PatientResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_patient_id: str = Depends(get_current_user_id),
):
    """Returns active patient profile and linked family members."""
    stmt = (
        select(Patient)
        .options(selectinload(Patient.family_members))
        .where(Patient.id == current_patient_id)
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        # Fallback to patient_01 for demo testing if not yet created
        stmt = (
            select(Patient)
            .options(selectinload(Patient.family_members))
            .where(Patient.id == "patient_01")
        )
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient profile not found")

    return PatientResponse.model_validate(patient)


@router.put("/me", response_model=PatientResponse)
async def update_my_profile(
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_patient_id: str = Depends(get_current_user_id),
):
    """Updates active patient profile details (vitals, address, emergency contact, avatar)."""
    stmt = (
        select(Patient)
        .options(selectinload(Patient.family_members))
        .where(Patient.id == current_patient_id)
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        # Check patient_01
        stmt = (
            select(Patient)
            .options(selectinload(Patient.family_members))
            .where(Patient.id == "patient_01")
        )
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient profile not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None and hasattr(patient, field):
            setattr(patient, field, val)

    await db.commit()
    await db.refresh(patient)
    return PatientResponse.model_validate(patient)


@router.get("/family", response_model=List[FamilyMemberResponse])
async def get_family_members(
    db: AsyncSession = Depends(get_db),
    current_patient_id: str = Depends(get_current_user_id),
):
    """Returns list of dependents/family members."""
    stmt = select(FamilyMember).where(FamilyMember.patient_id == current_patient_id)
    result = await db.execute(stmt)
    members = result.scalars().all()
    return [FamilyMemberResponse.model_validate(m) for m in members]


@router.post("/family", response_model=FamilyMemberResponse)
async def add_family_member(
    payload: FamilyMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_patient_id: str = Depends(get_current_user_id),
):
    """Adds dependent family member with generated UHID."""
    member_id = f"fam_{uuid.uuid4().hex[:6]}"
    uhid = payload.uhid or f"FM-{uuid.uuid4().int % 90000 + 10000}"

    member = FamilyMember(
        id=member_id,
        patient_id=current_patient_id,
        name=payload.name,
        relation=payload.relation,
        uhid=uhid,
        age=payload.age,
        gender=payload.gender,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return FamilyMemberResponse.model_validate(member)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_by_id(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns single patient by ID or UHID for Patient Profile page."""
    stmt = (
        select(Patient)
        .options(selectinload(Patient.family_members))
        .where((Patient.id == patient_id) | (Patient.uhid == patient_id))
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.model_validate(patient)


@router.post("", response_model=PatientResponse)
async def create_patient(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new patient into the hospital directory (Reception / Web Portal)."""
    pat_id = payload.get("id") or f"pat_{uuid.uuid4().hex[:8]}"
    uhid = payload.get("uhid") or f"PT-{uuid.uuid4().int % 90000 + 10000}"
    name = payload.get("name") or f"{payload.get('firstName', '')} {payload.get('lastName', '')}".strip() or "New Patient"

    patient = Patient(
        id=pat_id,
        uhid=uhid,
        name=name,
        phone=payload.get("phone", "+91 98765 00000"),
        email=payload.get("email"),
        gender=payload.get("gender", "Not Specified"),
        blood_group=payload.get("bloodGroup") or payload.get("blood_group") or "Unknown",
        address=payload.get("address"),
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return PatientResponse.model_validate(patient)


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Updates patient directory record."""
    stmt = (
        select(Patient)
        .options(selectinload(Patient.family_members))
        .where((Patient.id == patient_id) | (Patient.uhid == patient_id))
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for k, v in payload.items():
        if hasattr(patient, k) and v is not None:
            setattr(patient, k, v)

    await db.commit()
    await db.refresh(patient)
    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Archives / deletes patient record."""
    stmt = select(Patient).where((Patient.id == patient_id) | (Patient.uhid == patient_id))
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    await db.delete(patient)
    await db.commit()
    return {"success": True, "message": f"Patient {patient_id} deleted successfully"}
