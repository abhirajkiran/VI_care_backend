from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HospitalBase(BaseModel):
    id: str
    name: str
    logo_url: str = Field(default="assets/images/logo.png", alias="logoUrl")
    address: str
    city: str
    latitude: float
    longitude: float
    distance_km: float = Field(default=0.0, alias="distanceKm")
    is_open_now: bool = Field(default=True, alias="isOpenNow")
    working_hours: str = Field(default="Open 24/7", alias="workingHours")
    phone: str
    emergency_phone: str = Field(default="", alias="emergencyPhone")
    email: str
    about: Optional[str] = ""
    departments: List[str] = []
    branches: List[str] = []
    department_count: int = Field(default=0, alias="departmentCount")
    rating: float = 4.8
    review_count: int = Field(default=0, alias="reviewCount")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class HospitalResponse(HospitalBase):
    pass


class HospitalListResponse(BaseModel):
    hospitals: List[HospitalResponse]
    total: int


class HospitalServiceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    category: str
    price: Optional[float] = None
    is_available: bool = Field(default=True, alias="isAvailable")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
