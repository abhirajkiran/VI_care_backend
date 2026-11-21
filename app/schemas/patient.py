from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FamilyMemberBase(BaseModel):
    id: Optional[str] = None
    name: str
    relation: str
    uhid: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class FamilyMemberCreate(FamilyMemberBase):
    pass


class FamilyMemberResponse(FamilyMemberBase):
    id: str
    uhid: str


class PatientBase(BaseModel):
    id: str
    uhid: str
    name: str
    date_of_birth: Optional[date] = Field(default=date(1995, 1, 1), alias="dateOfBirth")
    gender: str = "Not Specified"
    blood_group: str = Field(default="Unknown", alias="bloodGroup")
    phone: str
    email: Optional[str] = ""
    address: Optional[str] = ""
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    emergency_contact_name: Optional[str] = Field(default="", alias="emergencyContactName")
    emergency_contact_phone: Optional[str] = Field(default="", alias="emergencyContactPhone")
    emergency_contact_relation: Optional[str] = Field(default="", alias="emergencyContactRelation")
    allergies: Optional[List[str]] = []
    chronic_conditions: Optional[List[str]] = Field(default=[], alias="chronicConditions")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = Field(default=None, alias="bloodGroup")
    date_of_birth: Optional[date] = Field(default=None, alias="dateOfBirth")
    address: Optional[str] = None
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    emergency_contact_name: Optional[str] = Field(default=None, alias="emergencyContactName")
    emergency_contact_phone: Optional[str] = Field(default=None, alias="emergencyContactPhone")
    emergency_contact_relation: Optional[str] = Field(default=None, alias="emergencyContactRelation")
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = Field(default=None, alias="chronicConditions")

    model_config = ConfigDict(populate_by_name=True)


class PatientResponse(PatientBase):
    family_members: List[FamilyMemberResponse] = Field(default=[], alias="familyMembers")
