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
    QDoubleSpinBox,
    QTextEdit,
    QCompleter,
    QComboBox,
)
from vetclinic_gui.qt_compat import Qt
from PyQt6.QtCore import QDate, QStringListModel
from datetime import date

from vetclinic_gui.services.clients_service import ClientService
from vetclinic_gui.services.animals_service import AnimalService

class AnimalRegistrationPage(QWidget):
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id

        # trzymamy pełną listę klientów tu:
        self._clients = ClientService.list() or []
        # mapujemy wyświetlany tekst → client.id
        self._completer_map = {}
        self._selected_owner_id = None

        self._setup_ui()
        # po zbudowaniu UI, zasilamy completer wszystkimi klientami
        self._update_owner_completer()

    def _setup_ui(self):
        self.setStyleSheet("background-color: #F3F4F6;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addStretch()

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

        title = QLabel("Rejestracja nowego zwierzęcia")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
        """)
        card_layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignCenter)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)

        # ⇒ pola zwierzęcia:
        self.name_le    = QLineEdit(); self.name_le.setPlaceholderText("Np. Burek")
        self.species_le = QLineEdit(); self.species_le.setPlaceholderText("Np. pies, kot")
        self.breed_le   = QLineEdit(); self.breed_le.setPlaceholderText("Np. owczarek niem.")
        self.gender_cb  = QComboBox()
        for lbl, val in [("– wybierz –",None),("Samiec","male"),("Samica","female"),("Nieznana","unknown")]:
            self.gender_cb.addItem(lbl,val)
        self.dob_de     = QDateEdit(calendarPopup=True)
        self.dob_de.setDisplayFormat("yyyy-MM-dd")
        self.dob_de.setDate(QDate.currentDate())
        self.weight_ds  = QDoubleSpinBox()
        self.weight_ds.setRange(0,500); self.weight_ds.setDecimals(2); self.weight_ds.setSuffix(" kg")
        self.chip_le    = QLineEdit(); self.chip_le.setPlaceholderText("Numer mikroczipa")
        self.notes_te   = QTextEdit(); self.notes_te.setPlaceholderText("Dodatkowe uwagi"); self.notes_te.setFixedHeight(80)

        # ⇒ nowe pole Właściciel z completerem
        self.owner_le = QLineEdit()
        self.owner_le.setPlaceholderText("🔍 Wyszukaj właściciela…")

        # model + completer jako atrybuty
        self._owner_model     = QStringListModel(self)
        self._owner_completer = QCompleter(self._owner_model, self.owner_le)
        self._owner_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._owner_completer.setFilterMode(Qt.MatchContains)
        self._owner_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._owner_completer.activated[str].connect(self._on_owner_selected)
        # podpinamy filtr przy każdej edycji tekstu
        self.owner_le.textEdited.connect(self._filter_owners)
        self.owner_le.setCompleter(self._owner_completer)

        # styl pól…
        widget_style = """
            QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox {
                background-color: #fff;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #374151;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #2563EB;
            }
        """
        for w in (self.name_le,self.species_le,self.breed_le,
                  self.gender_cb,self.dob_de,self.weight_ds,
                  self.chip_le,self.owner_le):
            w.setStyleSheet(widget_style)
        self.notes_te.setStyleSheet("""
            QTextEdit { background-color:#fff;border:1px solid #d1d5db;border-radius:6px;
                         padding:8px;font-size:14px;color:#374151; }
            QTextEdit:focus { border:1px solid #2563EB; }
        """)

        # dodajemy wszystkie do layoutu
        form.addRow("Imię zwierzęcia:", self.name_le)
        form.addRow("Gatunek:",         self.species_le)
        form.addRow("Rasa:",            self.breed_le)
        form.addRow("Płeć:",            self.gender_cb)
        form.addRow("Data ur.:",        self.dob_de)
        form.addRow("Waga:",            self.weight_ds)
        form.addRow("Mikroczip #:",      self.chip_le)
        form.addRow("Notatki:",          self.notes_te)
        form.addRow("Właściciel:",       self.owner_le)

        card_layout.addLayout(form)

        # przycisk
        self.register_btn = QPushButton("Zarejestruj zwierzę")
        self.register_btn.setFixedHeight(40)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setStyleSheet("""
            QPushButton { background-color:#2563EB;color:#fff;
                          font-size:16px;font-weight:bold;
                          border:none;border-radius:6px;padding:0 24px; }
            QPushButton:hover { background-color:#1D4ED8; }
            QPushButton:pressed { background-color:#1E40AF; }
        """)
        self.register_btn.clicked.connect(self._on_register)

        btn_ctr = QFrame()
        btn_ctr.setLayout(QVBoxLayout())
        btn_ctr.layout().setContentsMargins(0,0,0,0)
        btn_ctr.layout().setAlignment(Qt.AlignCenter)
        btn_ctr.layout().addWidget(self.register_btn)
        card_layout.addWidget(btn_ctr)

        main_layout.addWidget(card, alignment=Qt.AlignHCenter)
        main_layout.addStretch()

    def _update_owner_completer(self):
        """Wczytaj całą listę klientów do completera."""
        suggestions = []
        self._completer_map.clear()
        for c in self._clients:
            txt = f"{c.first_name} {c.last_name}, {c.address}"
            suggestions.append(txt)
            self._completer_map[txt] = c.id

        self._owner_model.setStringList(suggestions)

    def _filter_owners(self, text: str):
        """Filtruj lokalną listę po każdym znaku."""
        txt = text.lower()
        filtered = []
        self._completer_map.clear()

        for c in self._clients:
            full = f"{c.first_name} {c.last_name}, {c.address}"
            if txt in full.lower():
                filtered.append(full)
                self._completer_map[full] = c.id

        self._owner_model.setStringList(filtered)
        self._owner_completer.setCompletionPrefix(text)
        self._owner_completer.complete()

    def _on_owner_selected(self, text: str):
        """Zapisujemy wybranego właściciela."""
        self._selected_owner_id = self._completer_map.get(text)


    def _on_register(self):
        missing = []
        if not self.name_le.text().strip():     missing.append("Imię zwierzęcia")
        if not self.species_le.text().strip():  missing.append("Gatunek")
        if not self._selected_owner_id:         missing.append("Właściciel")
        if missing:
            QMessageBox.warning(
                self, "Brak danych",
                "Uzupełnij pola:\n" + "\n".join(missing)
            )
            return
    
        # 1) oblicz wiek w latach jako liczba zmiennoprzecinkowa
        dob = self.dob_de.date().toPyDate()
        today = date.today()
        years = today.year - dob.year
        months = today.month - dob.month
        if today.day < dob.day:
            months -= 1
        total_months = years * 12 + months
        age_decimal = round(total_months / 12, 1)
    
        # 2) przygotuj dane
        payload = {
            "name":             self.name_le.text().strip(),
            "species":          self.species_le.text().strip(),
            "breed":            self.breed_le.text().strip() or None,
            "gender":           self.gender_cb.currentData(),  # male/female/unknown
            "birth_date":       dob.isoformat(),
            "age":              age_decimal,
            "weight":           self.weight_ds.value() or None,
            "microchip_number": self.chip_le.text().strip() or None,
            "notes":            self.notes_te.toPlainText().strip() or None,
            "owner_id":         self._selected_owner_id,
        }
    
        # 3) wyślij do serwisu
        try:
            AnimalService.create(payload)
            QMessageBox.information(self, "Sukces", "Zwierzę zostało zarejestrowane.")
    
            # 4) wyczyść formularz
            self.name_le.clear()
            self.species_le.clear()
            self.breed_le.clear()
            self.gender_cb.setCurrentIndex(0)
            self.dob_de.setDate(QDate.currentDate())
            self.weight_ds.setValue(0.0)
            self.chip_le.clear()
            self.notes_te.clear()
            self.owner_le.clear()
            self._selected_owner_id = None
    
        except Exception as e:
            QMessageBox.critical(self, "Błąd rejestracji", str(e))
    
