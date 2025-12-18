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
    QDateEdit,
    QComboBox,
    QCompleter,
    QTextEdit,
)
from vetclinic_gui.qt_compat import Qt
from PyQt6.QtCore import QDate, QStringListModel
from PyQt6.QtGui import QColor

from vetclinic_gui.services.clients_service   import ClientService
from vetclinic_gui.services.animals_service   import AnimalService
from vetclinic_gui.services.facility_service  import FacilityService
from vetclinic_gui.services.doctors_service   import DoctorService
from vetclinic_gui.services.appointments_service import AppointmentService


class AppointmentBookingPage(QWidget):
    """
    Ekran do umawiania nowej wizyty, z:
      - wyborem klienta (autocomplete)
      - wyborem zwierzęcia (po kliencie)
      - wyborem placówki
      - wyborem priorytetu (normalna/pilna/nagła – kolorowane)
      - wyborem lekarza (autocomplete)
      - wyborem daty (QDateEdit)
      - wyborem godziny w kwadransach (QComboBox, wolne sloty pobrane z backendu)
      - uwagami (QTextEdit)
    """
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id      = receptionist_id
        self._clients             = ClientService.list()  or []
        self._doctors             = DoctorService.list()  or []
        self._selected_client_id  = None
        self._selected_doctor_id  = None
        self._selected_facility_id = None

        self._setup_ui()
        self._populate_client_completer()
        self._populate_doctor_completer()


    def _setup_ui(self):
        # === tło ===
        self.setStyleSheet("background-color: #F3F4F6;")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch()

        # === karta ===
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
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        # === tytuł ===
        title = QLabel("Umawianie nowej wizyty")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#1F2937;")
        lay.addWidget(title)

        # === formularz ===
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignCenter)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)

        # — Klient z autouzupełnianiem —
        self.client_le = QLineEdit()
        self.client_le.setPlaceholderText("🔍 Wyszukaj klienta...")
        self._client_model     = QStringListModel(self)
        self._client_completer = QCompleter(self._client_model, self.client_le)
        self._client_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._client_completer.setFilterMode(Qt.MatchContains)
        self._client_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._client_completer.activated[str].connect(self._on_client_chosen)
        self.client_le.setCompleter(self._client_completer)
        self.client_le.textEdited.connect(self._filter_clients)
        form.addRow("Klient:", self.client_le)

        # — Zwierzęta (po wybraniu klienta) —
        self.animal_cb = QComboBox()
        self.animal_cb.setEnabled(False)
        form.addRow("Zwierzę:", self.animal_cb)

        # — Placówka —
        self.facility_cb = QComboBox()
        self.facility_cb.addItem("– wybierz –", None)
        for f in FacilityService.list():
            self.facility_cb.addItem(f.name, f.id)
        # Aktualizacja wybranego ID oraz ewentualne odświeżenie slotów
        self.facility_cb.currentIndexChanged.connect(self._on_facility_changed)
        form.addRow("Placówka:", self.facility_cb)

        # — Priorytet wizyty —
        self.priority_cb = QComboBox()
        self.priority_cb.addItem("normalna", "normalna")
        self.priority_cb.addItem("pilna",   "pilna")
        self.priority_cb.addItem("nagła",   "nagła")
        self.priority_cb.setItemData(0, QColor("green"),  Qt.ForegroundRole)
        self.priority_cb.setItemData(1, QColor("orange"), Qt.ForegroundRole)
        self.priority_cb.setItemData(2, QColor("red"),    Qt.ForegroundRole)
        self.priority_cb.setCurrentIndex(0)
        form.addRow("Priorytet:", self.priority_cb)

        # — Lekarz z autouzupełnianiem —
        self.doctor_le = QLineEdit()
        self.doctor_le.setPlaceholderText("🔍 Wyszukaj lekarza...")
        self._doctor_model     = QStringListModel(self)
        self._doctor_completer = QCompleter(self._doctor_model, self.doctor_le)
        self._doctor_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._doctor_completer.setFilterMode(Qt.MatchContains)
        self._doctor_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._doctor_completer.activated[str].connect(self._on_doctor_chosen)
        self.doctor_le.setCompleter(self._doctor_completer)
        self.doctor_le.textEdited.connect(self._filter_doctors)
        self.doctor_le.setEnabled(False)
        form.addRow("Lekarz:", self.doctor_le)

        # — Data wizyty (QDateEdit) —
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        # ogranicz wybór do pon-sob, ale Qt nie ma gotowej opcji; na razie tylko blokuj przeszłość
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self._update_time_slots)
        form.addRow("Data wizyty:", self.date_edit)

        # — Godzina wizyty (QComboBox, generowany dynamicznie) —
        self.time_cb = QComboBox()
        self.time_cb.setEnabled(False)
        form.addRow("Godzina (kwadrans):", self.time_cb)

        # — Uwagi —
        self.notes_te = QTextEdit()
        self.notes_te.setFixedHeight(60)
        form.addRow("Uwagi:", self.notes_te)

        lay.addLayout(form)

        # === przycisk zapisu ===
        btn = QPushButton("Zapisz wizytę")
        btn.setFixedHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color:#FFF;
                font-size:16px; font-weight:bold;
                border:none; border-radius:6px;
                padding:0 24px;
            }
            QPushButton:hover { background-color:#1D4ED8; }
            QPushButton:pressed { background-color:#1E40AF; }
        """)
        btn.clicked.connect(self._on_save)

        ctr = QFrame()
        ctr.setLayout(QVBoxLayout())
        ctr.layout().setContentsMargins(0, 0, 0, 0)
        ctr.layout().setAlignment(Qt.AlignCenter)
        ctr.layout().addWidget(btn)
        lay.addWidget(ctr)

        main.addWidget(card, alignment=Qt.AlignHCenter)
        main.addStretch()


    def _populate_client_completer(self):
        suggestions = []
        self._client_map = {}
        for c in self._clients:
            txt = f"{c.first_name} {c.last_name}, {c.address}"
            suggestions.append(txt)
            self._client_map[txt] = c.id
        self._client_model.setStringList(suggestions)


    def _filter_clients(self, text: str):
        txt = text.lower()
        filtered = []
        self._client_map.clear()
        for c in self._clients:
            full = f"{c.first_name} {c.last_name}, {c.address}"
            if txt in full.lower():
                filtered.append(full)
                self._client_map[full] = c.id
        self._client_model.setStringList(filtered)
        self._client_completer.setCompletionPrefix(text)
        self._client_completer.complete()


    def _on_client_chosen(self, text: str):
        self._selected_client_id = self._client_map.get(text)
        # Załaduj zwierzęta klienta
        self.animal_cb.clear()
        for a in AnimalService.list_by_owner(self._selected_client_id):
            self.animal_cb.addItem(f"{a.name} (#{a.id})", a.id)
        self.animal_cb.setEnabled(True)
        # Po wyborze klienta odblokuj lekarza
        self.doctor_le.setEnabled(True)


    def _populate_doctor_completer(self):
        suggestions = []
        self._doctor_map = {}
        for d in self._doctors:
            label = f"{d.first_name} {d.last_name} ({d.specialization})"
            suggestions.append(label)
            self._doctor_map[label] = d.id
        self._doctor_model.setStringList(suggestions)


    def _filter_doctors(self, text: str):
        txt = text.lower()
        filtered = []
        self._doctor_map.clear()
        for d in self._doctors:
            label = f"{d.first_name} {d.last_name} ({d.specialization})"
            if txt in label.lower():
                filtered.append(label)
                self._doctor_map[label] = d.id
        self._doctor_model.setStringList(filtered)
        self._doctor_completer.setCompletionPrefix(text)
        self._doctor_completer.complete()


    def _on_doctor_chosen(self, text: str):
        self._selected_doctor_id = self._doctor_map.get(text)
        # Odblokuj wybór godziny i od razu odśwież wolne sloty
        self.time_cb.setEnabled(True)
        self._update_time_slots(self.date_edit.date())


    def _on_facility_changed(self, index: int):
        # Jeśli potrzebujesz filtrować wolne sloty wg placówki, możesz tu odświeżyć _update_time_slots
        self._selected_facility_id = self.facility_cb.currentData()
        # self._update_time_slots(self.date_edit.date())  # odkomentuj, jeśli placówka ma wpływ


    def _update_time_slots(self, qdate: QDate):
        """
        Pobiera z backendu (AppointmentService.get_free_slots) listę wolnych kwadransów
        dla wybranego lekarza i daty. Wypełnia self.time_cb tylko tymi slotami.
        """
        # 1) Jeśli nie wybrano lekarza ani placówki, nie pokazuj nic
        if not self._selected_doctor_id or self.facility_cb.currentData() is None:
            self.time_cb.clear()
            return

        date_str = qdate.toString("yyyy-MM-dd")
        try:
            # Zakładam, że get_free_slots zwraca listę ciągów "HH:MM"
            free_slots = AppointmentService.get_free_slots(
                doctor_id=self._selected_doctor_id,
                date_str=date_str
            )
        except Exception:
            # W razie błędu sieci/serwisu: wyczyść combobox i dopisz placeholder
            self.time_cb.clear()
            self.time_cb.addItem("— błąd pobierania slotów —", None)
            return

        self.time_cb.clear()
        for slot in free_slots:
            self.time_cb.addItem(slot, slot)
        if not free_slots:
            self.time_cb.addItem("— brak wolnych terminów —", None)


    def _reset_form(self):
        """
        Przywraca formularz do stanu początkowego:
        - czyści pola klienta, lekarza, notatek,
        - resetuje comboboxy i QDateEdit,
        - wyłącza comboboxy, które wymagają wyboru klienta/lekarza/placówki.
        """
        # Klient
        self.client_le.clear()
        self._selected_client_id = None
        self._client_model.setStringList([])
        self._client_completer.setCompletionPrefix("")
        # Zwierzę
        self.animal_cb.clear()
        self.animal_cb.setEnabled(False)
        # Placówka – ustaw na „– wybierz –”
        self.facility_cb.setCurrentIndex(0)
        self._selected_facility_id = None
        # Priorytet – zostawiamy na „normalna”
        self.priority_cb.setCurrentIndex(0)
        # Lekarz
        self.doctor_le.clear()
        self._selected_doctor_id = None
        self._doctor_model.setStringList([])
        self._doctor_completer.setCompletionPrefix("")
        self.doctor_le.setEnabled(False)
        # Data
        self.date_edit.setDate(QDate.currentDate())
        # Godzina
        self.time_cb.clear()
        self.time_cb.setEnabled(False)
        # Uwagi
        self.notes_te.clear()

    def _on_save(self):
        missing = []
        if not self._selected_client_id:
            missing.append("Klient")
        if self.animal_cb.currentData() is None:
            missing.append("Zwierzę")
        if self.facility_cb.currentData() is None:
            missing.append("Placówka")
        if not self._selected_doctor_id:
            missing.append("Lekarz")
        if self.date_edit.date() is None:
            missing.append("Data")
        if self.time_cb.currentData() is None:
            missing.append("Godzina")
        if missing:
            QMessageBox.warning(self, "Brak danych",
                                "Uzupełnij: " + ", ".join(missing))
            return

        # Łączenie daty i wybranego slotu w ISO8601
        data_str = self.date_edit.date().toString("yyyy-MM-dd")   # np. "2025-06-10"
        godz     = self.time_cb.currentData()                     # np. "09:00"
        visit_datetime = f"{data_str}T{godz}:00"

        payload = {
            "owner_id":       self._selected_client_id,
            "animal_id":      self.animal_cb.currentData(),
            "facility_id":    self.facility_cb.currentData(),
            "doctor_id":      self._selected_doctor_id,
            "priority":       self.priority_cb.currentData(),
            "visit_datetime": visit_datetime,
            "notes":          self.notes_te.toPlainText().strip() or None,
        }

        try:
            AppointmentService.create(payload)
            QMessageBox.information(self, "Sukces", "Wizyta została umówiona.")
            # Po poprawnym zapisie czyścimy cały formularz:
            self._reset_form()
        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", str(e))
