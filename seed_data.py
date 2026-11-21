import asyncio
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, AsyncSessionLocal, async_engine
from app.models.hospital import Hospital, HospitalService
from app.models.doctor import Doctor
from app.models.patient import Patient, FamilyMember
from app.models.appointment import Appointment
from app.models.notification import Notification


async def seed_database():
    print("🌱 Connecting to database and creating tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("🏥 Seeding Hospitals...")
        hospitals_data = [
            Hospital(
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
                about="Accredited multi-specialty tertiary care hospital with 450 beds and robotic surgery.",
                departments=["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Oncology", "General Medicine"],
                branches=["Main Campus - Marine Drive", "North Diagnostic Wing"],
                department_count=18,
                rating=4.9,
                review_count=380,
            ),
            Hospital(
                id="hosp_02",
                name="Vicare Aster Medcity",
                logo_url="assets/images/logo.png",
                address="Cheranalloor Road, South Enclave",
                city="Kochi",
                latitude=10.0450,
                longitude=76.2800,
                is_open_now=True,
                working_hours="Open 24/7 • Multi-Organ Transplant Center",
                phone="+91 484 669 9999",
                emergency_phone="+91 484 669 9108",
                email="aster@vicare-network.org",
                about="World-class quaternary healthcare destination featuring dedicated centers of excellence.",
                departments=["Cardiology", "Neurology", "Orthopedics", "Pediatrics", "General Medicine", "ENT"],
                branches=["Waterfront Campus", "East Express Clinic"],
                department_count=24,
                rating=4.8,
                review_count=512,
            ),
            Hospital(
                id="hosp_03",
                name="Vicare Sunrise Specialty Center",
                logo_url="assets/images/logo.png",
                address="Seaport-Airport Road, Kakkanad InfoPark",
                city="Kochi",
                latitude=10.0120,
                longitude=76.3500,
                is_open_now=True,
                working_hours="Mon - Sun: 07:00 AM - 10:00 PM",
                phone="+91 484 414 4444",
                emergency_phone="+91 484 414 4100",
                email="sunrise@vicare-network.org",
                about="Specialized surgical and laparoscopic center providing fast-track outpatient clinics.",
                departments=["Cardiology", "General Medicine", "Gynecology", "Pediatrics", "Dermatology"],
                branches=["TechZone Campus"],
                department_count=12,
                rating=4.7,
                review_count=198,
            ),
        ]
        for h in hospitals_data:
            await session.merge(h)

        print("🩺 Seeding Doctors...")
        doctors_data = [
            Doctor(
                id="doc_01",
                hospital_id="hosp_01",
                name="Dr. Sreelatha Menon",
                specialization="Senior Cardiologist",
                qualifications="MBBS, MD, DM (Cardiology), FACC",
                experience_years=16,
                department="Cardiology",
                languages=["English", "Malayalam", "Hindi"],
                consultation_fee=750.0,
                hospital_location="Cardio OPD Block A, Room 204",
                available_schedule="Mon - Sat (09:00 AM - 02:00 PM)",
                available_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                rating=4.9,
                review_count=310,
                next_available_slot="Today • 04:30 PM",
            ),
            Doctor(
                id="doc_02",
                hospital_id="hosp_01",
                name="Dr. Anand Ramanathan",
                specialization="Neurologist & Stroke Specialist",
                qualifications="MBBS, MD (Medicine), DM (Neurology)",
                experience_years=12,
                department="Neurology",
                languages=["English", "Tamil", "Hindi"],
                consultation_fee=800.0,
                hospital_location="Neurosciences OPD, Room 108",
                available_schedule="Mon - Fri (10:00 AM - 04:00 PM)",
                available_days=["Mon", "Tue", "Wed", "Thu", "Fri"],
                rating=4.8,
                review_count=195,
                next_available_slot="Today • 05:00 PM",
            ),
            Doctor(
                id="doc_03",
                hospital_id="hosp_02",
                name="Dr. Sarah Thomas",
                specialization="Pediatric Specialist",
                qualifications="MBBS, DCH, DNB (Pediatrics)",
                experience_years=9,
                department="Pediatrics",
                languages=["English", "Malayalam"],
                consultation_fee=600.0,
                hospital_location="Child Health Wing, Room 12",
                available_schedule="Mon - Sat (08:30 AM - 01:30 PM)",
                available_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                rating=4.9,
                review_count=240,
                next_available_slot="Today • 03:00 PM",
            ),
            Doctor(
                id="doc_04",
                hospital_id="hosp_03",
                name="Dr. Rajesh Nambiar",
                specialization="Orthopedic Surgeon",
                qualifications="MBBS, MS (Orthopedics), MCh (Ortho)",
                experience_years=18,
                department="Orthopedics",
                languages=["English", "Malayalam"],
                consultation_fee=700.0,
                hospital_location="Joint & Spine Wing, Room 301",
                available_schedule="Tue - Sat (11:00 AM - 05:00 PM)",
                available_days=["Tue", "Wed", "Thu", "Fri", "Sat"],
                rating=4.7,
                review_count=180,
                next_available_slot="Tomorrow • 10:00 AM",
            ),
        ]
        for d in doctors_data:
            await session.merge(d)

        print("👤 Seeding Patient Profile...")
        patient = Patient(
            id="patient_01",
            uhid="PT-10284",
            name="Aravind Krishnan",
            date_of_birth=date(1992, 5, 14),
            gender="Male",
            blood_group="B+",
            phone="+91 98765 43210",
            email="aravind.krishnan@example.com",
            address="TC 42/1481, Pattom, Thiruvananthapuram, Kerala 695004",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            emergency_contact_name="Kavitha Krishnan",
            emergency_contact_phone="+91 98765 99887",
            emergency_contact_relation="Spouse",
            allergies=["Penicillin", "Peanuts", "Sulfa drugs"],
            chronic_conditions=["Mild Hypertension", "Type-2 Diabetes (Pre-diabetic)"],
        )
        await session.merge(patient)

        # Family member
        fam = FamilyMember(
            id="fam_01",
            patient_id="patient_01",
            name="Ramachandran Krishnan",
            relation="Father",
            uhid="PT-08912",
            age="64",
            gender="Male",
        )
        await session.merge(fam)

        print("🔔 Seeding Notifications...")
        notif = Notification(
            id="notif_01",
            patient_id="patient_01",
            title="Appointment Reminder",
            body="Reminder: Cardiology consultation with Dr. Sreelatha Menon today at 10:30 AM.",
            is_read=False,
            category="reminder",
        )
        await session.merge(notif)

        await session.commit()
        print("✅ Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
