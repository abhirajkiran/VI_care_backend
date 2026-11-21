from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.billing_pharmacy import (
    BillPaymentRequest,
    BillSchema,
    PharmacyItemSchema,
)

router = APIRouter()

_INVOICES: List[Dict[str, Any]] = [
    {
        "id": "INV-2026-001",
        "invoiceNumber": "INV-2026-001",
        "patientId": "patient_01",
        "patientName": "Aravind Krishnan",
        "date": datetime.now(timezone.utc).isoformat(),
        "services": [
            {"description": "Specialist OPD Cardiology Consultation", "amount": 800.0},
            {"description": "12-Lead Electrocardiogram (ECG)", "amount": 450.0},
            {"description": "Digital Hospital Registration & EMR Archival", "amount": 150.0},
        ],
        "subtotal": 1400.0,
        "insuranceCovered": 400.0,
        "paidAmount": 1000.0,
        "balance": 0.0,
        "status": "paid",
        "hospitalId": "hosp_01",
        "hospitalName": "Vicare Apollo City Hospital",
    },
    {
        "id": "INV-2026-002",
        "invoiceNumber": "INV-2026-002",
        "patientId": "patient_01",
        "patientName": "Aravind Krishnan",
        "date": datetime.now(timezone.utc).isoformat(),
        "services": [
            {"description": "Comprehensive Lipid Profile Panel", "amount": 800.0},
            {"description": "Blood Sample Phlebotomy & Consumables", "amount": 100.0},
        ],
        "subtotal": 900.0,
        "insuranceCovered": 0.0,
        "paidAmount": 0.0,
        "balance": 900.0,
        "status": "pending",
        "hospitalId": "hosp_01",
        "hospitalName": "Vicare Apollo City Hospital",
    },
]

_MEDICINES: List[Dict[str, Any]] = [
    {
        "id": "MED-001",
        "name": "Telmisartan 40mg",
        "genericName": "Telmisartan",
        "category": "Cardiac",
        "stockQuantity": 240,
        "unit": "Tablets",
        "unitPrice": 14.5,
        "expiryDate": "2027-08-31T00:00:00Z",
        "minAlertLevel": 30,
    },
    {
        "id": "MED-002",
        "name": "Atorvastatin 10mg",
        "genericName": "Atorvastatin Calcium",
        "category": "Cardiac",
        "stockQuantity": 180,
        "unit": "Tablets",
        "unitPrice": 18.0,
        "expiryDate": "2027-11-30T00:00:00Z",
        "minAlertLevel": 30,
    },
    {
        "id": "MED-003",
        "name": "Paracetamol 650mg",
        "genericName": "Acetaminophen",
        "category": "Analgesics",
        "stockQuantity": 500,
        "unit": "Tablets",
        "unitPrice": 3.2,
        "expiryDate": "2028-05-31T00:00:00Z",
        "minAlertLevel": 50,
    },
    {
        "id": "MED-004",
        "name": "Amoxicillin 500mg",
        "genericName": "Amoxicillin Trihydrate",
        "category": "Antibiotics",
        "stockQuantity": 120,
        "unit": "Capsules",
        "unitPrice": 12.0,
        "expiryDate": "2027-03-31T00:00:00Z",
        "minAlertLevel": 25,
    },
]


# =========================================================================
# BILLING & INVOICES
# =========================================================================

@router.get("/billing/invoices", response_model=List[BillSchema])
@router.get("/invoices", response_model=List[BillSchema])
async def get_invoices(patientId: Optional[str] = Query(None)):
    """Returns patient invoices and receipts."""
    if patientId:
        return [BillSchema(**inv) for inv in _INVOICES if inv["patientId"] == patientId]
    return [BillSchema(**inv) for inv in _INVOICES]


@router.post("/billing/pay")
@router.post("/invoices/{invoice_id}/payment")
async def pay_invoice(
    payload: BillPaymentRequest,
    invoice_id: Optional[str] = None,
):
    """Processes simulated digital bill payment (UPI, NetBanking, Card)."""
    target_id = invoice_id or payload.bill_id
    inv = next((i for i in _INVOICES if i["id"] == target_id or i["invoiceNumber"] == target_id), None)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    new_paid = inv["paidAmount"] + payload.amount
    inv["paidAmount"] = new_paid
    inv["balance"] = max(0.0, inv["subtotal"] - inv["insuranceCovered"] - new_paid)
    inv["status"] = "paid" if inv["balance"] == 0 else "partiallyPaid"

    return {
        "success": True,
        "message": f"Payment of ₹{payload.amount} processed successfully via {payload.payment_method}",
        "transactionId": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "invoice": inv,
    }


# =========================================================================
# PHARMACY INVENTORY & DISPENSING
# =========================================================================

@router.get("/pharmacy/inventory", response_model=List[PharmacyItemSchema])
@router.get("/medicines", response_model=List[PharmacyItemSchema])
async def get_pharmacy_inventory(query: Optional[str] = Query(None)):
    """Returns pharmacy medicine catalog and stock availability."""
    meds = _MEDICINES
    if query:
        q = query.lower().strip()
        meds = [m for m in meds if q in m["name"].lower() or q in m["genericName"].lower()]
    return [PharmacyItemSchema(**m) for m in meds]


@router.post("/medicines", response_model=PharmacyItemSchema)
@router.post("/pharmacy/inventory", response_model=PharmacyItemSchema)
async def create_medicine(item: dict):
    """Adds a new medicine to pharmacy catalog."""
    new_id = item.get("id") or f"MED-{uuid.uuid4().hex[:6].upper()}"
    med = {
        "id": new_id,
        "name": item.get("name", "New Medicine"),
        "genericName": item.get("genericName", item.get("name", "")),
        "category": item.get("category", "General"),
        "stockQuantity": int(item.get("stockQuantity", item.get("quantity", 100))),
        "unit": item.get("unit", "Tablets"),
        "unitPrice": float(item.get("unitPrice", item.get("price", 10.0))),
        "expiryDate": item.get("expiryDate", datetime.utcnow() + timedelta(days=365)),
        "minAlertLevel": int(item.get("minAlertLevel", 20)),
    }
    _MEDICINES.append(med)
    return PharmacyItemSchema(**med)


@router.patch("/medicines/{medicine_id}/stock", response_model=PharmacyItemSchema)
async def update_medicine_stock(medicine_id: str, payload: dict):
    """Updates stock quantity for a medicine."""
    for m in _MEDICINES:
        if m["id"] == medicine_id:
            if "quantity" in payload:
                m["stockQuantity"] = int(payload["quantity"])
            elif "stockQuantity" in payload:
                m["stockQuantity"] = int(payload["stockQuantity"])
            return PharmacyItemSchema(**m)
    raise HTTPException(status_code=404, detail=f"Medicine {medicine_id} not found")


@router.post("/pharmacy/dispense")
async def dispense_pharmacy_prescription(payload: dict):
    """Dispenses prescription from pharmacy inventory."""
    prescription_id = payload.get("prescriptionId") or payload.get("id")
    return {
        "success": True,
        "message": f"Prescription {prescription_id} dispensed successfully",
        "dispensedAt": datetime.utcnow().isoformat(),
        "status": "Dispensed",
    }


@router.get("/pharmacy/prescriptions")
async def get_pharmacy_prescriptions(patientId: Optional[str] = Query(None)):
    """Returns pharmacy dispensing queue for patient prescriptions."""
    from app.api.v1.endpoints.clinical import _PRESCRIPTIONS

    prescriptions = _PRESCRIPTIONS
    if patientId:
        prescriptions = [p for p in prescriptions if p.get("patientId") == patientId]

    return prescriptions
