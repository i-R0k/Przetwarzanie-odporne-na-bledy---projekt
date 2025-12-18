import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
pytestmark = pytest.mark.gui

import gc
import pytest

@pytest.fixture(autouse=True)
def cleanup_qt_widgets():
    yield
    # Wymuś zbieranie śmieci i zamknięcie okien po każdym teście
    import PyQt6.QtWidgets
    for widget in PyQt6.QtWidgets.QApplication.allWidgets():
        try:
            widget.close()
        except Exception:
            pass
    gc.collect()


# ====================== DASHBOARD ======================
@patch("vetclinic_gui.windows.Doctor.dashboard.AnimalService")
@patch("vetclinic_gui.windows.Doctor.dashboard.ClientService")
@patch("vetclinic_gui.windows.Doctor.dashboard.AppointmentService")
def test_dashboard_upcoming_and_previous_visits(mock_appt, mock_client, mock_animal, app):
    from vetclinic_gui.windows.Doctor.dashboard import DashboardPage
    import datetime

    # Dummy dane
    class DummyAnimal:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    animals = [DummyAnimal(1, "Reksio"), DummyAnimal(2, "Pusia")]
    mock_animal.list.return_value = animals

    class DummyClient:
        def __init__(self, id, first, last):
            self.id = id
            self.first_name = first
            self.last_name = last
    clients = [DummyClient(11, "Anna", "Nowak"), DummyClient(12, "Paweł", "Kot")]
    mock_client.list.return_value = clients

    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    class DummyVisit:
        def __init__(self, id, animal_id, owner_id, visit_datetime, reason, notes, priority):
            self.id = id
            self.animal_id = animal_id
            self.owner_id = owner_id
            self.visit_datetime = visit_datetime
            self.reason = reason
            self.notes = notes
            self.priority = priority

    # Jeden w przyszłości, jeden w przeszłości
    visits = [
        DummyVisit(1, 1, 11, tomorrow, "Szczepienie", "Uwaga 1", "pilna"),
        DummyVisit(2, 2, 12, yesterday, "Kontrola", "", "nagła"),
    ]
    mock_appt.list.return_value = visits

    dash = DashboardPage()
    # Sprawdź sekcje wizyt
    # --- Nadchodzące
    up_group = dash._create_upcoming_visits()
    up_table = up_group.findChild(
        type(dash), QTableWidgetItem, options=Qt.FindChildOption.FindChildrenRecursively
    )
    assert up_group is not None
    # --- Poprzednie
    prev_group = dash._create_previous_visits()
    assert prev_group is not None
    # --- Statystyki
    stats_group = dash._create_appointments_stats()
    assert stats_group is not None@patch("vetclinic_gui.windows.Doctor.dashboard.AnimalService")

@patch("vetclinic_gui.windows.Doctor.dashboard.AnimalService")
@patch("vetclinic_gui.windows.Doctor.dashboard.ClientService")
@patch("vetclinic_gui.windows.Doctor.dashboard.AppointmentService")
def test_dashboard_upcoming_and_previous_visits(mock_appt, mock_client, mock_animal, app):
    from vetclinic_gui.windows.Doctor.dashboard import DashboardPage
    from PyQt6.QtWidgets import QTableWidget
    import datetime

    # Dummy dane
    class DummyAnimal:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    animals = [DummyAnimal(1, "Reksio"), DummyAnimal(2, "Pusia")]
    mock_animal.list.return_value = animals

    class DummyClient:
        def __init__(self, id, first, last):
            self.id = id
            self.first_name = first
            self.last_name = last
    clients = [DummyClient(11, "Anna", "Nowak"), DummyClient(12, "Paweł", "Kot")]
    mock_client.list.return_value = clients

    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    class DummyVisit:
        def __init__(self, id, animal_id, owner_id, visit_datetime, reason, notes, priority):
            self.id = id
            self.animal_id = animal_id
            self.owner_id = owner_id
            self.visit_datetime = visit_datetime
            self.reason = reason
            self.notes = notes
            self.priority = priority

    visits = [
        DummyVisit(1, 1, 11, tomorrow, "Szczepienie", "Uwaga 1", "pilna"),
        DummyVisit(2, 2, 12, yesterday, "Kontrola", "", "nagła"),
    ]
    mock_appt.list.return_value = visits

    dash = DashboardPage()   # <-- teraz po mockowaniu!
    # --- Nadchodzące
    up_group = dash._create_upcoming_visits()
    tables = up_group.findChildren(QTableWidget)
    assert tables and tables[0].rowCount() > 0

    # --- Poprzednie
    prev_group = dash._create_previous_visits()
    tables_prev = prev_group.findChildren(QTableWidget)
    assert tables_prev and tables_prev[0].rowCount() > 0

    # --- Statystyki
    stats_group = dash._create_appointments_stats()
    assert stats_group is not None


@patch("vetclinic_gui.windows.Doctor.dashboard.AppointmentService")
def test_dashboard_upcoming_visits_error(mock_appt, app):
    from vetclinic_gui.windows.Doctor.dashboard import DashboardPage
    # Simuluj błąd pobierania
    mock_appt.list.side_effect = Exception("DB error")
    dash = DashboardPage()
    up_group = dash._create_upcoming_visits()
    assert up_group is not None
    prev_group = dash._create_previous_visits()
    assert prev_group is not None

# ====================== VISITS WINDOW ======================

@patch("vetclinic_gui.windows.Doctor.visit.DoctorService")
@patch("vetclinic_gui.windows.Doctor.visit.ClientService")
@patch("vetclinic_gui.windows.Doctor.visit.AnimalService")
@patch("vetclinic_gui.windows.Doctor.visit.AppointmentService")
def test_visits_window_loading_and_editing(mock_appt, mock_animal, mock_client, mock_doc, app):
    from vetclinic_gui.windows.Doctor.visit import VisitsWindow
    import datetime

    # Mock lekarz z facility_id
    class DummyDoc:
        def __init__(self, id, facility_id):
            self.id = id
            self.facility_id = facility_id
    mock_doc.get.return_value = DummyDoc(1, 77)

    # Mock klienci
    class DummyClient:
        def __init__(self, id, first, last):
            self.id = id
            self.first_name = first
            self.last_name = last
    clients = [DummyClient(21, "Anna", "Nowak")]
    mock_client.list.return_value = clients

    # Mock zwierzęta
    class DummyAnimal:
        def __init__(self, id, owner_id, name, gender, age, weight, species, breed, birth_date, microchip, notes):
            self.id = id
            self.owner_id = owner_id
            self.name = name
            self.gender = gender
            self.age = age
            self.weight = weight
            self.species = species
            self.breed = breed
            self.birth_date = birth_date
            self.microchip_number = microchip
            self.notes = notes
    import datetime
    dt = datetime.date(2023,1,1)
    animals = [DummyAnimal(101, 21, "Rex", "samiec", 4, 23.5, "pies", "owczarek", dt, "chipX", "notatka")]
    mock_animal.list.return_value = animals

    # Mock wizyty
    class DummyVisit:
        def __init__(self):
            self.id = 99
            self.animal_id = 101
            self.owner_id = 21
            self.doctor_id = 1
            self.visit_datetime = datetime.datetime(2023, 6, 15, 12, 0)  # ← tutaj
            self.weight = 23.5
            self.reason = "Wizyta kontrolna"
            self.treatment = "Leczenie"
            self.priority = "nagła"

    mock_appt.list.return_value = [DummyVisit()]
    mock_appt.get.return_value = DummyVisit()

    win = VisitsWindow(doctor_id=1)
    assert win.client_cb.count() == 1
    assert win.animal_cb.count() == 1
    # symuluj edycję wizyty
    win._on_edit_visit(0, 0)
    assert hasattr(win, "editing_id")
    assert win.reason_te.toPlainText() == "Wizyta kontrolna"

@patch("vetclinic_gui.windows.Doctor.visit.DoctorService")
@patch("vetclinic_gui.windows.Doctor.visit.ClientService")
@patch("vetclinic_gui.windows.Doctor.visit.AnimalService")
@patch("vetclinic_gui.windows.Doctor.visit.AppointmentService")
def test_visits_window_save(mock_appt, mock_animal, mock_client, mock_doc, app):
    from vetclinic_gui.windows.Doctor.visit import VisitsWindow
    import datetime

    # Dummy dane lekarza, pacjenta, zwierzęcia
    class DummyDoc: facility_id = 1
    mock_doc.get.return_value = DummyDoc()
    class DummyClient:
        def __init__(self, id, first, last): self.id = id; self.first_name = first; self.last_name = last
    mock_client.list.return_value = [DummyClient(10, "A", "B")]
    class DummyAnimal:
        def __init__(self): self.id = 101; self.owner_id = 10; self.name = "Max"; self.gender = "samiec"; self.age = 5; self.weight = 8.1; self.species = "pies"; self.breed = "mieszaniec"; self.birth_date = datetime.date(2020,5,4); self.microchip_number = "xyz"; self.notes = ""
    mock_animal.list.return_value = [DummyAnimal()]
    class DummyVisit:
        def __init__(self): self.id = 1; self.animal_id = 101; self.owner_id = 10; self.doctor_id = 1; self.visit_datetime = "2024-06-10 13:15"; self.weight = 8.1; self.reason = "Szczepienie"; self.treatment = "Szczepionka"; self.priority = "pilna"
    mock_appt.list.return_value = [DummyVisit()]

    win = VisitsWindow(doctor_id=1)
    win.reason_te.setPlainText("Nowy powód")
    win.treatment_te.setPlainText("Nowe leczenie")
    win.weight_visit_sb.setValue(12.5)
    win.age_visit_sb.setValue(7)
    win.priority_cb.setCurrentText("nagła")
    # Wywołaj zapis
    with patch.object(QMessageBox, "information"):
        win._on_save_visit()
    assert mock_appt.create.called or mock_appt.update.called

@patch("vetclinic_gui.windows.Doctor.visit.DoctorService")
@patch("vetclinic_gui.windows.Doctor.visit.ClientService")
@patch("vetclinic_gui.windows.Doctor.visit.AnimalService")
@patch("vetclinic_gui.windows.Doctor.visit.AppointmentService")
def test_visits_filter_and_completer(mock_appt, mock_animal, mock_client, mock_doc, app):
    from vetclinic_gui.windows.Doctor.visit import VisitsWindow
    import datetime

    # Dane
    class DummyDoc: facility_id = 1
    mock_doc.get.return_value = DummyDoc()
    class DummyClient:
        def __init__(self, id, first, last): self.id = id; self.first_name = first; self.last_name = last
    clients = [DummyClient(1, "A", "Kowalski"), DummyClient(2, "B", "Nowak")]
    mock_client.list.return_value = clients
    class DummyAnimal:
        def __init__(self, id, owner_id, name): self.id = id; self.owner_id = owner_id; self.name = name; self.gender = "samica"; self.age = 3; self.weight = 5.0; self.species = "kot"; self.breed = "syjamski"; self.birth_date = datetime.date(2022,2,2); self.microchip_number = ""; self.notes = ""
    animals = [DummyAnimal(10, 1, "Puszek"), DummyAnimal(11, 2, "Fiona")]
    mock_animal.list.return_value = animals
    class DummyVisit: id=1; animal_id=10; owner_id=1; doctor_id=1; visit_datetime="2024-07-03 11:11"; weight=5.0; reason="Badanie"; treatment=""; priority="normalna"
    mock_appt.list.return_value = [DummyVisit()]

    win = VisitsWindow(doctor_id=1)
    # Filtrowanie po nazwisku właściciela
    win.search_le.setText("Kowal")
    assert win.client_cb.count() == 1
    # Szybkie wybieranie przez completer (symulacja)
    win._on_owner_selected("A Kowalski")
    assert win.client_cb.currentText() == "A Kowalski"
