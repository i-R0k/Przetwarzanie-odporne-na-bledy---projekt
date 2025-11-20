import pytest
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vetclinic_api.core.database import Base
from vetclinic_api.schemas.animal import AnimalCreate, AnimalUpdate
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate
from vetclinic_api.schemas.facility import FacilityCreate, FacilityUpdate
from vetclinic_api.schemas.invoice import InvoiceCreate
from vetclinic_api.schemas.medical_records import MedicalRecordCreate, MedicalRecordUpdate
from vetclinic_api.schemas.users import (
    ClientCreate,
    ConsultantCreate,
    DoctorCreate,
    UserUpdate,
)
from vetclinic_api.schemas.weight_logs import WeightLogCreate

import vetclinic_api.crud.animal_crud as animal_crud
import vetclinic_api.crud.appointments_crud as appointments_crud
import vetclinic_api.crud.consultants as consultants
import vetclinic_api.crud.doctors as doctors
import vetclinic_api.crud.facility_crud as facility_crud
import vetclinic_api.crud.invoice_crud as invoice_crud
import vetclinic_api.crud.medical_records as medical_records
import vetclinic_api.crud.users_crud as users_crud
import vetclinic_api.crud.weight_log_crud as weight_log_crud


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture
def db(engine) -> Session:
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def test_animal_crud(db):
    a1 = animal_crud.create_animal(
        db,
        AnimalCreate(
            name="Rex",
            species="Dog",
            birthday=datetime(2020, 1, 1),
            microchip_number=None,
            owner_id=1,
        ),
    )
    assert a1.name == "Rex" and a1.microchip_number is None

    chip = "9" * 15
    a2 = animal_crud.create_animal(
        db,
        AnimalCreate(
            name="Mia",
            species="Cat",
            birthday=datetime(2021, 5, 5),
            microchip_number=chip,
            owner_id=2,
        ),
    )
    assert a2.microchip_number == chip

    with pytest.raises(ValueError):
        animal_crud.create_animal(
            db,
            AnimalCreate(
                name="Bad",
                species="Dog",
                birthday=datetime(2019, 3, 3),
                microchip_number="123",
                owner_id=3,
            ),
        )

    assert animal_crud.get_animal(db, a1.id).id == a1.id
    assert any(x.id == a2.id for x in animal_crud.get_animals(db))

    updated = animal_crud.update_animal(db, a1.id, AnimalUpdate(name="Rexie"))
    assert updated.name == "Rexie"

    with pytest.raises(ValueError):
        animal_crud.update_animal(db, a1.id, AnimalUpdate(microchip_number="bad"))

    deleted = animal_crud.delete_animal(db, a1.id)
    assert deleted.id == a1.id
    assert animal_crud.get_animal(db, a1.id) is None


def test_facility_crud(db):
    assert facility_crud.get_facilities(db) == []

    facility = facility_crud.create_facility(
        db, FacilityCreate(name="Main Clinic", address="123 Vet St")
    )
    assert facility.name == "Main Clinic" and facility.address == "123 Vet St"

    assert facility_crud.get_facility(db, facility.id).id == facility.id
    assert facility in facility_crud.get_facilities(db)

    updated = facility_crud.update_facility(
        db, facility.id, FacilityUpdate(address="456 New Ave")
    )
    assert updated.address == "456 New Ave"
    assert facility_crud.update_facility(db, 999, FacilityUpdate(name="X")) is None

    facility_crud.delete_facility(db, facility.id)
    assert facility_crud.get_facility(db, facility.id) is None


def test_consultants_crud(db, monkeypatch):
    from vetclinic_api.services.email_service import EmailService

    monkeypatch.setattr(EmailService, "send_temporary_password", lambda e, p: None)

    c1 = consultants.create_consultant(
        db,
        ConsultantCreate(
            first_name="Anna",
            last_name="K",
            facility_id=1,
            backup_email="b@vet.pl",
            email="anna@vet.pl",
        ),
    )
    assert c1.email == "anna@vet.pl" and c1.must_change_password

    c2 = consultants.create_consultant(
        db,
        ConsultantCreate(
            first_name="Anna",
            last_name="K",
            facility_id=1,
            backup_email="b2@vet.pl",
            email="anna2@vet.pl",
        ),
    )
    assert c2.email != c1.email and c2.id != c1.id

    all_c = consultants.list_consultants(db)
    assert c1 in all_c and c2 in all_c
    assert consultants.get_consultant(db, c1.id) == c1
    assert consultants.get_consultant(db, 0) is None

    updated = consultants.update_consultant(
        db,
        c1.id,
        UserUpdate(password="NewP@ss1", first_name="Ania", wallet_address="0xAAA"),
    )
    assert updated.first_name == "Ania" and not updated.must_change_password

    assert consultants.delete_consultant(db, c1.id)
    assert consultants.get_consultant(db, c1.id) is None


def test_doctors_crud(db, monkeypatch):
    from vetclinic_api.services.email_service import EmailService

    monkeypatch.setattr(EmailService, "send_temporary_password", lambda e, p: None)

    raw_pw, doctor = doctors.create_doctor(
        db,
        DoctorCreate(
            first_name="Jan",
            last_name="Nowak",
            email="jan@vet.pl",
            backup_email="bk@vet.pl",
            specialization="Surgery",
            permit_number="12345",
            facility_id=1,
        ),
    )
    assert isinstance(raw_pw, str) and doctor.must_change_password

    assert doctor in doctors.list_doctors(db)
    assert doctors.get_doctor(db, doctor.id) == doctor
    assert doctors.get_doctor(db, 0) is None

    updated = doctors.update_doctor(
        db,
        doctor.id,
        UserUpdate(
            backup_email="new@vet.pl",
            specialization="Dentistry",
            permit_number="54321",
            facility_id=2,
            password="XyZ!234",
            first_name="Janek",
            last_name="K",
            email="janek@vet.pl",
            wallet_address="0xDOC",
        ),
    )
    assert updated.backup_email == "new@vet.pl" and updated.facility_id == 2

    assert doctors.delete_doctor(db, doctor.id)
    assert doctors.get_doctor(db, doctor.id) is None


def test_users_crud(db, monkeypatch):
    from vetclinic_api.services.email_service import EmailService

    monkeypatch.setattr(EmailService, "send_temporary_password", lambda e, p: None)

    client = users_crud.create_client(
        db,
        ClientCreate(
            first_name="Basia",
            last_name="K",
            email="basia@c.pl",
            password="P@ssw0rd",
            phone_number="+48123456789",
            address="Addr 5",
            postal_code="00-001 Warszawa",
            role="client",
            wallet_address="0xABC",
        ),
    )
    assert client.first_name == "Basia" and client.must_change_password

    clients = users_crud.list_clients(db)
    assert any(cli.id == client.id for cli in clients)
    assert users_crud.get_client(db, client.id) == client

    updated = users_crud.update_client(
        db,
        client.id,
        UserUpdate(
            password="New!234",
            first_name="Basiunia",
            phone_number="+48100000000",
            address="New Addr",
            postal_code="01-111 City",
            wallet_address="0xDEF",
        ),
    )
    assert updated.first_name == "Basiunia"

    assert users_crud.delete_client(db, client.id)
    assert users_crud.get_client(db, client.id) is None


def test_appointments_crud(db, monkeypatch):
    monkeypatch.setattr(appointments_crud, "create_invoice", lambda db, i: None)

    now = datetime.utcnow()
    appt = appointments_crud.create_appointment(
        db,
        AppointmentCreate(
            owner_id=1,
            animal_id=2,
            visit_datetime=now,
            fee=Decimal("150.00"),
            doctor_id=7,
            facility_id=3,
        ),
    )

    assert appointments_crud.get_appointment(db, appt.id).id == appt.id
    assert appt in appointments_crud.get_appointments(db)

    updated = appointments_crud.update_appointment(
        db, appt.id, AppointmentUpdate(fee=Decimal("200.00"))
    )
    assert updated.fee == Decimal("200.00")

    assert appt in appointments_crud.get_appointments_by_owner(db, 1)
    removed = appointments_crud.delete_appointment(db, appt.id)
    assert removed.id == appt.id
    assert appointments_crud.get_appointment(db, appt.id) is None


def test_invoice_crud(db):
    inv = invoice_crud.create_invoice(
        db, InvoiceCreate(client_id=10, amount=Decimal("99.99"))
    )
    assert inv.client_id == 10 and inv.amount == Decimal("99.99")
    assert invoice_crud.get_invoice(db, inv.id).id == inv.id
    assert inv in invoice_crud.list_invoices(db)
    updated = invoice_crud.update_invoice_status(db, inv.id, "PAID")
    assert updated.status == "PAID"


def test_weight_log_crud(db):
    wl = weight_log_crud.create_weight_log(
        db, WeightLogCreate(animal_id=5, weight=12.3, recorded_at=None)
    )
    assert wl.animal_id == 5 and float(wl.weight) == 12.3
    assert weight_log_crud.get_weight_log(db, wl.id).id == wl.id
    assert wl in weight_log_crud.list_weight_logs(db)
    removed = weight_log_crud.delete_weight_log(db, wl.id)
    assert removed.id == wl.id
    assert weight_log_crud.get_weight_log(db, wl.id) is None


def test_medical_records_crud(db, monkeypatch):
    monkeypatch.setattr(medical_records, "get_appointment", lambda db, i: True)
    monkeypatch.setattr(medical_records, "get_animal", lambda db, i: True)

    record = medical_records.create_medical_record(
        db,
        MedicalRecordCreate(
            appointment_id=1,
            animal_id=1,
            description="Desc",
        ),
    )
    assert record.description == "Desc"
    rid = record.id

    assert medical_records.get_medical_record(db, rid).id == rid
    with pytest.raises(Exception):
        medical_records.get_medical_record(db, 0)

    assert any(r.id == rid for r in medical_records.list_medical_records(db))
    assert any(
        r.id == rid
        for r in medical_records.list_medical_records_by_appointment(db, 1)
    )

    updated = medical_records.update_medical_record(
        db, rid, MedicalRecordUpdate(description="New")
    )
    assert updated.description == "New"

    medical_records.delete_medical_record(db, rid)
    with pytest.raises(Exception):
        medical_records.get_medical_record(db, rid)
