import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.gui


# ---------- consultant_service.py ----------
@patch("vetclinic_gui.services.consultant_service.requests.get")
def test_consultant_list(mock_get):
    mock_get.return_value.json.return_value = [{"id": 1, "backup_email": "a@b.pl"}]
    mock_get.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.consultant_service import ConsultantService

    out = ConsultantService.list()
    assert isinstance(out, list)
    assert hasattr(out[0], "backup_email")
    mock_get.assert_called_once()


@patch("vetclinic_gui.services.consultant_service.requests.post")
def test_consultant_create(mock_post):
    mock_post.return_value.json.return_value = {"id": 1, "backup_email": "a@b.pl"}
    mock_post.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.consultant_service import ConsultantService

    payload = {"backup_email": "a@b.pl"}
    result = ConsultantService.create(payload)
    assert result.backup_email == "a@b.pl"
    assert hasattr(result, "raw_password")


@patch("vetclinic_gui.services.consultant_service.requests.put")
def test_consultant_update(mock_put):
    mock_put.return_value.json.return_value = {"id": 1, "backup_email": "x@y.pl"}
    mock_put.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.consultant_service import ConsultantService

    result = ConsultantService.update(1, {"backup_email": "x@y.pl"})
    assert result.backup_email == "x@y.pl"
    mock_put.assert_called_once()


@patch("vetclinic_gui.services.consultant_service.requests.delete")
def test_consultant_delete(mock_delete):
    mock_delete.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.consultant_service import ConsultantService

    ConsultantService.delete(1)
    mock_delete.assert_called_once()


# ---------- doctors_service.py ----------
@patch("vetclinic_gui.services.doctors_service.requests.get")
def test_doctor_list(mock_get):
    mock_get.return_value.json.return_value = [{"id": 1, "email": "lek@med.pl"}]
    mock_get.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.doctors_service import DoctorService

    out = DoctorService.list()
    assert isinstance(out, list)
    assert hasattr(out[0], "email")


@patch("vetclinic_gui.services.doctors_service.requests.get")
def test_doctor_get(mock_get):
    mock_get.return_value.json.return_value = {"id": 5, "email": "lek@med.pl"}
    mock_get.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.doctors_service import DoctorService

    out = DoctorService.get(5)
    assert out.id == 5


@patch("vetclinic_gui.services.doctors_service.requests.post")
def test_doctor_create(mock_post):
    mock_post.return_value.json.return_value = {"id": 6, "email": "lek@med.pl"}
    mock_post.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.doctors_service import DoctorService

    out = DoctorService.create({"email": "lek@med.pl"})
    assert out.email == "lek@med.pl"


@patch("vetclinic_gui.services.doctors_service.requests.put")
def test_doctor_update(mock_put):
    mock_put.return_value.json.return_value = {"id": 7, "email": "l@x.pl"}
    mock_put.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.doctors_service import DoctorService

    out = DoctorService.update(7, {"email": "l@x.pl"})
    assert out.email == "l@x.pl"


@patch("vetclinic_gui.services.doctors_service.requests.delete")
def test_doctor_delete(mock_del):
    mock_del.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.doctors_service import DoctorService

    DoctorService.delete(9)
    mock_del.assert_called_once()


# ---------- facility_service.py ----------
@patch("vetclinic_gui.services.facility_service.requests.get")
def test_facility_list(mock_get):
    mock_get.return_value.json.return_value = [{"id": 1, "name": "ABC"}]
    mock_get.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.facility_service import FacilityService

    out = FacilityService.list()
    assert isinstance(out, list)
    assert out[0].name == "ABC"


@patch("vetclinic_gui.services.facility_service.requests.get")
def test_facility_get(mock_get):
    mock_get.return_value.json.return_value = {"id": 5, "name": "XYZ"}
    mock_get.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.facility_service import FacilityService

    out = FacilityService.get(5)
    assert out.id == 5


@patch("vetclinic_gui.services.facility_service.requests.post")
def test_facility_create(mock_post):
    mock_post.return_value.json.return_value = {"id": 6, "name": "DEF"}
    mock_post.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.facility_service import FacilityService

    out = FacilityService.create({"name": "DEF"})
    assert out.name == "DEF"


@patch("vetclinic_gui.services.facility_service.requests.put")
def test_facility_update(mock_put):
    mock_put.return_value.json.return_value = {"id": 7, "name": "Upd"}
    mock_put.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.facility_service import FacilityService

    out = FacilityService.update(7, {"name": "Upd"})
    assert out.name == "Upd"


@patch("vetclinic_gui.services.facility_service.requests.delete")
def test_facility_delete(mock_del):
    mock_del.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.facility_service import FacilityService

    FacilityService.delete(10)
    mock_del.assert_called_once()


# ---------- invoice_service.py ----------
@patch("vetclinic_gui.services.invoice_service.SessionLocal")
@patch("vetclinic_gui.services.invoice_service.list_invoices")
def test_invoice_list_by_client(mock_list_invoices, mock_session):
    class DummyInv:
        def __init__(self, id, client_id):
            self.id = id
            self.client_id = client_id

    mock_list_invoices.return_value = [DummyInv(1, 4), DummyInv(2, 9)]
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.invoice_service import InvoiceService

    out = InvoiceService.list_by_client(9)
    assert out and out[0].client_id == 9


# ---------- medical_records_service.py ----------
@patch("vetclinic_gui.services.medical_records_service.requests.get")
def test_medical_records_list(mock_get):
    mock_get.return_value.json.return_value = [{"id": 1}]
    mock_get.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.medical_records_service import MedicalRecordsService

    out = MedicalRecordsService.list()
    assert out
    mock_get.assert_called_once()


# ---------- payment_service.py ----------
@patch("vetclinic_gui.services.payment_service.requests.post")
def test_payment_stripe_checkout(mock_post):
    mock_post.return_value.json.return_value = {"url": "http://pay"}
    mock_post.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.payment_service import PaymentService

    out = PaymentService.stripe_checkout(7)
    assert out == "http://pay"


@patch("vetclinic_gui.services.payment_service.requests.post")
def test_payment_payu_checkout(mock_post):
    mock_post.return_value.json.return_value = {"redirectUri": "http://payu"}
    mock_post.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.payment_service import PaymentService

    out = PaymentService.payu_checkout(7, "e@x.pl", "Imie Nazwisko")
    assert out == "http://payu"


# ---------- temp_email_service.py ----------
@patch("vetclinic_gui.services.temp_email_service.requests.get")
def test_temp_email_domain(mock_get):
    mock_get.return_value.json.return_value = {"hydra:member": [{"domain": "mail.test"}]}
    mock_get.return_value.raise_for_status.return_value = None
    from vetclinic_gui.services.temp_email_service import TempEmailService

    out = TempEmailService.get_domain()
    assert out == "mail.test"


# ---------- weight_logs_service.py ----------
@patch("vetclinic_gui.services.weight_logs_service.SessionLocal")
@patch("vetclinic_gui.services.weight_logs_service.list_weight_logs")
def test_weight_log_list_by_animal(mock_list, mock_session):
    class WL:
        animal_id = 2

    mock_list.return_value = [WL()]
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.weight_logs_service import WeightLogService

    out = WeightLogService.list_by_animal(2)
    assert out and out[0].animal_id == 2


# ---------- AuthService ----------
@patch("vetclinic_gui.services.auth_service.requests.post")
def test_authservice_login(mock_post):
    from vetclinic_gui.services.auth_service import AuthService

    mock_post.return_value.status_code = 200
    service = AuthService("http://fakeurl")
    service.login("e@x.pl", "haslo", otp_code="111", totp_code="222")
    payload = mock_post.call_args[1]["json"]
    assert payload["email"] == "e@x.pl"
    assert payload["otp_code"] == "111"
    assert payload["totp_code"] == "222"


@patch("vetclinic_gui.services.auth_service.requests.post")
def test_authservice_confirm_totp(mock_post):
    from vetclinic_gui.services.auth_service import AuthService

    service = AuthService()
    service.confirm_totp("e@x.pl", "123456")
    mock_post.assert_called_with(
        f"{service.base}/users/confirm-totp",
        json={"email": "e@x.pl", "totp_code": "123456"},
    )


@patch("vetclinic_gui.services.auth_service.requests.post")
def test_authservice_change_password(mock_post):
    from vetclinic_gui.services.auth_service import AuthService

    service = AuthService()
    service.change_password("e@x.pl", "old", "new", reset_totp=True)
    json_payload = mock_post.call_args[1]["json"]
    assert json_payload["reset_totp"] is True


@patch("vetclinic_gui.services.auth_service.requests.post")
def test_authservice_setup_totp(mock_post):
    from vetclinic_gui.services.auth_service import AuthService

    service = AuthService()
    service.setup_totp("e@x.pl")
    assert mock_post.call_args[1]["params"] == {"email": "e@x.pl"}


# ---------- ClientService ----------
@patch("vetclinic_gui.services.clients_service.SessionLocal")
@patch("vetclinic_gui.services.clients_service.list_clients")
def test_clientservice_list(mock_list, mock_session):
    mock_list.return_value = [{"id": 1}]
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.clients_service import ClientService

    out = ClientService.list()
    assert out


@patch("vetclinic_gui.services.clients_service.SessionLocal")
@patch("vetclinic_gui.services.clients_service.get_client")
def test_clientservice_get(mock_get, mock_session):
    mock_get.return_value = {"id": 5}
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.clients_service import ClientService

    out = ClientService.get(5)
    assert out["id"] == 5


@patch("vetclinic_gui.services.clients_service.SessionLocal")
@patch("vetclinic_gui.services.clients_service.crud_create_user")
@patch("vetclinic_gui.services.clients_service.ClientCreate")
def test_clientservice_create(mock_ccreate, mock_crud, mock_session):
    mock_crud.return_value = {"id": 3, "role": "klient"}
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.clients_service import ClientService

    out = ClientService.create({"first_name": "Anna", "email": "a@b.pl"})
    assert out["role"] == "klient"


@patch("vetclinic_gui.services.clients_service.SessionLocal")
@patch("vetclinic_gui.services.clients_service.crud_update_user")
@patch("vetclinic_gui.services.clients_service.UserUpdate")
def test_clientservice_update(mock_update, mock_crud, mock_session):
    mock_crud.return_value = {"id": 10}
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.clients_service import ClientService

    out = ClientService.update(10, {"email": "c@x.pl"})
    assert out["id"] == 10


@patch("vetclinic_gui.services.clients_service.SessionLocal")
@patch("vetclinic_gui.services.clients_service.crud_delete_user")
def test_clientservice_delete(mock_delete, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.clients_service import ClientService

    ClientService.delete(6)
    mock_delete.assert_called_once()


# ---------- AnimalService ----------
@patch("vetclinic_gui.services.animals_service.SessionLocal")
@patch("vetclinic_gui.services.animals_service.get_animals")
def test_animalservice_list(mock_list, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    mock_list.return_value = [{"id": 3, "owner_id": 5}]
    from vetclinic_gui.services.animals_service import AnimalService

    out = AnimalService.list()
    assert out


def test_animalservice_list_by_owner():
    from vetclinic_gui.services.animals_service import AnimalService

    class Dummy:
        def __init__(self, owner_id):
            self.owner_id = owner_id

    AnimalService.list = staticmethod(lambda: [Dummy(5), Dummy(7), Dummy(5)])
    out = AnimalService.list_by_owner(5)
    assert all([x.owner_id == 5 for x in out])


@patch("vetclinic_gui.services.animals_service.SessionLocal")
@patch("vetclinic_gui.services.animals_service.get_animal")
def test_animalservice_get(mock_get, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    mock_get.return_value = {"id": 9}
    from vetclinic_gui.services.animals_service import AnimalService

    out = AnimalService.get(9)
    assert out["id"] == 9


@patch("vetclinic_gui.services.animals_service.SessionLocal")
@patch("vetclinic_gui.services.animals_service.create_animal")
@patch("vetclinic_gui.services.animals_service.AnimalSchema.AnimalCreate")
def test_animalservice_create(mock_cc, mock_cr, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    mock_cr.return_value = {"id": 4}
    from vetclinic_gui.services.animals_service import AnimalService

    out = AnimalService.create({"owner_id": 2, "name": "Reksio"})
    assert out["id"] == 4


@patch("vetclinic_gui.services.animals_service.SessionLocal")
@patch("vetclinic_gui.services.animals_service.update_animal")
@patch("vetclinic_gui.services.animals_service.AnimalSchema.AnimalUpdate")
def test_animalservice_update(mock_uc, mock_uu, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    mock_uu.return_value = {"id": 10}
    from vetclinic_gui.services.animals_service import AnimalService

    out = AnimalService.update(10, {"name": "X"})
    assert out["id"] == 10


@patch("vetclinic_gui.services.animals_service.SessionLocal")
@patch("vetclinic_gui.services.animals_service.delete_animal")
def test_animalservice_delete(mock_del, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    from vetclinic_gui.services.animals_service import AnimalService

    AnimalService.delete(7)
    mock_del.assert_called_once()


# ---------- AppointmentService ----------
@patch("vetclinic_gui.services.appointments_service.SessionLocal")
def test_appointments_list(mock_session):
    db = MagicMock()
    db.query().options().all.return_value = [{"id": 1}]
    mock_session.return_value = db
    from vetclinic_gui.services.appointments_service import AppointmentService

    out = AppointmentService.list()
    assert out


@patch("vetclinic_gui.services.appointments_service.SessionLocal")
def test_appointments_get(mock_session):
    db = MagicMock()
    db.query().options().filter().one_or_none.return_value = {"id": 5}
    mock_session.return_value = db
    from vetclinic_gui.services.appointments_service import AppointmentService

    out = AppointmentService.get(5)
    assert out["id"] == 5


@patch("vetclinic_gui.services.appointments_service.SessionLocal")
def test_appointments_list_by_owner(mock_session):
    db = MagicMock()
    db.query().options().filter().all.return_value = [{"id": 5, "owner_id": 1}]
    mock_session.return_value = db
    from vetclinic_gui.services.appointments_service import AppointmentService

    out = AppointmentService.list_by_owner(1)
    assert out[0]["owner_id"] == 1


@patch("vetclinic_gui.services.appointments_service.SessionLocal")
def test_appointments_get_free_slots(mock_session):
    db = MagicMock()
    db.query().filter().all.return_value = []
    mock_session.return_value = db
    from vetclinic_gui.services.appointments_service import AppointmentService

    slots = AppointmentService.get_free_slots(1, "2025-06-30")
    assert "08:00" in slots

    slots2 = AppointmentService.get_free_slots(1, "2025-06-29")
    assert slots2 == []

    slots3 = AppointmentService.get_free_slots(1, "ZLY")
    assert slots3 == []
