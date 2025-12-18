from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QMessageBox,
    QFrame,
    QSizePolicy,
)
from vetclinic_gui.qt_compat import Qt
import json
from vetclinic_gui.services.doctors_service import DoctorService

class DoctorRegistrationPage(QWidget):
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._setup_ui()

    def _setup_ui(self):
        # całość tła
        self.setStyleSheet("background-color: #F3F4F6;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addStretch()

        # karta
        card = QFrame()
        card.setMaximumWidth(600)
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid rgba(0,0,0,0.07);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24,24,24,24)
        card_layout.setSpacing(16)

        # tytuł
        title = QLabel("Rejestracja nowego lekarza")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
        """)
        card_layout.addWidget(title)

        # formularz
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignCenter)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)

        # pola
        self.first_name_le   = QLineEdit()
        self.last_name_le    = QLineEdit()
        self.email_le        = QLineEdit()
        self.backup_email_le = QLineEdit()
        self.spec_le         = QLineEdit()
        self.permit_le       = QLineEdit()

        # email readonly
        self.email_le.setReadOnly(True)

        # wspólny styl
        le_style = """
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #374151;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
            }
        """
        for w in (
            self.first_name_le, self.last_name_le,
            self.email_le, self.backup_email_le,
            self.spec_le, self.permit_le
        ):
            w.setStyleSheet(le_style)

        self.first_name_le.setPlaceholderText("Imię")
        self.last_name_le.setPlaceholderText("Nazwisko")
        self.backup_email_le.setPlaceholderText("np. name@domain.com")
        self.spec_le.setPlaceholderText("Specjalizacja")
        self.permit_le.setPlaceholderText("Nr pozwolenia")

        form.addRow("Imię:",           self.first_name_le)
        form.addRow("Nazwisko:",       self.last_name_le)
        form.addRow("Email:",          self.email_le)
        form.addRow("Backup Email:",   self.backup_email_le)
        form.addRow("Specjalizacja:",  self.spec_le)
        form.addRow("Nr pozwolenia:",  self.permit_le)

        card_layout.addLayout(form)

        # przycisk
        self.register_btn = QPushButton("Zarejestruj lekarza")
        self.register_btn.setFixedHeight(40)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 24px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        card_layout.addWidget(self.register_btn, alignment=Qt.AlignHCenter)

        # dodaj kartę
        main_layout.addWidget(card, alignment=Qt.AlignHCenter)
        main_layout.addStretch()

        # sygnały
        self.first_name_le.textChanged.connect(self._update_email)
        self.last_name_le.textChanged.connect(self._update_email)
        self.register_btn.clicked.connect(self._on_register)

    def _update_email(self):
        """Generuj unikalny email w locie."""
        fn = self.first_name_le.text().strip().lower()
        ln = self.last_name_le.text().strip().lower()
        if not fn or not ln:
            self.email_le.clear()
            return

        domain = "@lekarz.vetclinic.com"
        exists = {d.email for d in DoctorService.list() or []}

        candidates = [f"{fn[0]}.{ln}", f"{fn[0]}{ln}"]

        for i in range(2, len(fn)+1):
            candidates.append(f"{fn[:i]}.{ln}")
            candidates.append(f"{fn[:i]}{ln}")

        suffix = 1
        base = f"{fn[0]}.{ln}"
        while True:
            candidates.append(f"{base}{suffix}")
            suffix += 1
            if suffix > 10:
                break

        # wybierz pierwszą wolną
        for prefix in candidates:
            email = prefix + domain
            if email not in exists:
                self.email_le.setText(email)
                return

        self.email_le.setText(f"{fn}.{ln}{domain}")

    def _on_register(self):
        missing = []
        if not self.first_name_le.text().strip(): missing.append("Imię")
        if not self.last_name_le.text().strip():  missing.append("Nazwisko")
        if not self.email_le.text().strip():      missing.append("Email")
        if not self.spec_le.text().strip():       missing.append("Specjalizacja")
        if not self.permit_le.text().strip():     missing.append("Nr pozwolenia")
        if not self.backup_email_le.text().strip(): missing.append("Backup email")
    
        if missing:
            QMessageBox.warning(
                self, "Brak danych",
                "Uzupełnij pola:\n" + "\n".join(missing)
            )
            return
    
        payload = {
            "first_name": self.first_name_le.text().strip(),
            "last_name": self.last_name_le.text().strip(),
            "specialization": self.spec_le.text().strip(),
            "permit_number": self.permit_le.text().strip(),
            "backup_email": self.backup_email_le.text().strip()
        }
    
        print("Przekazywany payload do API:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))   # <<< DEBUG
    
        try:
            doctor = DoctorService.create(payload)
            QMessageBox.information(
                self, "Sukces",
                f"Do bazy dodano lekarza {doctor.first_name} {doctor.last_name}\n"
                f"Email: {doctor.email}\nTymczasowe hasło wysłano na {payload['backup_email']}"
            )
            # wyczyść pola…
        except Exception as e:
            QMessageBox.critical(self, "Błąd rejestracji", str(e))
