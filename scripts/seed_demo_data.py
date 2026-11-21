import asyncio
from datetime import date, datetime
from app.core.database import AsyncSessionLocal
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient
from sqlalchemy import select

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if hospitals exist
        result = await session.execute(select(Hospital))
        existing = result.scalars().first()
        if existing:
            print("Database already has records, skipping seed.")
            return

        print("Seeding initial hospital records...")
        h1 = Hospital(
            id="hosp_01",
            name="Vicare Apollo City Hospital",
            logo_url="assets/images/logo.png",
            address="450 Healthcare Blvd, Medical District",
            city="Kochi",
            latitude=9.9816,
            longitude=76.2999,
            is_open_now=True,
            working_hours="Open 24/7 • Emergency & Critical Care",
            phone="+91 484 280 1000",
            emergency_phone="+91 484 280 1111",
            email="apollo@vicare-network.org",
            about="Accredited multi-specialty tertiary care hospital with 450 beds and 24/7 trauma emergency care.",
            departments=["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "General Medicine"],
            branches=["Main Campus - Marine Drive", "North Diagnostic Wing"],
            department_count=18,
            rating=4.9,
            review_count=1240,
            is_active=True
        )
        session.add(h1)

        print("Seeding doctors...")
        d1 = Doctor(
            id="doc_01",
            hospital_id="hosp_01",
            name="Dr. Sarah Jenkins",
            specialization="Senior Interventional Cardiologist",
            qualifications="MD, DM (Cardiology), FACC",
            experience_years=14,
            department="Cardiology",
            languages=["English", "Hindi"],
            consultation_fee=850.0,
            hospital_location="Cardiac Care OPD, Room 204",
            available_schedule="Mon - Fri (09:00 AM - 02:00 PM)",
            available_days=["Mon", "Tue", "Wed", "Thu", "Fri"],
            rating=4.9,
            review_count=320,
            next_available_slot="Today • 10:30 AM",
            is_active=True
        )
        d2 = Doctor(
            id="doc_02",
            hospital_id="hosp_01",
            name="Dr. Marcus Vance",
            specialization="Neurologist & Stroke Specialist",
            qualifications="MBBS, MD, DM (Neurology)",
            experience_years=11,
            department="Neurology",
            languages=["English"],
            consultation_fee=800.0,
            hospital_location="Neuroscience Center, Room 108",
            available_schedule="Mon - Thu (10:00 AM - 03:00 PM)",
            available_days=["Mon", "Tue", "Wed", "Thu"],
            rating=4.8,
            review_count=215,
            next_available_slot="Today • 11:15 AM",
            is_active=True
        )
        session.add_all([d1, d2])

        print("Seeding default demo patient...")
        p1 = Patient(
            id="patient_01",
            uhid="VIC-PAT-00109",
            name="Rahul Sharma",
            date_of_birth=date(1988, 5, 14),
            gender="Male",
            blood_group="O+",
            phone="+91 98765 43210",
            email="rahul.sharma@example.com",
            address="Flat 4B, Palm Grove Apts, MG Road, Kochi",
            emergency_contact_name="Pooja Sharma",
            emergency_contact_phone="+91 98765 00000",
            emergency_contact_relation="Spouse",
            allergies=["Penicillin"],
            chronic_conditions=["Mild Hypertension"]
        )
        session.add(p1)

        await session.commit()
        print("✅ Demo hospitals, doctors, and patient successfully seeded to Supabase!")

if __name__ == "__main__":
    asyncio.run(seed_data())
