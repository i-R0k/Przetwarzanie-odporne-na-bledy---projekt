from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)
from vetclinic_gui.qt_compat import Qt
from datetime import date

from vetclinic_gui.services.clients_service    import ClientService
from vetclinic_gui.services.animals_service    import AnimalService
from vetclinic_gui.services.facility_service   import FacilityService
from vetclinic_gui.services.doctors_service    import DoctorService
from vetclinic_gui.services.appointments_service import AppointmentService


class ReceptionistDashboardPage(QWidget):
    """
    Dashboard recepcjonisty - przegląd wizyt: przeszłe, dzisiejsze i przyszłe.
    Pokazuje w tabeli (dla każdej kategorii) kolumny:
      Data | Godzina | Lekarz | Właściciel | Zwierzę | Placówka | Uwagi
    Estetyka: naprzemienne kolory wierszy i nagłówki przyciągające wzrok.
    """
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id
        self._setup_ui()
        self._load_visits()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Przegląd wizyt")
        title.setStyleSheet("font-size:20px; font-weight:bold; margin-bottom:12px;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 16px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #e0f0ff;
                border-bottom: 2px solid #2196F3;
            }
        """)

        # Tabele dla trzech kategorii wizyt; kolumny: Data, Godzina, Lekarz, Właściciel, Zwierzę, Placówka, Uwagi
        self.past_table     = self._create_table()
        self.today_table    = self._create_table()
        self.upcoming_table = self._create_table()

        headers = ["Data", "Godzina", "Lekarz", "Właściciel", "Zwierzę", "Placówka", "Uwagi"]
        for tbl in (self.past_table, self.today_table, self.upcoming_table):
            tbl.setColumnCount(len(headers))
            tbl.setHorizontalHeaderLabels(headers)
            tbl.setAlternatingRowColors(True)
            tbl.setStyleSheet("""
                QTableWidget {
                    background-color: #fafafa;
                    alternate-background-color: #f0f0f0;
                }
                QHeaderView::section {
                    background-color: #2196F3;
                    color: white;
                    padding: 4px;
                    font-weight: bold;
                    border: 1px solid #e0e0e0;
                }
            """)
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.verticalHeader().setVisible(False)

        self.tabs.addTab(self.past_table, "Przeszłe")
        self.tabs.addTab(self.today_table, "Dzisiejsze")
        self.tabs.addTab(self.upcoming_table, "Przyszłe")
        layout.addWidget(self.tabs)

    def _create_table(self) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setRowCount(0)
        tbl.setColumnCount(7)
        return tbl

    def _load_visits(self):
        try:
            all_visits = AppointmentService.list()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można pobrać wizyt: {e}")
            return

        today_date = date.today()

        doctors     = {d.id: f"{d.first_name} {d.last_name}" for d in DoctorService.list() or []}
        clients     = {c.id: f"{c.first_name} {c.last_name}" for c in ClientService.list() or []}
        animals     = {a.id: a.name                              for a in AnimalService.list() or []}
        facilities  = {f.id: f.name                              for f in FacilityService.list() or []}

        for tbl in (self.past_table, self.today_table, self.upcoming_table):
            tbl.setRowCount(0)

        for v in all_visits:
            dt = v.visit_datetime
            if not dt:
                continue

            # Wybór odpowiedniej tabeli
            if dt.date() < today_date:
                tbl = self.past_table
            elif dt.date() == today_date:
                tbl = self.today_table
            else:
                tbl = self.upcoming_table

            row = tbl.rowCount()
            tbl.insertRow(row)

            # Przygotuj wartości:
            date_str     = dt.date().isoformat()       # np. "2025-06-10"
            time_str     = dt.strftime("%H:%M")        # np. "09:15"
            doctor_name  = doctors.get(v.doctor_id, "")
            owner_name   = clients.get(v.owner_id, "")
            animal_name  = animals.get(v.animal_id, "")
            facility_name= facilities.get(v.facility_id, "")
            notes        = v.notes or ""

            values = [
                date_str,
                time_str,
                doctor_name,
                owner_name,
                animal_name,
                facility_name,
                notes
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                tbl.setItem(row, col, item)
