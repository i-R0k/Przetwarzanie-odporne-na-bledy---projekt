from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MedicalRecordBase(BaseModel):
    description: str

class MedicalRecordCreate(MedicalRecordBase):
    appointment_id: int
    animal_id: int

class MedicalRecordUpdate(BaseModel):
    description: str | None = None
    appointment_id: int | None = None
    animal_id: int | None = None

class MedicalRecord(MedicalRecordBase):
    id: int
    created_at: datetime
    appointment_id: int
    animal_id: int

    model_config = ConfigDict(from_attributes=True)
