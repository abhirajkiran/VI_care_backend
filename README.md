# Vicare Healthcare — Multi-Hospital Python FastAPI Backend

Production-ready async REST API built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0 (Async)**, and **Redis** for the **Vicare Hospital Mobile App**.

---

## 🚀 Quick Start (Docker Compose - Recommended)

The easiest way to start the FastAPI server, PostgreSQL database, and Redis is using Docker:

```bash
cd /Users/mac1/Desktop/hospital_backend

# 1. Start all services in the background
docker compose up -d

# 2. Seed mock hospitals, doctors, and patient data
docker compose exec web python seed_data.py
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Local Development Setup (Without Docker)

### 1. Prerequisites
- Python 3.11+
- PostgreSQL running locally on port 5432
- Redis running locally on port 6379

### 2. Setup Virtual Environment
```bash
cd /Users/mac1/Desktop/hospital_backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Database
Copy environment settings:
```bash
cp .env.example .env
```
Ensure PostgreSQL database `vicare_db` exists:
```bash
psql -U postgres -c "CREATE DATABASE vicare_db;"
psql -U postgres -c "CREATE USER vicare_user WITH PASSWORD 'vicare_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE vicare_db TO vicare_user;"
```

### 4. Seed Data & Run Server
```bash
# Seed initial hospitals, doctors & patient
python seed_data.py

# Start Uvicorn live server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📱 Connecting the Flutter Mobile App

Open `lib/core/constants/app_constants.dart` in your Flutter project:

```dart
// 1. Set backend base URL:
// For Android Emulator:
static const String apiBaseUrl = 'http://10.0.2.2:8000/api/v1';

// For iOS Simulator / macOS desktop / Physical device on Wi-Fi:
// static const String apiBaseUrl = 'http://localhost:8000/api/v1';
// static const String apiBaseUrl = 'http://192.168.1.X:8000/api/v1';

// 2. Disable Mock Mode
static const bool useMockBackend = false;
```

---

## 📂 Project Architecture

```text
hospital_backend/
├── app/
│   ├── main.py                     # FastAPI app factory, CORS, routes
│   ├── core/
│   │   ├── config.py               # Pydantic Settings & environment
│   │   ├── database.py             # Async SQLAlchemy engine & session
│   │   ├── security.py             # JWT token encode/decode & bcrypt
│   │   └── redis.py                # Async Redis connection pool
│   ├── models/                     # SQLAlchemy Database Entities
│   │   ├── hospital.py             # Hospitals & Services
│   │   ├── doctor.py               # Doctors & Schedules
│   │   ├── patient.py              # Patients & Dependents
│   │   ├── appointment.py          # Visits & Queue
│   │   └── notification.py         # Patient alerts
│   ├── schemas/                    # Pydantic v2 JSON serializers
│   │   ├── auth.py
│   │   ├── hospital.py
│   │   ├── doctor.py
│   │   ├── patient.py
│   │   └── appointment.py
│   ├── api/v1/endpoints/           # REST Route Handlers
│   │   ├── auth.py                 # OTP send/verify, JWT issuance
│   │   ├── hospitals.py            # Nearby hospitals (Haversine sort)
│   │   ├── doctors.py              # Doctor search & slots
│   │   ├── appointments.py         # Booking & atomic token queue
│   │   ├── patients.py             # Patient profile (/me) & family
│   │   ├── notifications.py        # Notification stream
│   │   └── search.py               # Global multi-criteria search
│   └── services/                   # Core Business Logic
│       ├── distance_service.py     # Haversine distance calculations
│       ├── token_service.py        # Redis atomic token sequencing (e.g. A-14)
│       └── auth_service.py         # OTP generation & validation
├── seed_data.py                    # Initial database populator
├── Dockerfile                      # Production container image
├── docker-compose.yml              # Multi-container stack (App + Postgres + Redis)
└── requirements.txt
```
