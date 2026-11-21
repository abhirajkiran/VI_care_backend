from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator


class SendOtpRequest(BaseModel):
    phone: Optional[str] = None
    phoneOrEmail: Optional[str] = None

    @model_validator(mode="after")
    def validate_identifier(self):
        val = self.phone or self.phoneOrEmail
        if not val:
            raise ValueError("Either phone or phoneOrEmail is required")
        self.phone = val
        return self


class SendOtpResponse(BaseModel):
    success: bool = True
    message: str = "OTP sent successfully"
    otp_demo: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    phone: Optional[str] = None
    phoneOrEmail: Optional[str] = None
    otp: str = Field(..., description="6-digit verification OTP")

    @model_validator(mode="after")
    def validate_identifier(self):
        val = self.phone or self.phoneOrEmail
        if not val:
            raise ValueError("Either phone or phoneOrEmail is required")
        self.phone = val
        return self


class LoginRequest(BaseModel):
    identifier: str
    password: str
    role: Optional[str] = "patient"


class TokenResponse(BaseModel):
    token: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool = False
    patient_id: str
    uhid: str
    user: Optional[Dict[str, Any]] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
