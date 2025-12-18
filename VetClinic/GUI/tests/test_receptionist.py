import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QMessageBox, QComboBox, QLineEdit
pytestmark = pytest.mark.gui

# ===================== CLIENT REGISTRATION =====================

@patch("vetclinic_gui.windows.Receptionist.client_registration.ClientService")
def test_client_registration_success(mock_service, app):
    from vetclinic_gui.windows.Receptionist.client_registration import RegistrationPage
    page = RegistrationPage()
    page.first_name_le.setText("Jan")
    page.last_name_le.setText("Kowalski")
    page.phone_le.setText("123456789")
    page.email_le.setText("jan@kowal.pl")
    page.address_le.setText("ul. Testowa 1")
    page.postal_code_le.setText("00-000")
    mock_service.create.return_value = MagicMock()
    with patch.object(QMessageBox, "information") as infomock:
        page._on_register()
        assert mock_service.create.called
        assert infomock.called
    # Po sukcesie wszystkie pola puste
    for le in (page.first_name_le, page.last_name_le, page.phone_le, page.email_le, page.address_le, page.postal_code_le):
        assert le.text() == ""

@patch("vetclinic_gui.windows.Receptionist.client_registration.ClientService")
def test_client_registration_missing_fields(mock_service, app):
    from vetclinic_gui.windows.Receptionist.client_registration import RegistrationPage
    page = RegistrationPage()
    # Wszystko puste
    with patch.object(QMessageBox, "warning") as warnmock:
        page._on_register()
        assert warnmock.called
    assert not mock_service.create.called

# ===================== ANIMAL REGISTRATION =====================

@patch("vetclinic_gui.windows.Receptionist.animal_registration.AnimalService")
@patch("vetclinic_gui.windows.Receptionist.animal_registration.ClientService")
def test_animal_registration_success(mock_client_service, mock_animal_service, app):
    from vetclinic_gui.windows.Receptionist.animal_registration import AnimalRegistrationPage
    class DummyClient:
        id = 1
        first_name = "Anna"
        last_name = "Nowak"
        address = "ul. Testowa"
    mock_client_service.list.return_value = [DummyClient()]
    page = AnimalRegistrationPage()
    page.name_le.setText("Reksio")
    page.species_le.setText("pies")
    page.breed_le.setText("mieszaniec")
    page.gender_cb.setCurrentIndex(1)
    page.weight_ds.setValue(8.5)
    page.chip_le.setText("CHIP123")
    page.notes_te.setPlainText("Szczepiony")
    # symulacja wyboru właściciela przez completer:
    text = "Anna Nowak, ul. Testowa"
    page._on_owner_selected(text)
    page._selected_owner_id = 1
    with patch.object(QMessageBox, "information") as infomock:
        page._on_register()
        assert mock_animal_service.create.called
        assert infomock.called
    assert page.name_le.text() == ""
    assert page.species_le.text() == ""
    assert page.owner_le.text() == ""

@patch("vetclinic_gui.windows.Receptionist.animal_registration.AnimalService")
@patch("vetclinic_gui.windows.Receptionist.animal_registration.ClientService")
def test_animal_registration_missing_fields(mock_client_service, mock_animal_service, app):
    from vetclinic_gui.windows.Receptionist.animal_registration import AnimalRegistrationPage
    mock_client_service.list.return_value = []
    page = AnimalRegistrationPage()
    # Wszystko puste
    with patch.object(QMessageBox, "warning") as warnmock:
        page._on_register()
        assert warnmock.called
    assert not mock_animal_service.create.called

# ===================== DOCTOR REGISTRATION =====================

@patch("vetclinic_gui.windows.Receptionist.doctor_registration.DoctorService")
def test_doctor_registration_success(mock_service, app):
    from vetclinic_gui.windows.Receptionist.doctor_registration import DoctorRegistrationPage
    mock_service.list.return_value = []
    page = DoctorRegistrationPage()
    page.first_name_le.setText("Marek")
    page.last_name_le.setText("Nowy")
    page.spec_le.setText("Chirurgia")
    page.permit_le.setText("9999")
    page.backup_email_le.setText("backup@x.pl")
    # symulacja automatycznego emaila:
    page._update_email()
    page.email_le.setText("m.nowy@lekarz.vetclinic.com")
    mock_service.create.return_value = MagicMock(first_name="Marek", last_name="Nowy", email="m.nowy@lekarz.vetclinic.com")
    with patch.object(QMessageBox, "information") as infomock:
        page._on_register()
        assert mock_service.create.called
        assert infomock.called

@patch("vetclinic_gui.windows.Receptionist.doctor_registration.DoctorService")
def test_doctor_registration_missing_fields(mock_service, app):
    from vetclinic_gui.windows.Receptionist.doctor_registration import DoctorRegistrationPage
    mock_service.list.return_value = []
    page = DoctorRegistrationPage()
    # Wszystko puste
    with patch.object(QMessageBox, "warning") as warnmock:
        page._on_register()
        assert warnmock.called
    assert not mock_service.create.called

# ===================== APPOINTMENT BOOKING =====================

@patch("vetclinic_gui.windows.Receptionist.appointment_add.AppointmentService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.DoctorService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.FacilityService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.AnimalService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.ClientService")
def test_appointment_booking_success(mock_client, mock_animal, mock_fac, mock_doc, mock_appt, app):
    from vetclinic_gui.windows.Receptionist.appointment_add import AppointmentBookingPage
    # Dane testowe
    class DummyClient: id=10; first_name="Jan"; last_name="Kowal"; address="ul. Y"
    class DummyAnimal: id=15; name="Puszek"
    class DummyDoctor: id=5; first_name="Ala"; last_name="Doktorka"; specialization="Chirurgia"
    class DummyFacility: id=7; name="Przychodnia"
    mock_client.list.return_value = [DummyClient()]
    mock_animal.list_by_owner.return_value = [DummyAnimal()]
    mock_doc.list.return_value = [DummyDoctor()]
    mock_fac.list.return_value = [DummyFacility()]
    mock_appt.get_free_slots.return_value = ["09:00", "10:00"]
    page = AppointmentBookingPage()
    # Wybierz klienta
    page._on_client_chosen("Jan Kowal, ul. Y")
    # Wybierz zwierzę
    page.animal_cb.setCurrentIndex(0)
    # Wybierz placówkę
    page.facility_cb.setCurrentIndex(1)
    # Wybierz lekarza
    page._on_doctor_chosen("Ala Doktorka (Chirurgia)")
    # Wybierz godzinę
    page.time_cb.setCurrentIndex(0)
    # Notes
    page.notes_te.setPlainText("Pilna konsultacja")
    with patch.object(QMessageBox, "information") as infomock:
        page._on_save()
        assert mock_appt.create.called
        assert infomock.called

@patch("vetclinic_gui.windows.Receptionist.appointment_add.AppointmentService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.DoctorService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.FacilityService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.AnimalService")
@patch("vetclinic_gui.windows.Receptionist.appointment_add.ClientService")
def test_appointment_booking_missing_fields(mock_client, mock_animal, mock_fac, mock_doc, mock_appt, app):
    from vetclinic_gui.windows.Receptionist.appointment_add import AppointmentBookingPage
    mock_client.list.return_value = []
    mock_doc.list.return_value = []
    mock_fac.list.return_value = []
    page = AppointmentBookingPage()
    with patch.object(QMessageBox, "warning") as warnmock:
        page._on_save()
        assert warnmock.called
    assert not mock_appt.create.called

# ===================== DASHBOARD =====================

@patch("vetclinic_gui.windows.Receptionist.dashboard.AppointmentService")
@patch("vetclinic_gui.windows.Receptionist.dashboard.DoctorService")
@patch("vetclinic_gui.windows.Receptionist.dashboard.ClientService")
@patch("vetclinic_gui.windows.Receptionist.dashboard.AnimalService")
@patch("vetclinic_gui.windows.Receptionist.dashboard.FacilityService")
def test_receptionist_dashboard_load(mock_fac, mock_animal, mock_client, mock_doc, mock_appt, app):
    from vetclinic_gui.windows.Receptionist.dashboard import ReceptionistDashboardPage
    import datetime

    class DummyDoctor: id=1; first_name="Jan"; last_name="Lek"
    class DummyClient: id=10; first_name="Ala"; last_name="Nowak"
    class DummyAnimal: id=15; name="Azor"
    class DummyFacility: id=7; name="Przychodnia"
    now = datetime.datetime.now()

    class DummyVisit:
        def __init__(self, dt):
            self.visit_datetime = dt
            self.doctor_id = 1
            self.owner_id = 10
            self.animal_id = 15
            self.facility_id = 7
            self.notes = "Info"

    visits = [
        DummyVisit(now.replace(hour=9, minute=15)),
        DummyVisit(now.replace(hour=13, minute=0)),
        DummyVisit(now.replace(day=now.day-1, hour=12, minute=0)),
        DummyVisit(now.replace(day=now.day+1, hour=8, minute=30)),
    ]
    mock_appt.list.return_value = visits
    mock_doc.list.return_value = [DummyDoctor()]
    mock_client.list.return_value = [DummyClient()]
    mock_animal.list.return_value = [DummyAnimal()]
    mock_fac.list.return_value = [DummyFacility()]
    page = ReceptionistDashboardPage()
    # Sprawdź tabele
    assert page.past_table.rowCount() > 0
    assert page.today_table.rowCount() > 0
    assert page.upcoming_table.rowCount() > 0

@patch("vetclinic_gui.windows.Receptionist.dashboard.AppointmentService")
def test_receptionist_dashboard_error(mock_appt, app):
    from vetclinic_gui.windows.Receptionist.dashboard import ReceptionistDashboardPage
    mock_appt.list.side_effect = Exception("db error")
    with patch.object(QMessageBox, "critical") as critmock:
        ReceptionistDashboardPage()
        assert critmock.called
