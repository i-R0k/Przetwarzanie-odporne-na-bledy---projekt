from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vetclinic_api.crud.appointments_crud import get_appointment
from vetclinic_api.crud.animal_crud import get_animal
from vetclinic_api.models.medical_records import MedicalRecord as MRModel
from vetclinic_api.schemas.medical_records import MedicalRecordCreate, MedicalRecordUpdate


def list_medical_records(
    db: Session, skip: int = 0, limit: int = 100
) -> List[MRModel]:
    """Return paginated medical records."""
    return db.query(MRModel).offset(skip).limit(limit).all()


def list_medical_records_by_appointment(
    db: Session, appointment_id: int
) -> List[MRModel]:
    """Return medical records for a given appointment."""
    return (
        db.query(MRModel)
        .filter(MRModel.appointment_id == appointment_id)
        .all()
    )


def get_medical_record(db: Session, record_id: int) -> MRModel:
    """Return a single medical record or raise 404."""
    rec = db.query(MRModel).filter(MRModel.id == record_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found",
        )
    return rec


def create_medical_record(db: Session, data: MedicalRecordCreate) -> MRModel:
    """Create a medical record linked to existing appointment and animal."""
    get_appointment(db, data.appointment_id)
    get_animal(db, data.animal_id)

    db_record = MRModel(
        description=data.description,
        appointment_id=data.appointment_id,
        animal_id=data.animal_id,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def update_medical_record(
    db: Session, record_id: int, rec_update: MedicalRecordUpdate
) -> MRModel:
    """Update fields on an existing medical record."""
    db_rec = get_medical_record(db, record_id)

    if rec_update.appointment_id is not None:
        get_appointment(db, rec_update.appointment_id)
        db_rec.appointment_id = rec_update.appointment_id
    if rec_update.animal_id is not None:
        get_animal(db, rec_update.animal_id)
        db_rec.animal_id = rec_update.animal_id
    if rec_update.description is not None:
        db_rec.description = rec_update.description

    db.commit()
    db.refresh(db_rec)
    return db_rec


def delete_medical_record(db: Session, record_id: int) -> None:
    """Delete a medical record."""
    db_rec = get_medical_record(db, record_id)
    db.delete(db_rec)
    db.commit()
