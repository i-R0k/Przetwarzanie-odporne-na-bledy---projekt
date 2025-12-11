import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import datetime

from vetclinic_api.routers import (
    payments,
    users,
    animals,
    appointments,
    consultants,
    doctors,
    facilities,
    invoices,
    medical_records,
)
from vetclinic_api.main import app

client = TestClient(app)

# ========================== PAYMENTS ==========================
def test_stripe_success(monkeypatch):
    class DummySession:
        id = "sess_123"
        url = "https://stripe.com/pay"
    monkeypatch.setattr(payments, "get_invoice", lambda db, i: type("obj", (), {"amount": 10})())
    monkeypatch.setattr(payments, "create_stripe_session", lambda invoice_id, amount: DummySession())
    r = client.post("/payments/stripe/1")
    assert r.status_code == 200
    assert r.json()["provider"] == "stripe"

def test_stripe_404(monkeypatch):
    monkeypatch.setattr(payments, "get_invoice", lambda db, i: None)
    r = client.post("/payments/stripe/99")
    assert r.status_code == 404

def test_payu_success(monkeypatch):
    monkeypatch.setattr(payments, "get_invoice", lambda db, i: type("obj", (), {"amount": 20})())
    monkeypatch.setattr(payments, "create_payu_order", lambda *a, **kw: {"orderId": "OID", "redirectUri": "https://payu.com/redirect"})
    r = client.post("/payments/payu/1", params={"buyer_email": "a@b.com", "buyer_name": "Ala"})
    assert r.status_code == 200
    assert r.json()["provider"] == "payu"

def test_payu_404(monkeypatch):
    monkeypatch.setattr(payments, "get_invoice", lambda db, i: None)
    r = client.post("/payments/payu/99", params={"buyer_email": "a@b.com", "buyer_name": "Ala"})
    assert r.status_code == 404

# ========================== USERS ==========================
def test_register_only_clients(monkeypatch):
    monkeypatch.setattr(users, "create_client", lambda db, u: {
        "id": 123,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "phone_number": u.phone_number,
        "address": u.address,
        "postal_code": u.postal_code,
        "role": u.role,
        "wallet_address": u.wallet_address
    })
    data = {
        "first_name": "X",
        "last_name": "Y",
        "email": "z@a.com",
        "password": "Passw0rd!",
        "phone_number": "+48123456789",
        "address": "ul. Testowa 1",
        "postal_code": "00-001 Warszawa",
        "role": "klient",
        "wallet_address": "0x1"
    }
    r = client.post("/users/register", json=data)
    print("DEBUG:", r.status_code, r.json())
    assert r.status_code == 201

    data["role"] = "lekarz"
    r2 = client.post("/users/register", json=data)
    assert r2.status_code == 400

def test_users_get(monkeypatch):
    monkeypatch.setattr(users, "list_clients", lambda db: [
        {
            "id": 1,
            "first_name": "Anna",
            "last_name": "Kowalska",
            "email": "a@b.com",
            "phone_number": "+48123456789",
            "address": "ul. Testowa 1",
            "postal_code": "00-001 Warszawa",
            "role": "klient",
            "wallet_address": "0x123"
        },
        {
            "id": 2,
            "first_name": "Jan",
            "last_name": "Nowak",
            "email": "j@b.com",
            "phone_number": "+48987654321",
            "address": "ul. Nowa 2",
            "postal_code": "00-002 Kraków",
            "role": "klient",
            "wallet_address": "0x234"
        }
    ])
    r = client.get("/users/")
    print("DEBUG:", r.status_code, r.json())
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_user_get_notfound(monkeypatch):
    monkeypatch.setattr(users, "get_client", lambda db, uid: None)
    r = client.get("/users/77")
    assert r.status_code == 404

def test_user_update_notfound(monkeypatch):
    monkeypatch.setattr(users, "update_client", lambda db, uid, d: None)
    r = client.put("/users/88", json={
        "first_name": "Z",
        "wallet_address": "0x1"
    })
    assert r.status_code == 404

def test_user_delete(monkeypatch):
    monkeypatch.setattr(users, "delete_client", lambda db, uid: True)
    r = client.delete("/users/1")
    assert r.status_code == 204

def test_user_delete_notfound(monkeypatch):
    monkeypatch.setattr(users, "delete_client", lambda db, uid: False)
    r = client.delete("/users/2")
    assert r.status_code == 404

def test_user_delete_many(monkeypatch):
    monkeypatch.setattr(users, "delete_client", lambda db, uid: True)
    r = client.request("DELETE", "/users/", json=[1, 2])
    assert r.status_code == 204

# ========================== ANIMALS ==========================
def test_animal_create(monkeypatch):
    monkeypatch.setattr(animals.animal_crud, "create_animal", lambda db, a: {
        "id": 1,
        "name": "Rex",
        "species": "Dog",
        "owner_id": 1,
        "birthday": "2020-01-01",
        "microchip_number": None,
        "created_at": "2024-07-01T10:00:00",
        "updated_at": "2024-07-01T10:00:00"
    })
    r = client.post("/animals/", json={
        "name": "Rex",
        "species": "Dog",
        "birthday": "2020-01-01",
        "microchip_number": None,
        "owner_id": 1
    })
    assert r.status_code == 201

def test_animal_get_notfound(monkeypatch):
    monkeypatch.setattr(animals.animal_crud, "get_animal", lambda db, aid: None)
    r = client.get("/animals/99")
    assert r.status_code == 404

def test_animal_update_notfound(monkeypatch):
    monkeypatch.setattr(animals.animal_crud, "update_animal", lambda db, aid, a: None)
    r = client.put("/animals/88", json={"name": "NewName"})
    assert r.status_code == 404

def test_animal_delete_notfound(monkeypatch):
    monkeypatch.setattr(animals.animal_crud, "delete_animal", lambda db, aid: None)
    r = client.delete("/animals/88")
    assert r.status_code == 404

# ========================== APPOINTMENTS ==========================
def test_appointment_create(monkeypatch):
    monkeypatch.setattr(appointments.appointments_crud, "create_appointment", lambda db, a: {
        "id": 1,
        "owner_id": 1,
        "animal_id": 1,
        "visit_datetime": "2024-01-01T10:00:00",
        "fee": 123.0,
        "doctor_id": 2,
        "facility_id": 3,
        "created_at": "2024-01-01T09:00:00",
        "updated_at": "2024-01-01T09:00:00"
    })
    r = client.post("/appointments/", json={
        "owner_id": 1,
        "animal_id": 1,
        "visit_datetime": "2024-01-01T10:00:00",
        "fee": 123.0,
        "doctor_id": 2,
        "facility_id": 3
    })
    assert r.status_code == 201

def test_appointment_get_notfound(monkeypatch):
    monkeypatch.setattr(appointments.appointments_crud, "get_appointment", lambda db, aid: None)
    r = client.get("/appointments/66")
    assert r.status_code == 404

def test_appointment_update_notfound(monkeypatch):
    monkeypatch.setattr(appointments.appointments_crud, "update_appointment", lambda db, aid, a: None)
    r = client.put("/appointments/99", json={"fee": 50})
    assert r.status_code == 404

def test_appointment_delete_notfound(monkeypatch):
    monkeypatch.setattr(appointments.appointments_crud, "delete_appointment", lambda db, aid: None)
    r = client.delete("/appointments/99")
    assert r.status_code == 404

def test_appointment_slots(monkeypatch):
    # niedziela = pusto
    from datetime import date
    r = client.get("/appointments/free_slots/?doctor_id=1&date=2024-07-07") # 2024-07-07 to niedziela
    assert r.status_code == 200
    assert r.json() == []

# ========================== CONSULTANTS ==========================
def test_consultant_crud(monkeypatch):
    monkeypatch.setattr(consultants, "list_consultants", lambda db, skip=0, limit=100: [
        {
            "id": 1,
            "first_name": "Anna",
            "last_name": "Nowak",
            "email": "a@b.com",
            "facility_id": 2,
            "backup_email": "backup@b.com",
            "must_change_password": False,
            "wallet_address": "0xAAA"
        }
    ])
    r = client.get("/consultants/")
    assert r.status_code == 200

    monkeypatch.setattr(consultants, "create_consultant", lambda db, u: {
        "id": 2,
        "first_name": u["first_name"] if isinstance(u, dict) else u.first_name,
        "last_name": u["last_name"] if isinstance(u, dict) else u.last_name,
        "email": u["email"] if isinstance(u, dict) else u.email,
        "facility_id": u["facility_id"] if isinstance(u, dict) else u.facility_id,
        "backup_email": u.get("backup_email", "backup2@b.com") if isinstance(u, dict) else getattr(u, "backup_email", "backup2@b.com"),
        "must_change_password": True,
        "wallet_address": "0xBBB"
    })
    r2 = client.post("/consultants/", json={
        "first_name": "A", "last_name": "B", "email": "a@b.com",
        "backup_email": "b@b.com", "facility_id": 1, "wallet_address": "0xBBB"
    })
    assert r2.status_code == 201

    monkeypatch.setattr(consultants, "get_consultant", lambda db, cid: None)
    r3 = client.get("/consultants/99")
    assert r3.status_code == 404

    monkeypatch.setattr(consultants, "update_consultant", lambda db, cid, data: None)
    r4 = client.put("/consultants/77", json={"first_name": "X", "wallet_address": "0x1"})
    assert r4.status_code == 404

# ========================== DOCTORS ==========================
def test_doctor_crud(monkeypatch):
    monkeypatch.setattr(doctors, "list_doctors", lambda db: [
        {
            "id": 1,
            "first_name": "Jan",
            "last_name": "Kowalski",
            "email": "j.kowalski@vet.pl",
            "specialization": "Chirurgia",
            "permit_number": "12345",
            "facility_id": 1,
            "backup_email": "backup@vet.pl",
            "must_change_password": False,
            "wallet_address": "0xDOC1"
        }
    ])
    r = client.get("/doctors/")
    assert r.status_code == 200

    monkeypatch.setattr(doctors, "create_doctor", lambda db, u: ("raw", {
        "id": 2,
        "first_name": u["first_name"] if isinstance(u, dict) else u.first_name,
        "last_name": u["last_name"] if isinstance(u, dict) else u.last_name,
        "email": u["email"] if isinstance(u, dict) else u.email,
        "specialization": u.get("specialization", "Dermatologia") if isinstance(u, dict) else getattr(u, "specialization", "Dermatologia"),
        "permit_number": u.get("permit_number", "54321") if isinstance(u, dict) else getattr(u, "permit_number", "54321"),
        "facility_id": u.get("facility_id", 1) if isinstance(u, dict) else getattr(u, "facility_id", 1),
        "backup_email": u.get("backup_email", "backup2@vet.pl") if isinstance(u, dict) else getattr(u, "backup_email", "backup2@vet.pl"),
        "must_change_password": True,
        "wallet_address": "0xDOC2"
    }))
    r2 = client.post("/doctors/", json={
        "first_name": "A", "last_name": "B", "backup_email": "b@vet.pl",
        "specialization": "Dermatologia", "permit_number": "54321",
        "facility_id": 1, "wallet_address": "0xDOC2", "email": "a@vet.pl"
    })
    assert r2.status_code == 201

    monkeypatch.setattr(doctors, "get_doctor", lambda db, did: None)
    r3 = client.get("/doctors/99")
    assert r3.status_code == 404

    monkeypatch.setattr(doctors, "update_doctor", lambda db, did, data: None)
    r4 = client.put("/doctors/77", json={"first_name": "X", "wallet_address": "0x1"})
    assert r4.status_code == 404


# ========================== FACILITIES ==========================
def test_facility_crud(monkeypatch):
    monkeypatch.setattr(facilities, "get_facilities", lambda db, skip, limit: [
        {
            "id": 1,
            "name": "F",
            "address": "ul. Fikcyjna 2",
            "created_at": "2024-07-01T10:00:00",
            "updated_at": "2024-07-01T10:00:00"
        }
    ])
    r = client.get("/facilities/")
    assert r.status_code == 200

    monkeypatch.setattr(facilities, "create_facility", lambda db, d: {
        "id": 2,
        "name": d["name"] if isinstance(d, dict) else d.name,
        "address": d["address"] if isinstance(d, dict) else d.address,
        "created_at": "2024-07-01T10:01:00",
        "updated_at": "2024-07-01T10:01:00"
    })
    r2 = client.post("/facilities/", json={
        "name": "Główna",
        "address": "ul. Główna 1"
    })
    assert r2.status_code == 201


# ========================== INVOICES ==========================
def test_invoice_crud(monkeypatch):
    monkeypatch.setattr(invoices, "create_invoice", lambda db, inv: {
        "id": 1,
        "client_id": 1,
        "amount": 11,
        "status": "pending",
        "created_at": "2024-07-01T10:00:00"
    })
    r = client.post("/invoices/", json={"client_id": 1, "amount": 11})
    assert r.status_code == 201


# ========================== MEDICAL RECORDS ==========================
def test_medical_records_crud(monkeypatch):
    monkeypatch.setattr(medical_records, "list_medical_records", lambda db, skip=0, limit=100: [
        {
            "id": 1,
            "appointment_id": 101,
            "animal_id": 21,
            "description": "Kontrola",
            "created_at": "2024-07-01T10:00:00"
        }
    ])
    r = client.get("/medical_records/")
    assert r.status_code == 200

    monkeypatch.setattr(medical_records, "create_medical_record", lambda db, d: {
        "id": 2,
        "appointment_id": d.get("appointment_id", 102) if isinstance(d, dict) else getattr(d, "appointment_id", 102),
        "animal_id": d.get("animal_id", 22) if isinstance(d, dict) else getattr(d, "animal_id", 22),
        "description": d.get("description", "Szczepienie") if isinstance(d, dict) else getattr(d, "description", "Szczepienie"),
        "created_at": "2024-07-01T11:00:00"
    })
    r2 = client.post("/medical_records/", json={
        "appointment_id": 102,
        "animal_id": 22,
        "description": "Szczepienie"
    })
    assert r2.status_code == 201


def test_consultant_create(monkeypatch):
    def fake_create_consultant(db, user):
        return {
            "id": 123,
            "first_name": user.first_name if hasattr(user, "first_name") else user["first_name"],
            "last_name": user.last_name if hasattr(user, "last_name") else user["last_name"],
            "email": user.email if hasattr(user, "email") else user["email"],
            "facility_id": 1,
            "backup_email": "backup@a.com",
            "must_change_password": False,
            "wallet_address": "0xAAA"
        }
    monkeypatch.setattr(consultants, "create_consultant", fake_create_consultant)

    payload = {
        "first_name": "Anna",
        "last_name": "Nowak",
        "email": "anna@x.com",
        "facility_id": 1,
        "backup_email": "backup@a.com",
        "wallet_address": "0xAAA"
    }
    r = client.post("/consultants/", json=payload)
    assert r.status_code == 201
    assert r.json()["first_name"] == "Anna"
    assert r.json()["id"] == 123

# --- TEST 2: Odczyt pojedynczego konsultanta - 404 ---
def test_consultant_read_notfound(monkeypatch):
    monkeypatch.setattr(consultants, "get_consultant", lambda db, cid: None)
    r = client.get("/consultants/1234")
    assert r.status_code == 404

# --- TEST 3: Odczyt wszystkich wizyt (appointments) ---
def test_appointments_list(monkeypatch):
    monkeypatch.setattr(appointments.appointments_crud, "get_appointments", lambda db, skip, limit: [
        {
            "id": 1,
            "owner_id": 1,
            "animal_id": 2,
            "visit_datetime": "2024-07-03T09:00:00",
            "fee": 111.00,
            "doctor_id": 7,
            "facility_id": 1,
            "created_at": "2024-07-02T08:00:00",
            "updated_at": "2024-07-02T08:00:00"
        }
    ])
    r = client.get("/appointments/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert r.json()[0]["id"] == 1

# --- TEST 4: Lista wolnych slotów - niedziela ---
def test_appointments_free_slots_sunday(monkeypatch):
    # nie patchujemy, endpoint ma logiczkę która sprawdza niedzielę
    response = client.get("/appointments/free_slots/?doctor_id=5&date=2024-07-07")  # 2024-07-07 to niedziela
    assert response.status_code == 200
    assert response.json() == []
