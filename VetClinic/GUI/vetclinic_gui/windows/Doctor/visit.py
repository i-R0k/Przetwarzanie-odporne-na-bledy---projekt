from vetclinic_gui.qt_compat import Qt
from PyQt6.QtCore import QDateTime, pyqtSignal, QStringListModel
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QGroupBox,
    QDateTimeEdit,
    QComboBox,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QApplication,
    QDoubleSpinBox,
    QSplitter,
    QSizePolicy,
    QHeaderView,
    QLabel,
    QGridLayout,
    QCompleter,
    QAbstractItemView,
)
from PyQt6.QtGui import QFont
import sys

from vetclinic_gui.services.animals_service       import AnimalService
from vetclinic_gui.services.appointments_service  import AppointmentService
from vetclinic_gui.services.clients_service       import ClientService
from vetclinic_gui.services.doctors_service       import DoctorService


class VisitsWindow(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, doctor_id: int):
        super().__init__()
        self.doctor_id = doctor_id

        # Pobierz lekarza i facility_id
        doc = DoctorService.get(doctor_id)
        self.facility_id = getattr(doc, "facility_id", None)

        # Jeżeli brakuje facility_id, zablokuj zapis i wyświetl błąd
        if not isinstance(self.facility_id, int):
            QMessageBox.critical(
                self, "Błąd konfiguracyjny",
                "Nie udało się odczytać placówki lekarza (facility_id).\n"
                "Upewnij się, że backend zwraca to pole."
            )
            # Nie zezwalamy na zapis wizyty
            self.can_save = False
        else:
            self.can_save = True

        # Miejsce na wszystkie rekordy pobrane z API:
        self.clients = []
        self.animals = []

        self._setup_ui()
        self._load_data()

    def _groupbox_css(self) -> str:
        return """
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 12px;
                font-size: 18px;
                font-weight: bold;
                color: #111827;
                background-color: #ffffff;
            }
        """

    def _setup_ui(self):
        # --- Ustawienia okna ---
        self.setWindowTitle("Wizyty")
        self.resize(1200, 800)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- Pasek akcji ---
        top_bar = QHBoxLayout()
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("🔍 Wyszukaj opiekuna...")
        self.search_le.setFixedHeight(30)
        self.search_le.setStyleSheet(
            "QLineEdit { border:1px solid #d1d5db; border-radius:15px; padding-left:10px; }"
        )
        self.search_le.textChanged.connect(self._filter_clients)

        self._owner_model     = QStringListModel(self)
        self._owner_completer = QCompleter(self._owner_model, self)
        self._owner_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._owner_completer.setFilterMode(Qt.MatchContains)
        self.search_le.setCompleter(self._owner_completer)
        self._owner_completer.activated.connect(self._on_owner_selected)
        self._completer_map = {}

        top_bar.addWidget(self.search_le)
        top_bar.addStretch()

        self.save_btn = QPushButton("Zapisz wizytę")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(
            "QPushButton { padding:8px 16px; background-color:#38a2db; color:#fff; "
            "border:none; border-radius:15px; }"
            "QPushButton:hover { background-color:#2e3a50; }"
        )
        self.save_btn.clicked.connect(self._on_save_visit)
        top_bar.addWidget(self.save_btn)

        main_layout.addLayout(top_bar)

        # --- Inicjalizacja widgetów formularza ---
        self.datetime_edit   = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)

        self.client_cb       = QComboBox()
        self.client_cb.currentIndexChanged.connect(self._on_client_change)

        self.animal_cb       = QComboBox()
        self.animal_cb.currentIndexChanged.connect(self._on_animal_change)

        self.status_cb       = QComboBox()
        self.status_cb.addItems(["zaplanowana", "odwołana", "zakończona"])

        self.priority_cb     = QComboBox()
        self.priority_cb.addItems(["normalna", "pilna", "nagła"])

        self.weight_visit_sb = QDoubleSpinBox()
        self.weight_visit_sb.setRange(0.1, 500.0)
        self.weight_visit_sb.setSuffix(" kg")
        self.weight_visit_sb.setSingleStep(0.1)
        self.weight_visit_sb.setDecimals(2)

        self.age_visit_sb = QDoubleSpinBox()
        self.age_visit_sb.setRange(0.0, 100.0)
        self.age_visit_sb.setDecimals(1)
        self.age_visit_sb.setSingleStep(0.1)
        self.age_visit_sb.setSuffix(" lat")

        self.gender_visit_cb = QComboBox()
        self.gender_visit_cb.addItems(["samiec", "samica", "nieznana"])

        self.fee_sb = QDoubleSpinBox()
        self.fee_sb.setRange(0, 100000)
        self.fee_sb.setDecimals(2)
        self.fee_sb.setSuffix(" PLN")
        self.fee_sb.setSingleStep(1.0)

        self.reason_te    = QTextEdit()
        self.reason_te.setFixedHeight(60)

        self.treatment_te = QTextEdit()
        self.treatment_te.setFixedHeight(100)

        # --- Pola tylko do odczytu z danych zwierzęcia ---
        self.species_le   = QLineEdit();    self.species_le.setReadOnly(True)
        self.breed_le     = QLineEdit();    self.breed_le.setReadOnly(True)
        self.gender_le    = QLineEdit();    self.gender_le.setReadOnly(True)
        self.birthdate_le = QLineEdit();    self.birthdate_le.setReadOnly(True)
        self.age_le       = QLineEdit();    self.age_le.setReadOnly(True)
        self.weight_le    = QLineEdit();    self.weight_le.setReadOnly(True)
        self.microchip_le = QLineEdit();    self.microchip_le.setReadOnly(True)
        self.animal_notes = QTextEdit()
        self.animal_notes.setReadOnly(True)
        self.animal_notes.setFixedHeight(60)

        # --- Sekcja: Nowa wizyta ---
        form_box = QGroupBox()
        form_box.setStyleSheet(self._groupbox_css() + """
            QLabel, QDateTimeEdit, QComboBox, QDoubleSpinBox, QTextEdit {
                font-family: "Segoe UI", sans-serif;
                font-size: 8pt;
            }
            QDateTimeEdit, QComboBox, QDoubleSpinBox, QTextEdit {
                background-color: #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px;             
            }
            QDateTimeEdit:hover, QComboBox:hover, QDoubleSpinBox:hover, QTextEdit:hover {
                border: 1px solid #38a2db;
            }
            QDateTimeEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border: 1px solid #256fb8;
            }
        """)
        form_vbox = QVBoxLayout(form_box)
        form_vbox.setContentsMargins(8, 8, 8, 8)
        form_vbox.setSpacing(6)

        hdr_form = QHBoxLayout()
        lbl_form = QLabel("Nowa wizyta")
        lbl_form.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        hdr_form.addWidget(lbl_form)
        hdr_form.addStretch()
        form_vbox.addLayout(hdr_form)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(10)
        form_layout.addRow("Data i czas:", self.datetime_edit)
        form_layout.addRow("Właściciel:",  self.client_cb)
        form_layout.addRow("Zwierzę:",     self.animal_cb)
        form_layout.addRow("Status:",      self.status_cb)
        form_layout.addRow("Typ wizyty:",  self.priority_cb)
        form_layout.addRow("Waga (kg):",   self.weight_visit_sb)
        form_layout.addRow("Wiek:",        self.age_visit_sb)
        form_layout.addRow("Płeć:",        self.gender_visit_cb)
        form_layout.addRow("Powód wizyty:",self.reason_te)
        form_layout.addRow("Leczenie:",    self.treatment_te)
        form_layout.addRow("Opłata (PLN):",  self.fee_sb)

        form_vbox.addLayout(form_layout)

        # --- Sekcja: Dane zwierzęcia ---
        info_box = QGroupBox()
        info_box.setStyleSheet(self._groupbox_css() + """
            QLineEdit, QTextEdit {
                font-family: "Segoe UI", sans-serif;
                font-size: 8pt;
                background-color: #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px;
            }
            QLabel {
                color: #374151;
                font-size: 8pt;
            }
        """)
        info_vbox = QVBoxLayout(info_box)
        info_vbox.setContentsMargins(4, 4, 4, 4)
        info_vbox.setSpacing(4)
        info_box.setMaximumWidth(350)

        hdr_info = QHBoxLayout()
        lbl_info = QLabel("Dane zwierzęcia")
        lbl_info.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        hdr_info.addWidget(lbl_info)
        hdr_info.addStretch()
        info_vbox.addLayout(hdr_info)
        info_vbox.addSpacing(6)

        info_grid = QGridLayout()
        info_grid.setContentsMargins(0, 0, 0, 0)
        info_grid.setHorizontalSpacing(12)
        info_grid.setVerticalSpacing(8)

        fields = [
            ("Gatunek:",   self.species_le),
            ("Rasa:",      self.breed_le),
            ("Płeć:",      self.gender_le),
            ("Data ur.:",  self.birthdate_le),
            ("Wiek:",      self.age_le),
            ("Waga (kg):", self.weight_le),
            ("Mikroczip:", self.microchip_le),
            ("Uwagi:",     self.animal_notes)
        ]
        for row, (text, widget) in enumerate(fields):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            info_grid.addWidget(lbl, row, 0)
            widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            info_grid.addWidget(widget, row, 1)
            info_grid.setRowStretch(row, 1)

        info_vbox.addLayout(info_grid, 1)

        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(form_box)
        top_splitter.addWidget(info_box)
        top_splitter.setStretchFactor(0, 3)
        top_splitter.setStretchFactor(1, 2)
        main_layout.addWidget(top_splitter)

        # --- Sekcja: Poprzednie wizyty ---
        prev_box = QGroupBox()
        prev_box.setStyleSheet(self._groupbox_css())
        prev_vbox = QVBoxLayout(prev_box)
        prev_vbox.setContentsMargins(8, 8, 8, 8)
        prev_vbox.setSpacing(6)

        hdr_prev = QHBoxLayout()
        lbl_prev = QLabel("Poprzednie wizyty")
        lbl_prev.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        hdr_prev.addWidget(lbl_prev)
        hdr_prev.addStretch()
        prev_vbox.addLayout(hdr_prev)

        self.prev_table = QTableWidget(0, 7)
        self.prev_table.setHorizontalHeaderLabels(
            ["ID", "Data i czas", "Zwierzę", "Właściciel", "Waga (kg)", "Powód", "Leczenie"]
        )
        self.prev_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.prev_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.prev_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.prev_table.verticalHeader().setVisible(False)
        self.prev_table.setAlternatingRowColors(True)

        self.prev_table.setStyleSheet("""
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 6px;
                border: none;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
        """)
        hdr = self.prev_table.horizontalHeader()
        for col in range(5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        self.prev_table.cellDoubleClicked.connect(self._on_edit_visit)
        prev_vbox.addWidget(self.prev_table)

        prev_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        main_layout.addWidget(prev_box)

    def _load_data(self):
        # Pobierz klientów i zwierzęta z API
        self.clients = ClientService.list()
        self._populate_clients(self.clients)
        self._update_owner_completer()

        self.animals = AnimalService.list()
        self._populate_animals(self.animals)

        if self.client_cb.count():
            self._on_client_change(0)

    def _populate_clients(self, clients_list):
        self.client_cb.blockSignals(True)
        self.client_cb.clear()
        for c in clients_list:
            label = f"{c.first_name} {c.last_name}"
            self.client_cb.addItem(label, c.id)
        self.client_cb.blockSignals(False)

    def _populate_animals(self, animals_list):
        self.animal_cb.blockSignals(True)
        self.animal_cb.clear()
        for a in animals_list:
            self.animal_cb.addItem(a.name, a.id)
        self.animal_cb.blockSignals(False)

    def _update_owner_completer(self):
        suggestions = []
        self._completer_map.clear()
        for c in self.clients:
            full = f"{c.first_name} {c.last_name}"
            suggestions.append(full)
            self._completer_map[full] = c.id
        for a in self.animals:
            suggestions.append(a.name)
            self._completer_map[a.name] = a.owner_id
        self._owner_model.setStringList(suggestions)

    def _filter_clients(self, text: str):
        txt = text.lower()
        filtered = [
            c for c in self.clients
            if txt in f"{c.first_name} {c.last_name}".lower()
        ]
        self._populate_clients(filtered)
        if self.client_cb.count():
            self._on_client_change(0)

    def _on_owner_selected(self, text: str):
        owner_id = self._completer_map.get(text)
        if owner_id is None:
            return
        idx = self.client_cb.findData(owner_id)
        if idx == -1:
            return
        self.client_cb.blockSignals(True)
        self.client_cb.setCurrentIndex(idx)
        self.client_cb.blockSignals(False)
        self._on_client_change(idx)

    def _on_client_change(self, index: int):
        owner_id = self.client_cb.currentData()
        own_animals = [a for a in self.animals if a.owner_id == owner_id]
        self._populate_animals(own_animals)
        if own_animals:
            self._on_animal_change(0)
        else:
            for w in [
                self.species_le, self.breed_le, self.gender_le,
                self.birthdate_le, self.age_le, self.weight_le,
                self.microchip_le, self.animal_notes
            ]:
                w.clear()
            self.prev_table.setRowCount(0)

    def _on_animal_change(self, index: int):
        aid = self.animal_cb.currentData()
        animal = next((a for a in self.animals if a.id == aid), None)
        if not animal:
            return

        self.species_le.setText(animal.species or "")
        self.breed_le.setText(animal.breed or "")
        self.gender_le.setText(animal.gender or "")

        bd = animal.birth_date
        bd_str = bd.isoformat() if hasattr(bd, "isoformat") else str(bd or "")
        self.birthdate_le.setText(bd_str)

        self.age_le.setText(str(animal.age or ""))
        if animal.weight is not None:
            self.weight_le.setText(f"{animal.weight:.1f}")
        else:
            self.weight_le.clear()

        self.microchip_le.setText(animal.microchip_number or "")
        self.animal_notes.setPlainText(animal.notes or "")

        self.age_visit_sb.setValue(animal.age or 0.0)
        self.weight_visit_sb.setValue(animal.weight or 0.0)

        gi = self.gender_visit_cb.findText(animal.gender or "")
        if gi >= 0:
            self.gender_visit_cb.setCurrentIndex(gi)

        oi = self.client_cb.findData(animal.owner_id)
        if oi != -1:
            self.client_cb.blockSignals(True)
            self.client_cb.setCurrentIndex(oi)
            self.client_cb.blockSignals(False)

        self._load_previous_visits()

    def _load_previous_visits(self):
        # Pobierz wszystkie wizyty z serwisu i odfiltruj po zwierzęciu i lekarzu
        all_visits = AppointmentService.list()
        aid = self.animal_cb.currentData()
        visits = [
            v for v in all_visits
            if v.animal_id == aid and v.doctor_id == self.doctor_id
        ]

        self.prev_table.setRowCount(0)

        for visit in visits:
            row_index = self.prev_table.rowCount()
            self.prev_table.insertRow(row_index)

            animal = next((a for a in self.animals if a.id == visit.animal_id), None)
            owner = next((c for c in self.clients if c.id == visit.owner_id), None)

            date_time_str = visit.visit_datetime
            animal_name = animal.name if animal else ""
            owner_name = f"{owner.first_name} {owner.last_name}" if owner else ""

            wv = getattr(visit, "weight", None)
            weight_str = f"{wv:.1f}" if isinstance(wv, (int, float)) else ""

            reason_str = visit.reason or ""
            treatment_str = getattr(visit, "treatment", "") or ""

            values = [
                visit.id,
                date_time_str,
                animal_name,
                owner_name,
                weight_str,
                reason_str,
                treatment_str
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if col in (0, 4):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.prev_table.setItem(row_index, col, item)

    def _on_save_visit(self):
        if not self.can_save:
            QMessageBox.critical(self, "Błąd", "Nie można zapisać wizyty bez facility_id.")
            return

        # 1) Zaktualizuj dane zwierzęcia
        aid = self.animal_cb.currentData()
        AnimalService.update(aid, {
            "weight": self.weight_visit_sb.value(),
            "age":    self.age_visit_sb.value(),
            "gender": self.gender_visit_cb.currentText()
        })

        # 2) Przygotuj payload
        payload = {
            "doctor_id":      self.doctor_id,
            "animal_id":      aid,
            "owner_id":       self.client_cb.currentData(),
            "facility_id":    self.facility_id,            # już zawsze int
            "visit_datetime": self.datetime_edit.dateTime().toString(Qt.ISODate),
            "reason":         self.reason_te.toPlainText(),
            "treatment":      self.treatment_te.toPlainText(),
            "priority":       self.priority_cb.currentText(),
            "weight":         self.weight_visit_sb.value(),
            "fee":            self.fee_sb.value()
        }

        try:
            if hasattr(self, "editing_id"):
                AppointmentService.update(self.editing_id, payload)
                del self.editing_id
            else:
                AppointmentService.create(payload)
        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu wizyty", str(e))
            return

        QMessageBox.information(self, "Sukces", "Wizyta zapisana.")
        self._load_previous_visits()

    def _on_edit_visit(self, row: int, col: int):
        vid = int(self.prev_table.item(row, 0).text())
        visit = AppointmentService.get(vid)
        self.editing_id = vid

        dt_str = visit.visit_datetime.isoformat()
        self.datetime_edit.setDateTime(QDateTime.fromString(dt_str, Qt.ISODate))

        self.client_cb.setCurrentIndex(self.client_cb.findData(visit.owner_id))
        self.animal_cb.setCurrentIndex(self.animal_cb.findData(visit.animal_id))
        self.priority_cb.setCurrentText(visit.priority or "")
        self.reason_te.setPlainText(visit.reason or "")
        self.treatment_te.setPlainText(getattr(visit, "treatment", "") or "")
        self.weight_visit_sb.setValue(visit.weight or 0.0)

        if hasattr(visit, "age"):
            self.age_visit_sb.setValue(visit.age or 0.0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VisitsWindow(doctor_id=1)
    w.show()
    sys.exit(app.exec())
