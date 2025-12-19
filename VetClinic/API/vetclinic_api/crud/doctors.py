from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets

from vetclinic_api.models.users import Doctor
from vetclinic_api.schemas.users import DoctorCreate, UserUpdate
from vetclinic_api.services.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
        password = pw_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)

def create_doctor(db: Session, doc_in: DoctorCreate) -> tuple[str, Doctor]:
    raw_password = secrets.token_urlsafe(16)
    hashed       = get_password_hash(raw_password)
    doctor = Doctor(
        first_name           = doc_in.first_name,
        last_name            = doc_in.last_name,
        email                = doc_in.email,
        password_hash        = hashed,
        specialization       = doc_in.specialization,
        permit_number        = doc_in.permit_number,
        backup_email         = doc_in.backup_email,
        facility_id          = doc_in.facility_id,       # ← dorzucone
        must_change_password = True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    EmailService.send_temporary_password(doctor.backup_email, raw_password)
    return raw_password, doctor

def list_doctors(db: Session) -> list[Doctor]:
    return db.query(Doctor).all()

def get_doctor(db: Session, doctor_id: int) -> Doctor | None:
    return db.get(Doctor, doctor_id)

def update_doctor(db: Session, doctor_id: int, data_in: UserUpdate) -> Doctor | None:
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return None

    data = data_in.model_dump(exclude_unset=True)

    # hasło
    if "password" in data:
        raw_pw = data.pop("password")
        doctor.password_hash        = get_password_hash(raw_pw)
        doctor.must_change_password = True

    # backup_email, specialization, permit_number
    if "backup_email" in data:
        doctor.backup_email = data["backup_email"]
    if "specialization" in data:
        doctor.specialization = data["specialization"]
    if "permit_number" in data:
        doctor.permit_number = data["permit_number"]

    # nowa kolumna: facility_id
    if "facility_id" in data:
        doctor.facility_id = data["facility_id"]

    # inne pola (first_name, last_name, email)
    for attr in ("first_name", "last_name", "email"):
        if attr in data:
            setattr(doctor, attr, data[attr])

    db.commit()
    db.refresh(doctor)
    return doctor

def delete_doctor(db: Session, doctor_id: int) -> bool:
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return False
    db.delete(doctor)
    db.commit()
    return True
