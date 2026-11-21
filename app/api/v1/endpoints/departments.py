from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.hospital import Hospital
from app.schemas.department import DepartmentResponse

router = APIRouter()

STANDARD_DEPARTMENTS = [
    {
        "id": "dept_cardio",
        "name": "Cardiology",
        "code": "CARD",
        "head_doctor": "Dr. Sreelatha Menon",
        "doctors_count": 6,
        "staff_count": 18,
        "total_beds": 45,
        "available_beds": 12,
        "active_appointments": 14,
        "description": "Comprehensive cardiac diagnostics, cath lab, and cardiovascular intensive care.",
    },
    {
        "id": "dept_neuro",
        "name": "Neurology",
        "code": "NEUR",
        "head_doctor": "Dr. Anand Rajan",
        "doctors_count": 5,
        "staff_count": 15,
        "total_beds": 35,
        "available_beds": 8,
        "active_appointments": 10,
        "description": "Advanced stroke management, neuro-trauma, and neurophysiology.",
    },
    {
        "id": "dept_ortho",
        "name": "Orthopedics",
        "code": "ORTH",
        "head_doctor": "Dr. George Mathew",
        "doctors_count": 7,
        "staff_count": 20,
        "total_beds": 50,
        "available_beds": 15,
        "active_appointments": 18,
        "description": "Robotic joint replacement, spine surgery, and musculoskeletal rehabilitation.",
    },
    {
        "id": "dept_pedia",
        "name": "Pediatrics",
        "code": "PED",
        "head_doctor": "Dr. Deepa Pillai",
        "doctors_count": 6,
        "staff_count": 22,
        "total_beds": 40,
        "available_beds": 10,
        "active_appointments": 12,
        "description": "Neonatal intensive care (NICU), pediatric critical care, and developmental wellness.",
    },
    {
        "id": "dept_genmed",
        "name": "General Medicine",
        "code": "GENM",
        "head_doctor": "Dr. Thomas Joseph",
        "doctors_count": 8,
        "staff_count": 24,
        "total_beds": 60,
        "available_beds": 18,
        "active_appointments": 25,
        "description": "Adult primary care, fever clinic, internal medicine, and chronic disease management.",
    },
    {
        "id": "dept_onco",
        "name": "Oncology",
        "code": "ONC",
        "head_doctor": "Dr. K. N. Haridas",
        "doctors_count": 4,
        "staff_count": 14,
        "total_beds": 30,
        "available_beds": 6,
        "active_appointments": 8,
        "description": "Medical, surgical, and radiation oncology with day-care chemotherapy suites.",
    },
]


@router.get("", response_model=List[DepartmentResponse])
async def get_departments(
    hospitalId: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Returns all medical departments (for Web Portal staff management and filtering)."""
    if hospitalId:
        stmt = select(Hospital).where(Hospital.id == hospitalId)
        result = await db.execute(stmt)
        hosp = result.scalar_one_or_none()
        if hosp and hosp.departments:
            # Map hospital-specific departments
            mapped = []
            for d_name in hosp.departments:
                matched = next(
                    (s for s in STANDARD_DEPARTMENTS if s["name"].lower() == d_name.lower()),
                    None,
                )
                if matched:
                    item = dict(matched)
                    item["hospital_id"] = hospitalId
                    mapped.append(DepartmentResponse(**item))
                else:
                    mapped.append(
                        DepartmentResponse(
                            id=f"dept_{d_name.lower().replace(' ', '_')}",
                            hospital_id=hospitalId,
                            name=d_name,
                            code=d_name[:4].upper(),
                            description=f"{d_name} medical department",
                        )
                    )
            return mapped

    return [DepartmentResponse(**d) for d in STANDARD_DEPARTMENTS]


@router.get("/names", response_model=List[str])
async def get_department_names():
    """Returns simple list of department names for mobile app dropdowns."""
    return ["All"] + [d["name"] for d in STANDARD_DEPARTMENTS]
