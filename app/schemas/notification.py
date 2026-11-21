from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    id: str
    patient_id: str = Field(alias="patientId")
    title: str
    body: str
    is_read: bool = Field(alias="isRead")
    category: str
    action_route: Optional[str] = Field(default=None, alias="actionRoute")
    related_id: Optional[str] = Field(default=None, alias="relatedId")
    created_at: datetime = Field(alias="timestamp")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
