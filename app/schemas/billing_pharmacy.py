from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BillServiceItemSchema(BaseModel):
    description: str
    amount: float

    model_config = ConfigDict(populate_by_name=True)


class BillSchema(BaseModel):
    id: str
    invoice_number: str = Field(alias="invoiceNumber")
    patient_id: str = Field(alias="patientId")
    patient_name: str = Field(alias="patientName")
    date: datetime = Field(default_factory=datetime.utcnow)
    services: List[BillServiceItemSchema] = []
    subtotal: float
    insurance_covered: float = Field(default=0.0, alias="insuranceCovered")
    paid_amount: float = Field(default=0.0, alias="paidAmount")
    balance: float
    status: str = "pending"  # paid, pending, partiallyPaid
    hospital_id: Optional[str] = Field(default="hosp_01", alias="hospitalId")
    hospital_name: Optional[str] = Field(default="Vicare Apollo City Hospital", alias="hospitalName")

    model_config = ConfigDict(populate_by_name=True)


class BillPaymentRequest(BaseModel):
    bill_id: str = Field(alias="billId")
    amount: float
    payment_method: str = Field(default="UPI", alias="paymentMethod")

    model_config = ConfigDict(populate_by_name=True)


class PharmacyItemSchema(BaseModel):
    id: str
    name: str
    generic_name: str = Field(alias="genericName")
    category: str
    stock_quantity: int = Field(alias="stockQuantity")
    unit: str = "Tablets"
    unit_price: float = Field(alias="unitPrice")
    expiry_date: datetime = Field(alias="expiryDate")
    min_alert_level: int = Field(default=30, alias="minAlertLevel")

    model_config = ConfigDict(populate_by_name=True)
