from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget,
    QFrame, QLabel
)

from .Admin.settings import AdminSettingsPage
from .Admin.facilitys import FacilitiesPage
from .Admin.consultants import ConsultantsPage
from .Admin.doctors import DoctorsPage
from .Admin.clients import ClientsPage

from .Receptionist.dashboard import ReceptionistDashboardPage
from .Receptionist.client_registration import RegistrationPage
from .Receptionist.animal_registration import AnimalRegistrationPage
from .Receptionist.appointment_add  import AppointmentBookingPage
from .Receptionist.doctor_registration import DoctorRegistrationPage

from .Doctor.dashboard import DashboardPage
from .Doctor.visit import VisitsWindow

from .Client.dashboard import DashboardWindow
from .Client.invoices import InvoicesWindow
from vetclinic_gui.cluster_admin_widget import ClusterAdminWidget

class MainWindow(QMainWindow):
    def __init__(
        self,
        user_role: str,
        doctor_id: int = None,
        receptionist_id: int = None,
        client_id: int = None,
    ):
        super().__init__()
        self.user_role = user_role
        self.doctor_id = doctor_id
        self.receptionist_id = receptionist_id
        self.client_id = client_id
        self.pages_map = {}
        self.setWindowTitle("VetClinic")
        self.setMinimumSize(1080, 720)
        self._setup_ui()
        self.showMaximized()

    def _setup_ui(self):
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        self.pages = QStackedWidget()

        # 1) Zawsze inicjalizujemy pages
        pages = []

        # 2) Wypełniamy w zależności od roli
        if self.user_role == "admin":
            pages = [
                ("Ustawienia", AdminSettingsPage),
                ("Placówki", FacilitiesPage),
                ("Konsultanci", ConsultantsPage),
                ("Lekarze", DoctorsPage),
                ("Klienci", ClientsPage),
                ("Sieć / Blockchain", ClusterAdminWidget),
            ]
        elif self.user_role == "receptionist":
            pages = [
                ("Dashboard", ReceptionistDashboardPage),
                ("Umawianie wizyt", AppointmentBookingPage),
                ("Rejestracja klienta", RegistrationPage),
                ("Rejestracja zwierzaka", AnimalRegistrationPage),
                ("Rejestracja lekarza", DoctorRegistrationPage),
            ]
        elif self.user_role == "doctor":
            pages = [
                ("Dashboard", DashboardPage),
                ("Wizyty", VisitsWindow),
            ]
        elif self.user_role == "client":
            pages = [
                ("Dashboard", DashboardWindow),
                ("Płatności", InvoicesWindow),
            ]
        else:
            # 3) Jeśli trafi tu nieoczekiwana rola, od razu wiadomo dlaczego
            raise ValueError(f"Nieobsługiwana rola użytkownika: {self.user_role}")

        # 4) Tworzenie przycisków sidebaru i stron
        for label, page_factory in pages:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet(
                "QPushButton { text-align:left; padding:8px; color:#ffffff; font-size:16px; }"
                "QPushButton:hover { background-color: #2e3a50; }"
            )
            btn.clicked.connect(lambda _, l=label: self._navigate_to(l))
            sidebar.layout().addWidget(btn)

            # instancjonowanie strony z odpowiednimi parametrami
            if page_factory is VisitsWindow:
                page = page_factory(self.doctor_id)
            elif page_factory in (ReceptionistDashboardPage, RegistrationPage):
                page = page_factory(self.receptionist_id)
            elif page_factory is DashboardWindow:
                page = page_factory(self.client_id)
            elif page_factory is InvoicesWindow:
                page = page_factory(self.client_id)
            else:
                page = page_factory()

            idx = self.pages.count()
            self.pages.addWidget(page)
            self.pages_map[label] = idx

        sidebar.layout().addStretch()
        main_layout.addWidget(self.pages)
        self.setCentralWidget(container)

        # 5) Domyślnie pokazujemy pierwszą stronę
        if self.pages.count() > 0:
            self.pages.setCurrentIndex(0)


    def _create_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(260)
        frame.setStyleSheet("background-color: #2f3b52;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        logo = QLabel(
            "<span style='font-size:24px; font-weight:bold; color:#ffffff;'>"
            "Vet<span style='color:#38a2db;'>Clinic</span></span>"
        )
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        return frame

    def _navigate_to(self, label: str):
        idx = self.pages_map.get(label)
        if idx is not None:
            self.pages.setCurrentIndex(idx)
