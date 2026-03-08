from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from converter import fhir_to_iso
from validator import validate_identity
from database import engine, SessionLocal
from models import Base, Patient

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(
    filename="audit.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="FHIR to ISO-TS-22220 Identity Converter",
    description="Converts FHIR Patient data into ISO-compliant identity format with validation and duplicate detection",
    version="1.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Reads allowed origins from env var, falls back to known URLs for local dev
_origins_env = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = _origins_env.split(",") if _origins_env else [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "https://iso-ts-22220-2011.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "FHIR Identity Converter API Running"}


# ── Convert FHIR Patient → ISO Identity ───────────────────────────────────────
@app.post("/convert")
def convert_patient(patient: dict):
    db = SessionLocal()
    try:
        # Validate required FHIR fields
        required_fields = ["name", "birthDate", "gender", "identifier"]
        missing = [f for f in required_fields if f not in patient]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required FHIR fields: {', '.join(missing)}"
            )

        # Convert FHIR → ISO
        try:
            iso_data = fhir_to_iso(patient)
        except (KeyError, IndexError) as e:
            raise HTTPException(
                status_code=422,
                detail=f"Malformed FHIR data: {str(e)}"
            )

        # Validate identity fields
        if not validate_identity(iso_data):
            logging.warning("Invalid identity data received")
            raise HTTPException(status_code=400, detail="Invalid identity data")

        # Check duplicate by unique patient ID
        existing = db.query(Patient).filter(
            Patient.unique_patient_id == iso_data["unique_patient_id"]
        ).first()

        if existing:
            logging.warning(f"Duplicate patient ID: {iso_data['unique_patient_id']}")
            return {
                "status": "duplicate",
                "warning": "Duplicate patient ID detected",
                "iso_identity": iso_data
            }

        # Check possible duplicate by name + DOB
        possible_dup = db.query(Patient).filter(
            Patient.full_name == iso_data["full_name"],
            Patient.date_of_birth == iso_data["date_of_birth"]
        ).first()

        if possible_dup:
            logging.warning(
                f"Possible duplicate: {iso_data['full_name']} DOB {iso_data['date_of_birth']}"
            )
            return {
                "status": "possible_duplicate",
                "warning": "Possible duplicate patient detected",
                "existing_patient_id": possible_dup.unique_patient_id,
                "iso_identity": iso_data
            }

        # Save to database
        new_patient = Patient(
            unique_patient_id=iso_data["unique_patient_id"],
            full_name=iso_data["full_name"],
            date_of_birth=iso_data["date_of_birth"],
            gender=iso_data["gender"]
        )
        db.add(new_patient)
        db.commit()

        logging.info(f"Patient stored: {iso_data['unique_patient_id']}")

        return {
            "status": "success",
            "message": "Patient converted and stored successfully",
            "iso_identity": iso_data
        }

    finally:
        db.close()


# ── List all patients ─────────────────────────────────────────────────────────
@app.get("/patients")
def get_patients():
    db = SessionLocal()
    try:
        patients = db.query(Patient).all()
        result = []
        for p in patients:
            name_parts = p.full_name.strip().split(" ", 1)
            result.append({
                "id": p.unique_patient_id,
                "full_name": p.full_name,
                "date_of_birth": p.date_of_birth,
                "gender": p.gender,
                # FHIR-compatible shape for frontend rendering
                "name": [{
                    "use": "official",
                    "given": [name_parts[0]],
                    "family": name_parts[1] if len(name_parts) > 1 else ""
                }],
                "birthDate": p.date_of_birth,
            })
        return result
    finally:
        db.close()


# ── Get specific patient ──────────────────────────────────────────────────────
@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(
            Patient.unique_patient_id == patient_id
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        name_parts = patient.full_name.strip().split(" ", 1)
        return {
            "id": patient.unique_patient_id,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "name": [{
                "use": "official",
                "given": [name_parts[0]],
                "family": name_parts[1] if len(name_parts) > 1 else ""
            }],
            "birthDate": patient.date_of_birth,
        }
    finally:
        db.close()
