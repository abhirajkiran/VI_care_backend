import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.hospital import Hospital, HospitalService
from app.schemas.hospital import (
    HospitalListResponse,
    HospitalResponse,
    HospitalServiceResponse,
)
from app.services.distance_service import calculate_haversine_distance

router = APIRouter()


@router.get("", response_model=List[HospitalResponse])
async def get_hospitals(db: AsyncSession = Depends(get_db)):
    """Returns all hospitals in the network (for Web Portal & directory)."""
    stmt = select(Hospital).order_by(Hospital.name)
    result = await db.execute(stmt)
    hospitals = result.scalars().all()
    return [HospitalResponse.model_validate(h) for h in hospitals]


@router.get("/active", response_model=HospitalResponse)
async def get_active_hospital(db: AsyncSession = Depends(get_db)):
    """Returns currently active hospital tenant for Web Admin portal."""
    stmt = select(Hospital).where(Hospital.is_active == True).limit(1)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        # Fallback to any hospital
        stmt = select(Hospital).limit(1)
        result = await db.execute(stmt)
        hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="No hospital found")
    return HospitalResponse.model_validate(hospital)


@router.post("/switch/{hospital_id}")
async def switch_active_hospital(hospital_id: str, db: AsyncSession = Depends(get_db)):
    """Switches active hospital session in Web Portal."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return {
        "success": True,
        "activeHospitalId": hospital.id,
        "name": hospital.name,
    }


@router.post("/{hospital_id}/toggle-status")
async def toggle_hospital_status(hospital_id: str, db: AsyncSession = Depends(get_db)):
    """Toggles active/inactive status of a hospital."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    hospital.is_active = not hospital.is_active
    await db.commit()
    await db.refresh(hospital)
    return {"id": hospital.id, "isActive": hospital.is_active}


@router.post("", response_model=HospitalResponse)
async def create_hospital(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Super Admin console: Registers a new hospital tenant."""
    hosp_id = payload.get("id") or f"hosp_{uuid.uuid4().hex[:6]}"
    hospital = Hospital(
        id=hosp_id,
        name=payload.get("name", "New Hospital Branch"),
        address=payload.get("address", "Hospital Address"),
        city=payload.get("city", "Kochi"),
        latitude=float(payload.get("latitude") or 9.9816),
        longitude=float(payload.get("longitude") or 76.2999),
        phone=payload.get("phone", "+91 484 200 0000"),
        emergency_phone=payload.get("emergencyPhone") or payload.get("emergency_phone") or "+91 484 200 1111",
        email=payload.get("email", "contact@hospital.org"),
        about=payload.get("tagline") or payload.get("about", "Multi-specialty healthcare center."),
        departments=payload.get("departments", ["Cardiology", "General Medicine"]),
        branches=[payload.get("name", "Main Branch")],
        department_count=len(payload.get("departments", ["Cardiology", "General Medicine"])),
        rating=4.8,
        review_count=120,
        is_active=True,
    )
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)
    return HospitalResponse.model_validate(hospital)


@router.patch("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(
    hospital_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Super Admin console: Updates hospital branch details."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    for k, v in payload.items():
        if hasattr(hospital, k) and v is not None:
            setattr(hospital, k, v)

    await db.commit()
    await db.refresh(hospital)
    return HospitalResponse.model_validate(hospital)


@router.get("/nearby", response_model=HospitalListResponse)
async def get_nearby_hospitals(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radiusKm: Optional[int] = Query(None),
    query: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Returns nearby hospitals sorted by distance with optional radius and name filtering."""
    stmt = select(Hospital).where(Hospital.is_active == True)
    result = await db.execute(stmt)
    hospitals = result.scalars().all()

    # Default to user coordinates or hospital 01 location (Kochi: 9.9816, 76.2999)
    user_lat = latitude if latitude is not None else 9.9816
    user_lon = longitude if longitude is not None else 76.2999

    hospital_list: List[HospitalResponse] = []
    for h in hospitals:
        dist = calculate_haversine_distance(user_lat, user_lon, h.latitude, h.longitude)
        if radiusKm is not None and dist > radiusKm:
            continue

        if query:
            q = query.lower().strip()
            matches_name = q in h.name.lower()
            matches_city = q in h.city.lower()
            matches_addr = q in h.address.lower()
            matches_dept = any(q in d.lower() for d in (h.departments or []))
            if not (matches_name or matches_city or matches_addr or matches_dept):
                continue

        resp = HospitalResponse.model_validate(h)
        resp.distance_km = dist
        hospital_list.append(resp)

    # Sort by distance
    hospital_list.sort(key=lambda x: x.distance_km)

    return HospitalListResponse(
        hospitals=hospital_list,
        total=len(hospital_list),
    )


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital_by_id(hospital_id: str, db: AsyncSession = Depends(get_db)):
    """Returns detailed hospital information."""
    stmt = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return HospitalResponse.model_validate(hospital)


@router.get("/{hospital_id}/departments", response_model=List[str])
async def get_hospital_departments(hospital_id: str, db: AsyncSession = Depends(get_db)):
    """Returns list of active departments for a hospital."""
    stmt = select(Hospital.departments).where(Hospital.id == hospital_id)
    result = await db.execute(stmt)
    depts = result.scalar_one_or_none()
    return depts or []


@router.get("/{hospital_id}/services", response_model=List[HospitalServiceResponse])
async def get_hospital_services(hospital_id: str, db: AsyncSession = Depends(get_db)):
    """Returns medical and diagnostic services for a hospital."""
    stmt = select(HospitalService).where(HospitalService.hospital_id == hospital_id)
    result = await db.execute(stmt)
    services = result.scalars().all()
    return [HospitalServiceResponse.model_validate(s) for s in services]
