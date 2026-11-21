from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.doctor import Doctor
from app.models.hospital import Hospital, HospitalService
from app.schemas.doctor import DoctorResponse

router = APIRouter()


@router.get("/global")
async def global_search(
    query: str = Query(""),
    hospitalId: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    availableToday: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Universal search across doctors, departments, and hospital services."""
    q = f"%{query.strip().lower()}%" if query else "%"

    # 1. Search Doctors
    doc_stmt = (
        select(Doctor, Hospital.name.label("hosp_name"))
        .join(Hospital, Doctor.hospital_id == Hospital.id)
    )
    if hospitalId:
        doc_stmt = doc_stmt.where(Doctor.hospital_id == hospitalId)
    if department and department != "All":
        doc_stmt = doc_stmt.where(Doctor.department.ilike(department))
    if specialization:
        doc_stmt = doc_stmt.where(Doctor.specialization.ilike(f"%{specialization}%"))
    if query:
        doc_stmt = doc_stmt.where(
            (Doctor.name.ilike(q))
            | (Doctor.specialization.ilike(q))
            | (Doctor.department.ilike(q))
        )

    doc_result = await db.execute(doc_stmt)
    matched_doctors: List[Dict[str, Any]] = []
    for doc, hosp_name in doc_result.all():
        data = DoctorResponse.model_validate(doc).model_dump(by_alias=True)
        data["hospitalName"] = hosp_name
        matched_doctors.append(data)

    # 2. Search Services
    svc_stmt = select(HospitalService, Hospital.name.label("hosp_name")).join(
        Hospital, HospitalService.hospital_id == Hospital.id
    )
    if hospitalId:
        svc_stmt = svc_stmt.where(HospitalService.hospital_id == hospitalId)
    if query:
        svc_stmt = svc_stmt.where(
            (HospitalService.name.ilike(q)) | (HospitalService.category.ilike(q))
        )
    svc_result = await db.execute(svc_stmt)
    matched_services = [
        {
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "price": s.price,
            "hospitalName": h_name,
            "isAvailable": s.is_available,
        }
        for s, h_name in svc_result.all()
    ]

    return {
        "doctors": matched_doctors,
        "services": matched_services,
    }
