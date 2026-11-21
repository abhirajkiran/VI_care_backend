from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StaffMemberItem(BaseModel):
    id: str
    hospital_id: Optional[str] = Field(default="hosp_01", alias="hospitalId")
    name: str
    role: str
    department: str
    phone: str
    email: str
    joining_date: str = Field(default="2024-01-15", alias="joiningDate")
    shift: str = "Morning"
    status: str = "Active"

    model_config = ConfigDict(populate_by_name=True)


class AuditLogItem(BaseModel):
    id: str
    hospital_id: Optional[str] = Field(default="hosp_01", alias="hospitalId")
    timestamp: str
    action: str
    module: str
    record_id: str = Field(alias="recordId")
    ip_address: str = Field(default="127.0.0.1", alias="ipAddress")
    user_name: Optional[str] = Field(default="System Admin", alias="userName")
    user_role: Optional[str] = Field(default="Admin", alias="userRole")
    details: Optional[str] = ""

    model_config = ConfigDict(populate_by_name=True)
