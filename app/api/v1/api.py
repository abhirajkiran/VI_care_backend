from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin,
    appointments,
    auth,
    billing_pharmacy,
    clinical,
    departments,
    doctors,
    hospitals,
    notifications,
    patients,
    queue,
    search,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(hospitals.router, prefix="/hospitals", tags=["Hospitals & Departments"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctors & Schedules"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments & Tokens"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(queue.router, prefix="/queue", tags=["Queue Engine"])
api_router.include_router(clinical.router, tags=["Clinical & EMR"])
api_router.include_router(billing_pharmacy.router, tags=["Billing & Pharmacy"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patient Profiles"])
api_router.include_router(admin.router, tags=["Administration & Staff"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(search.router, prefix="/search", tags=["Global Search"])
