import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication

pytestmark = pytest.mark.gui


@pytest.fixture(scope="session")
def app():
    return QApplication([])


@patch("vetclinic_gui.windows.Client.dashboard.AnimalService")
@patch("vetclinic_gui.windows.Client.dashboard.AppointmentService")
@patch("vetclinic_gui.windows.Client.dashboard.MedicalRecordService")
def test_dashboard_load_and_switch_animal(mock_med, mock_appt, mock_animal, app):
    from vetclinic_gui.windows.Client.dashboard import DashboardWindow

    class DummyAnimal:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    animals = [DummyAnimal(1, "Fafik"), DummyAnimal(2, "Pusia")]
    mock_animal.list_by_owner.return_value = animals

    class DummyAppt:
        def __init__(self, id, animal_id, dt, reason, notes, priority, doctor):
            self.id = id
            self.animal_id = animal_id
            self.visit_datetime = dt
            self.reason = reason
            self.notes = notes
            self.priority = priority
            self.doctor = doctor

    class DummyDoctor:
        def __init__(self):
            self.first_name = "Jan"
            self.last_name = "Nowak"

    import datetime

    now = datetime.datetime.now()
    appts = [
        DummyAppt(10, 1, now, "Kontrola", "Brak", "Wysoki", DummyDoctor()),
        DummyAppt(11, 1, now, "Szczepienie", "Notatka", "Niski", DummyDoctor()),
    ]
    mock_appt.list_by_owner.return_value = appts
    mock_med.list_by_appointment.return_value = [MagicMock(description="Opis testowy")]

    dashboard = DashboardWindow(client_id=1)
    assert dashboard.combo_animal.count() == 2
    assert dashboard.med_table.rowCount() == 2
    assert dashboard.med_table.item(0, 0).text() == "Opis testowy"
    assert dashboard.med_table.item(1, 0).text() == "Opis testowy"

    dashboard.combo_animal.setCurrentIndex(1)
    assert dashboard.animal_id == 2


@patch("vetclinic_gui.windows.Client.dashboard.AnimalService")
@patch("vetclinic_gui.windows.Client.dashboard.AppointmentService")
@patch("vetclinic_gui.windows.Client.dashboard.MedicalRecordService")
def test_dashboard_empty_state(mock_med, mock_appt, mock_animal, app):
    from vetclinic_gui.windows.Client.dashboard import DashboardWindow

    mock_animal.list_by_owner.return_value = []
    mock_appt.list_by_owner.return_value = []
    mock_med.list_by_appointment.return_value = []

    dashboard = DashboardWindow(client_id=1)
    assert dashboard.med_table.rowCount() == 0


@patch("vetclinic_gui.windows.Client.invoices.InvoiceService")
def test_invoices_load_and_display(mock_invoice, app):
    from vetclinic_gui.windows.Client.invoices import InvoicesWindow
    from datetime import datetime

    class DummyInvoice:
        def __init__(self, id, created_at, amount, status):
            self.id = id
            self.created_at = created_at
            self.amount = amount
            self.status = status

    invoices = [
        DummyInvoice(1, datetime(2024, 6, 10), 150.0, "unpaid"),
        DummyInvoice(2, datetime(2024, 6, 1), 300.0, "paid"),
    ]
    mock_invoice.list_by_client.return_value = invoices
    win = InvoicesWindow(client_id=1)
    assert win.table.rowCount() == 2
    assert win.table.item(0, 0).text() == "1"
    assert "PLN" in win.table.item(0, 2).text()

    mock_invoice.list_by_client.return_value = []
    win._load_invoices()
    win.show()
    assert win.table.isHidden()
    assert win.empty_label.isVisible()


@patch("vetclinic_gui.windows.Client.invoices.InvoiceService")
def test_invoices_invalid_data(mock_invoice, app):
    from vetclinic_gui.windows.Client.invoices import InvoicesWindow

    class DummyInvoice:
        def __init__(self):
            self.id = 1
            self.created_at = "xxxx"
            self.amount = "cos"
            self.status = None

    mock_invoice.list_by_client.return_value = [DummyInvoice()]
    win = InvoicesWindow(client_id=1)
    assert win.table.rowCount() == 1
    assert win.table.item(0, 1).text() == ""
    assert win.table.item(0, 2).text() == "cos"
