from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QAbstractItemView,
)
from vetclinic_gui.qt_compat import Qt
import webbrowser

from vetclinic_gui.services.doctors_service import DoctorService
from vetclinic_gui.services.temp_email_service import TempEmailService

class DoctorsPage(QWidget):
    """
    CRUD lekarzy z wyborem specjalizacji i permit_number oraz
    podaniem backup-emaila (analogicznie do konsultantów).
    """
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._deleted_ids = set()
        self._setup_ui()
        self._load_doctors()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Tytuł
        title = QLabel("Zarządzanie lekarzami")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
            padding-bottom: 12px;
        """)
        layout.addWidget(title)

        # --- Tabela lekarzy ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Imię", "Nazwisko", "Email",
            "Specjalizacja", "Nr pozw.", "Backup Email"
        ])
        self.table.hideColumn(0)
        vh = self.table.verticalHeader()
        vh.setVisible(False)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vh.setDefaultSectionSize(48)

        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Styl tabeli
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F9FAFB;
                gridline-color: #E5E7EB;
            }
            QHeaderView::section {
                background-color: #F3F4F6;
                padding: 10px;
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                border: 1px solid #E5E7EB;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1F2937;
            }
            QLineEdit, QComboBox {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 6px;
            }
        """)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # --- Przyciski operacji ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.add_btn = QPushButton("Dodaj lekarza")
        self.remove_btn = QPushButton("Usuń zaznaczone")
        self.save_btn = QPushButton("Zapisz zmiany")

        for btn in (self.add_btn, self.remove_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #374151;
                    border: 1px solid #D1D5DB;
                    border-radius: 4px;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
            """)

        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(32)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)

        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)


    def _load_doctors(self):
        self.table.setRowCount(0)
        doctors = DoctorService.list() or []
        for doc in doctors:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # ID
            self.table.setItem(row,0, QTableWidgetItem(str(doc.id)))
            # Imię
            le1 = QLineEdit(doc.first_name)
            le1.setFixedHeight(28)
            self.table.setCellWidget(row,1,le1)
            # Nazwisko
            le2 = QLineEdit(doc.last_name)
            le2.setFixedHeight(28)
            self.table.setCellWidget(row,2,le2)
            # Email
            le3 = QLineEdit(doc.email)
            le3.setFixedHeight(28)
            self.table.setCellWidget(row,3,le3)
            # Specjalizacja
            le4 = QLineEdit(doc.specialization)
            le4.setFixedHeight(28)
            self.table.setCellWidget(row,4,le4)
            # Nr pozw.
            le5 = QLineEdit(doc.permit_number)
            le5.setFixedHeight(28)
            self.table.setCellWidget(row,5,le5)
            # Backup Email
            le6 = QLineEdit(doc.backup_email or "")
            le6.setFixedHeight(28)
            le6.setReadOnly(False)
            self.table.setCellWidget(row,6,le6)

    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # puste QLineEdit-y
        for col, ph in ((1,"Imię"),(2,"Nazwisko"),(3,"Email"),
                        (4,"Specjalizacja"),(5,"Nr pozw."),(6,"Backup Email")):
            le = QLineEdit()
            le.setFixedHeight(28)
            le.setPlaceholderText(ph)
            self.table.setCellWidget(row,col,le)

    def _on_remove(self):
        rows = sorted({item.row() for item in self.table.selectedItems()})
        for r in reversed(rows):
            id_item = self.table.item(r,0)
            if id_item and id_item.text():
                self._deleted_ids.add(int(id_item.text()))
            self.table.removeRow(r)

    def _on_save(self):
        try:
            # usuwanie
            for _id in self._deleted_ids:
                DoctorService.delete(_id)
            self._deleted_ids.clear()
            # zapis/aktualizacja
            for r in range(self.table.rowCount()):
                id_item = self.table.item(r,0)
                payload = {
                    "first_name":   self.table.cellWidget(r,1).text().strip(),
                    "last_name":    self.table.cellWidget(r,2).text().strip(),
                    "email":        self.table.cellWidget(r,3).text().strip(),
                    "specialization": self.table.cellWidget(r,4).text().strip(),
                    "permit_number": self.table.cellWidget(r,5).text().strip(),
                    "backup_email":  self.table.cellWidget(r,6).text().strip(),
                }
                if id_item and id_item.text():
                    DoctorService.update(int(id_item.text()), payload)
                else:
                    res = DoctorService.create(payload)
                    # uzupełnij ID i email, a następnie otwórz mailto:
                    self.table.setItem(r,0,QTableWidgetItem(str(res.user.id)))
                    self.table.cellWidget(r,3).setText(res.user.email)
                    # mailto
                    subj = "Dane dostępu VetClinic"
                    body = f"Hasło tymczasowe: {res.raw_password}"
                    mailto = f"mailto:{payload['backup_email']}?subject={subj}&body={body}"
                    webbrowser.open(mailto)
                    QMessageBox.information(
                        self, "Wysłano maila",
                        f"Tymczasowe hasło wysłane na {payload['backup_email']}"
                    )
            QMessageBox.information(self, "Sukces","Zmiany zapisane.")
            self._load_doctors()
        except Exception as e:
            QMessageBox.critical(self,"Błąd zapisu", str(e))
