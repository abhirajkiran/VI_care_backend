import uuid
from datetime import date
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.models.patient import Patient
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    SendOtpRequest,
    SendOtpResponse,
    TokenResponse,
    VerifyOtpRequest,
)
from app.services.auth_service import send_sms_otp, verify_sms_otp

router = APIRouter()


def _build_user_dict(patient: Patient) -> Dict[str, Any]:
    return {
        "id": patient.id,
        "name": patient.name or "Aravind Krishnan",
        "email": patient.email or f"{patient.phone}@vicare.internal",
        "phone": patient.phone,
        "role": "patient",
        "avatarUrl": patient.avatar_url,
        "uhid": patient.uhid,
        "bloodGroup": patient.blood_group,
        "gender": patient.gender,
    }


@router.post("/send-otp", response_model=SendOtpResponse)
async def send_otp(payload: SendOtpRequest):
    """Sends OTP to patient mobile phone."""
    phone = payload.phone
    otp = await send_sms_otp(phone)
    return SendOtpResponse(
        success=True,
        message=f"OTP sent to {phone}",
        otp_demo=otp,
    )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(payload: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    """Verifies OTP and issues JWT access and refresh tokens."""
    phone = payload.phone
    is_valid = await verify_sms_otp(phone, payload.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Use demo OTP 123456.",
        )

    # Check if patient exists
    stmt = select(Patient).where(or_(Patient.phone == phone, Patient.email == phone))
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    is_new_user = False

    if not patient:
        # Create new patient profile
        is_new_user = True
        patient_id = f"pat_{uuid.uuid4().hex[:8]}"
        uhid = f"PT-{uuid.uuid4().int % 90000 + 10000}"
        patient = Patient(
            id=patient_id,
            uhid=uhid,
            name="Aravind Krishnan",
            phone=phone,
            email=f"{phone}@vicare.internal" if "@" not in phone else phone,
            date_of_birth=date(1995, 1, 1),
            gender="Male",
            blood_group="O+",
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)

    access_token = create_access_token(patient.id)
    refresh_token = create_refresh_token(patient.id)

    return TokenResponse(
        token=access_token,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        is_new_user=is_new_user,
        patient_id=patient.id,
        uhid=patient.uhid,
        user=_build_user_dict(patient),
    )


@router.post("/register", response_model=TokenResponse)
async def register_patient(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Registers a new patient with email/phone/password and returns JWT access tokens."""
    name = (payload.get("name") or "New Patient").strip()
    email = (payload.get("email") or "").strip().lower()
    phone = (payload.get("phone") or f"+91 {uuid.uuid4().int % 9000000000 + 1000000000}").strip()

    # Check if patient exists
    conditions = []
    if email:
        conditions.append(Patient.email == email)
    if phone:
        conditions.append(Patient.phone == phone)

    patient = None
    if conditions:
        stmt = select(Patient).where(or_(*conditions))
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()

    is_new = False
    if not patient:
        is_new = True
        patient_id = f"pat_{uuid.uuid4().hex[:8]}"
        uhid = f"PT-{uuid.uuid4().int % 90000 + 10000}"
        patient = Patient(
            id=patient_id,
            uhid=uhid,
            name=name,
            phone=phone,
            email=email if email else f"{phone}@vicare.internal",
            date_of_birth=date(1995, 1, 1),
            gender="Not Specified",
            blood_group="Unknown",
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
    else:
        if name:
            patient.name = name
        await db.commit()
        await db.refresh(patient)

    access_token = create_access_token(patient.id)
    refresh_token = create_refresh_token(patient.id)

    return TokenResponse(
        token=access_token,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        is_new_user=is_new,
        patient_id=patient.id,
        uhid=patient.uhid,
        user=_build_user_dict(patient),
    )


@router.post("/login", response_model=TokenResponse)
async def login_credentials(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Password/Identifier login for web portal and mobile app."""
    ident = payload.identifier.lower().strip()
    role_hint = (payload.role or "").lower()

    # 1. Doctor login
    if "doctor" in ident or "doctor" in role_hint:
        stmt = select(Doctor)
        res = await db.execute(stmt)
        doc = res.scalars().first()
        doc_id = doc.id if doc else "doc_01"
        doc_name = doc.name if doc else "Dr. Sarah Jenkins"
        doc_dept = doc.department if doc else "Cardiology"
        hosp_id = doc.hospital_id if doc else "hosp_01"

        token = create_access_token(doc_id)
        return TokenResponse(
            token=token,
            access_token=token,
            refresh_token=create_refresh_token(doc_id),
            token_type="bearer",
            is_new_user=False,
            patient_id=doc_id,
            uhid="",
            user={
                "id": doc_id,
                "name": doc_name,
                "email": payload.identifier,
                "role": "Doctor",
                "department": doc_dept,
                "hospitalId": hosp_id,
                "status": "Active",
            },
        )

    # 2. Super Admin login
    if "superadmin" in ident:
        token = create_access_token("usr_super_admin")
        return TokenResponse(
            token=token,
            access_token=token,
            refresh_token=create_refresh_token("usr_super_admin"),
            token_type="bearer",
            is_new_user=False,
            patient_id="usr_super_admin",
            uhid="",
            user={
                "id": "usr_super_admin",
                "name": "System Super Admin",
                "email": payload.identifier,
                "role": "Super Admin",
                "status": "Active",
            },
        )

    # 3. Hospital Admin login
    if "admin" in ident or "admin" in role_hint:
        token = create_access_token("usr_admin_01")
        return TokenResponse(
            token=token,
            access_token=token,
            refresh_token=create_refresh_token("usr_admin_01"),
            token_type="bearer",
            is_new_user=False,
            patient_id="usr_admin_01",
            uhid="",
            user={
                "id": "usr_admin_01",
                "name": "Hospital Administrator",
                "email": payload.identifier,
                "role": "Hospital Admin",
                "hospitalId": "hosp_01",
                "status": "Active",
            },
        )

    # 4. Receptionist login
    if "reception" in ident or "reception" in role_hint:
        token = create_access_token("usr_rec_01")
        return TokenResponse(
            token=token,
            access_token=token,
            refresh_token=create_refresh_token("usr_rec_01"),
            token_type="bearer",
            is_new_user=False,
            patient_id="usr_rec_01",
            uhid="",
            user={
                "id": "usr_rec_01",
                "name": "Front Desk Receptionist",
                "email": payload.identifier,
                "role": "Receptionist",
                "hospitalId": "hosp_01",
                "status": "Active",
            },
        )

    # 5. Patient login (phone or email lookup)
    ident = payload.identifier.strip().lower()
    stmt = select(Patient).where(
        or_(Patient.phone == payload.identifier.strip(), Patient.email.ilike(ident), Patient.uhid.ilike(ident))
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found. Please check your credentials or create a new account.",
        )

    access_token = create_access_token(patient.id)
    refresh_token = create_refresh_token(patient.id)

    return TokenResponse(
        token=access_token,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        is_new_user=False,
        patient_id=patient.id,
        uhid=patient.uhid or "PT-10001",
        user=_build_user_dict(patient),
    )


@router.post("/google", response_model=TokenResponse)
async def google_login(payload: Optional[Dict[str, Any]] = None, db: AsyncSession = Depends(get_db)):
    """Google One-Tap sign in for Mobile App."""
    email = "google.patient@vicare.internal"
    name = "Google User"
    if payload and isinstance(payload, dict):
        email = (payload.get("email") or email).strip().lower()
        name = (payload.get("name") or name).strip()

    stmt = select(Patient).where(Patient.email == email)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        patient_id = f"pat_{uuid.uuid4().hex[:8]}"
        uhid = f"PT-{uuid.uuid4().int % 90000 + 10000}"
        patient = Patient(
            id=patient_id,
            uhid=uhid,
            name=name,
            email=email,
            phone="+91 98765 00000",
            gender="Not Specified",
            blood_group="Unknown",
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)

    access_token = create_access_token(patient.id)
    refresh_token = create_refresh_token(patient.id)

    return TokenResponse(
        token=access_token,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        is_new_user=False,
        patient_id=patient.id,
        uhid=patient.uhid,
        user=_build_user_dict(patient),
    )


@router.post("/logout")
async def logout():
    """Logout endpoint."""
    return {"success": True, "message": "Logged out successfully"}


@router.post("/refresh-token")
async def refresh_access_token(payload: RefreshTokenRequest):
    """Issues new access token from refresh token."""
    from jose import JWTError, jwt
    from app.core.config import settings

    try:
        data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if data.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        patient_id = data.get("sub")
        new_token = create_access_token(patient_id)
        return {
            "token": new_token,
            "access_token": new_token,
            "token_type": "bearer",
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
