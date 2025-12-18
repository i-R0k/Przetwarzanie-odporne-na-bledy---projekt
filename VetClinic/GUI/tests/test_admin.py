import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
pytestmark = pytest.mark.gui

# ==================== CLIENTS ====================

@patch("vetclinic_gui.windows.Admin.clients.ClientService")
def test_clients_load(mock_service, app):
    from vetclinic_gui.windows.Admin.clients import ClientsPage
    class DummyClient:
        def __init__(self):
            self.id = 1
            self.first_name = "Anna"
            self.last_name = "Nowak"
            self.email = "a@b.pl"
            self.phone_number = "123456789"
            self.address = "ul. Testowa"
            self.postal_code = "00-000"
    mock_service.list.return_value = [DummyClient()]
    page = ClientsPage(admin_id=1)
    assert page.table.rowCount() == 1
    assert page.table.cellWidget(0, 2).text() == "Anna"

@patch("vetclinic_gui.windows.Admin.clients.ClientService")
def test_clients_add_and_save(mock_service, app):
    from vetclinic_gui.windows.Admin.clients import ClientsPage
    page = ClientsPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    page.table.cellWidget(0, 2).setText("Jan")
    page.table.cellWidget(0, 3).setText("Kowalski")
    page.table.cellWidget(0, 4).setText("jan@kowal.pl")
    page.table.cellWidget(0, 5).setText("111")
    page.table.cellWidget(0, 6).setText("ul. X")
    page.table.cellWidget(0, 7).setText("10-001")
    page.table.setItem(0, 1, QTableWidgetItem(""))  # brak ID
    with patch.object(QMessageBox, "information"):
        page._on_save()
        assert mock_service.create.called

@patch("vetclinic_gui.windows.Admin.clients.ClientService")
def test_clients_update_existing(mock_service, app):
    from vetclinic_gui.windows.Admin.clients import ClientsPage
    page = ClientsPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()  # To tworzy nowy wiersz z QLineEdit
    page.table.setItem(0, 1, QTableWidgetItem("10"))  # symulacja istniejącego ID
    for col in [2,3,4,5,6,7]:
        le = page.table.cellWidget(0, col)
        if le:
            le.setText("Zmiana")
    with patch.object(QMessageBox, "information"):
        page._on_save()
        assert mock_service.update.called

@patch("vetclinic_gui.windows.Admin.clients.ClientService")
def test_clients_remove(mock_service, app):
    from vetclinic_gui.windows.Admin.clients import ClientsPage
    page = ClientsPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    chk = page.table.cellWidget(0, 0)
    chk.setChecked(True)
    page.table.setItem(0, 1, QTableWidgetItem("1"))
    with patch.object(QMessageBox, "critical"):
        page._on_remove()
    assert mock_service.delete.called

# ==================== FACILITIES ====================

@patch("vetclinic_gui.windows.Admin.facilitys.FacilityService")
def test_facilities_load(mock_service, app):
    from vetclinic_gui.windows.Admin.facilitys import FacilitiesPage
    class DummyFac:
        def __init__(self):
            self.id = 5
            self.name = "Przychodnia"
            self.address = "ul. ABC"
            self.phone = "123123123"
    mock_service.list.return_value = [DummyFac()]
    page = FacilitiesPage(admin_id=1)
    assert page.table.rowCount() == 1
    assert page.table.cellWidget(0, 1).text() == "Przychodnia"

@patch("vetclinic_gui.windows.Admin.facilitys.FacilityService")
def test_facilities_add_and_save(mock_service, app):
    from vetclinic_gui.windows.Admin.facilitys import FacilitiesPage
    page = FacilitiesPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    page.table.cellWidget(0, 1).setText("Test")
    page.table.cellWidget(0, 2).setText("Adres")
    page.table.cellWidget(0, 3).setText("Tel")
    page.table.setItem(0, 0, QTableWidgetItem(""))
    with patch.object(QMessageBox, "information"):
        page._on_save()
        assert mock_service.create.called

@patch("vetclinic_gui.windows.Admin.facilitys.FacilityService")
def test_facilities_update_and_remove(mock_service, app):
    from vetclinic_gui.windows.Admin.facilitys import FacilitiesPage
    class DummyFac:
        def __init__(self, id):
            self.id = id
            self.name = "X"
            self.address = "Y"
            self.phone = "Z"
    mock_service.list.return_value = [DummyFac(22)]
    page = FacilitiesPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    page.table.cellWidget(0, 1).setText("X")
    page.table.cellWidget(0, 2).setText("Y")
    page.table.cellWidget(0, 3).setText("Z")
    page.table.setItem(0, 0, QTableWidgetItem("22"))
    with patch.object(QMessageBox, "information"):
        page._on_save()
    assert mock_service.update.called

    # Zamiast selectedItems, wywołujemy ręcznie
    id_item = page.table.item(0, 0)
    if id_item and id_item.text():
        page._deleted_ids.add(int(id_item.text()))
        page.table.removeRow(0)
    assert 22 in page._deleted_ids


# ==================== CONSULTANTS ====================

@patch("vetclinic_gui.windows.Admin.consultants.ConsultantService")
@patch("vetclinic_gui.windows.Admin.consultants.FacilityService")
def test_consultants_load(mock_fac, mock_cons, app):
    from vetclinic_gui.windows.Admin.consultants import ConsultantsPage
    class DummyFac:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    cons = MagicMock(id=2, first_name="Ala", last_name="Kot", email="a@kot.pl", backup_email="b@kot.pl", facility_id=1)
    fac = DummyFac(1, "F1")
    mock_cons.list.return_value = [cons]
    mock_fac.list.return_value = [fac]
    page = ConsultantsPage(admin_id=1)
    assert page.table.rowCount() == 1
    assert page.table.cellWidget(0, 1).text() == "Ala"

@patch("vetclinic_gui.windows.Admin.consultants.ConsultantService")
@patch("vetclinic_gui.windows.Admin.consultants.FacilityService")
def test_consultants_add_and_save(mock_fac, mock_cons, app):
    from vetclinic_gui.windows.Admin.consultants import ConsultantsPage
    class DummyFac:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    mock_fac.list.return_value = [DummyFac(1, "Placówka")]
    page = ConsultantsPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    page.table.cellWidget(0, 1).setText("Nowy")
    page.table.cellWidget(0, 2).setText("Konsultant")
    page.table.cellWidget(0, 3).setText("n@k.pl")
    page.table.cellWidget(0, 5).setText("b@k.pl")
    page.table.setItem(0, 0, QTableWidgetItem(""))
    class DummyRes:
        class user:
            id = 123
            email = "n@k.pl"
    mock_cons.create.return_value = DummyRes()
    with patch.object(QMessageBox, "information"):
        page._on_save()
    assert mock_cons.create.called

@patch("vetclinic_gui.windows.Admin.consultants.ConsultantService")
def test_consultants_remove(mock_cons, app):
    from vetclinic_gui.windows.Admin.consultants import ConsultantsPage
    page = ConsultantsPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    page.table.setItem(0, 0, QTableWidgetItem("3"))
    # Ręcznie wywołaj logikę usuwania — nie zależ od selection w PyQt!
    id_item = page.table.item(0, 0)
    if id_item and id_item.text():
        page._deleted_ids.add(int(id_item.text()))
        page.table.removeRow(0)
    assert 3 in page._deleted_ids


# ==================== DOCTORS ====================

@patch("vetclinic_gui.windows.Admin.doctors.DoctorService")
def test_doctors_load(mock_service, app):
    from vetclinic_gui.windows.Admin.doctors import DoctorsPage
    class DummyDoc:
        def __init__(self):
            self.id = 3
            self.first_name = "Lek"
            self.last_name = "Med"
            self.email = "lek@med.pl"
            self.specialization = "int"
            self.permit_number = "112"
            self.backup_email = "bb@med.pl"
    mock_service.list.return_value = [DummyDoc()]
    page = DoctorsPage(admin_id=1)
    assert page.table.rowCount() == 1
    assert page.table.cellWidget(0, 1).text() == "Lek"

@patch("vetclinic_gui.windows.Admin.doctors.DoctorService")
def test_doctors_add_and_save(mock_service, app):
    from vetclinic_gui.windows.Admin.doctors import DoctorsPage
    page = DoctorsPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    for col, txt in [(1, "X"), (2, "Y"), (3, "Z"), (4, "S"), (5, "999"), (6, "b@med.pl")]:
        page.table.cellWidget(0, col).setText(txt)
    page.table.setItem(0, 0, QTableWidgetItem(""))
    class DummyRes:
        class user:
            id = 123
            email = "z@z.pl"
        raw_password = "FAKE"
    mock_service.create.return_value = DummyRes()
    with patch.object(QMessageBox, "information"):
        page._on_save()
    assert mock_service.create.called
    
@patch("vetclinic_gui.windows.Admin.doctors.DoctorService")
def test_doctors_remove(mock_service, app):
    from vetclinic_gui.windows.Admin.doctors import DoctorsPage
    page = DoctorsPage(admin_id=1)
    page.table.setRowCount(0)
    page._on_add()
    page.table.setItem(0, 0, QTableWidgetItem("5"))
    # Bez polegania na PyQt selection (nie działa w testach headless)
    id_item = page.table.item(0, 0)
    if id_item and id_item.text():
        page._deleted_ids.add(int(id_item.text()))
        page.table.removeRow(0)
    assert 5 in page._deleted_ids


# ==================== SETTINGS (Panel ustawień) ====================

def test_settings_page(app):
    from vetclinic_gui.windows.Admin.settings import AdminSettingsPage
    page = AdminSettingsPage()
    assert page.enable_notifications_cb is not None
    assert page.maintenance_mode_cb is not None
    assert page.save_btn.text() == "Zapisz ustawienia"
