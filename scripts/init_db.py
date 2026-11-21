import asyncio
from app.core.database import async_engine, Base
from app.models import Hospital, HospitalService, Doctor, Patient, FamilyMember, Appointment, Notification

async def init_tables():
    print(f"Connecting to database via async engine...")
    async with async_engine.begin() as conn:
        print("Creating all tables in database...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully in Supabase!")

if __name__ == "__main__":
    asyncio.run(init_tables())
