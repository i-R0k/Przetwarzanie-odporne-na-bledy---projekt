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
from vetclinic_gui.services.clients_service import ClientService

class RegistrationPage(QWidget):
    """
    Ekran do rejestracji nowego użytkownika (właściciela zwierzęcia).
    """
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id
        self._setup_ui()

    def _setup_ui(self):
        # __1__ całe tło na jasnoszary
        self.setStyleSheet("background-color: #F3F4F6;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # wpychamy kartę na środek pionowo
        main_layout.addStretch()

        # __2__ karta z białym tłem, zaokrąglonymi rogami i lekkim cieniem
        card = QFrame()
        card.setMaximumWidth(600)
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 8px;
                /* proste shadow (tylko border) – na Windowsie drop-shadow wymaga QGraphicsEffect */
                border: 1px solid rgba(0,0,0,0.07);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # __3__ tytuł karty
        title = QLabel("Rejestracja nowego klienta")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
        """)
        card_layout.addWidget(title)

        # __4__ formularz
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignCenter)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)

        # pola
        self.first_name_le  = QLineEdit()
        self.last_name_le   = QLineEdit()
        self.phone_le       = QLineEdit()
        self.email_le       = QLineEdit()
        self.address_le     = QLineEdit()
        self.postal_code_le = QLineEdit()

        # wspólny styl dla QLineEdit
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
        for le in (
            self.first_name_le, self.last_name_le,
            self.phone_le, self.email_le,
            self.address_le, self.postal_code_le
        ):
            le.setStyleSheet(le_style)

        form.addRow("Imię:",         self.first_name_le)
        form.addRow("Nazwisko:",     self.last_name_le)
        form.addRow("Telefon:",      self.phone_le)
        form.addRow("Email:",        self.email_le)
        form.addRow("Adres:",        self.address_le)
        form.addRow("Kod pocztowy:", self.postal_code_le)

        card_layout.addLayout(form)

        # __5__ przycisk
        self.register_btn = QPushButton("Zarejestruj użytkownika")
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
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
        """)
        self.register_btn.clicked.connect(self._on_register)

        # środek poziomo
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(self.register_btn)
        card_layout.addWidget(btn_container)

        # dodajemy kartę do głównego layoutu
        main_layout.addWidget(card, alignment=Qt.AlignHCenter)

        # i znowu stretch, żeby karta była wyśrodkowana
        main_layout.addStretch()

    def _on_register(self):
        # walidacja
        missing = []
        if not self.first_name_le.text().strip():  missing.append("Imię")
        if not self.last_name_le.text().strip():   missing.append("Nazwisko")
        if not self.phone_le.text().strip():       missing.append("Telefon")
        if not self.email_le.text().strip():       missing.append("Email")
        if not self.address_le.text().strip():     missing.append("Adres")
        if not self.postal_code_le.text().strip(): missing.append("Kod pocztowy")

        if missing:
            QMessageBox.warning(
                self, "Brak danych",
                "Uzupełnij pola:\n" + "\n".join(missing)
            )
            return

        payload = {
            "first_name":   self.first_name_le.text().strip(),
            "last_name":    self.last_name_le.text().strip(),
            "phone_number": self.phone_le.text().strip(),
            "email":        self.email_le.text().strip(),
            "address":      self.address_le.text().strip(),
            "postal_code":  self.postal_code_le.text().strip(),
        }

        try:
            ClientService.create(payload)
            QMessageBox.information(self, "Sukces", "Użytkownik został zarejestrowany.")
            for w in (
                self.first_name_le, self.last_name_le,
                self.phone_le, self.email_le,
                self.address_le, self.postal_code_le
            ):
                w.clear()
        except Exception as e:
            QMessageBox.critical(self, "Błąd rejestracji", str(e))
