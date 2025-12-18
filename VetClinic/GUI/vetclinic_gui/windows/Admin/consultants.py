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
    QComboBox,
    QLineEdit,
    QAbstractItemView,
)
from vetclinic_gui.qt_compat import Qt

from vetclinic_gui.services.consultant_service import ConsultantService
from vetclinic_gui.services.facility_service import FacilityService

class ConsultantsPage(QWidget):

    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._deleted_ids = set()
        self._setup_ui()
        self._load_consultants()

    def _setup_ui(self):
        # Główny układ
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Tytuł
        title = QLabel("Zarządzanie konsultantami")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
            padding-bottom: 12px;
        """)
        layout.addWidget(title)

        # --- Tabela konsultantów ---
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Imię", "Nazwisko", "Email", "Placówka", "Backup Email"
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
            QComboBox, QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 6px;
            }
        """)

        # Proporcje kolumn
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hdr.setStretchLastSection(False)

        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.add_btn = QPushButton("Dodaj konsultanta")
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

        # styl dla przycisku Zapisz
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

        # powiązania sygnałów
        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _load_consultants(self):
        self.table.setRowCount(0)
        consultants = ConsultantService.list() or []
        facilities  = FacilityService.list() or []

        for cons in consultants:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(cons.id)))

            # Imię jako QLineEdit
            first_le = QLineEdit(cons.first_name)
            first_le.setFixedHeight(28)
            self.table.setCellWidget(row, 1, first_le)

            # Nazwisko jako QLineEdit
            last_le = QLineEdit(cons.last_name)
            last_le.setFixedHeight(28)
            self.table.setCellWidget(row, 2, last_le)

            # Email jako QLineEdit
            email_le = QLineEdit(cons.email)
            email_le.setFixedHeight(28)
            self.table.setCellWidget(row, 3, email_le)

            # Placówka (QComboBox)…
            combo = QComboBox()
            for f in facilities:
                combo.addItem(f.name, f.id)
            if getattr(cons, "facility_id", None) is not None:
                idx = next((i for i,f in enumerate(facilities) if f.id == cons.facility_id), 0)
                combo.setCurrentIndex(idx)
            self.table.setCellWidget(row, 4, combo)

            # Backup Email jako QLineEdit (tylko do odczytu)…
            backup_le = QLineEdit(cons.backup_email or "")
            backup_le.setFixedHeight(28)
            backup_le.setReadOnly(False)
            self.table.setCellWidget(row, 5, backup_le)

    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Imię
        first_le = QLineEdit()
        first_le.setFixedHeight(28)
        first_le.setPlaceholderText("Imię")
        self.table.setCellWidget(row, 1, first_le)

        # Nazwisko
        last_le = QLineEdit()
        last_le.setFixedHeight(28)
        last_le.setPlaceholderText("Nazwisko")
        self.table.setCellWidget(row, 2, last_le)

        # Email
        email_le = QLineEdit()
        email_le.setFixedHeight(28)
        email_le.setPlaceholderText("Email")
        self.table.setCellWidget(row, 3, email_le)

        # Placówka
        combo = QComboBox()
        for f in FacilityService.list() or []:
            combo.addItem(f.name, f.id)
        self.table.setCellWidget(row, 4, combo)

        # Backup Email
        backup_le = QLineEdit()
        backup_le.setFixedHeight(28)
        backup_le.setPlaceholderText("Backup Email")
        self.table.setCellWidget(row, 5, backup_le)

    def _on_remove(self):
        rows = {item.row() for item in self.table.selectedItems()}
        for row in sorted(rows, reverse=True):
            id_item = self.table.item(row, 0)
            if id_item and id_item.text():
                self._deleted_ids.add(int(id_item.text()))
            self.table.removeRow(row)

    def _on_save(self):
        try:
            # 1) usuń skasowanych
            for cid in self._deleted_ids:
                ConsultantService.delete(cid)
            self._deleted_ids.clear()

            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                is_update = bool(id_item and id_item.text())

                # 2) pobierz widgety
                first_le  = self.table.cellWidget(row, 1)
                last_le   = self.table.cellWidget(row, 2)
                email_le  = self.table.cellWidget(row, 3)
                combo     = self.table.cellWidget(row, 4)   # *to* jest placówka
                backup_le = self.table.cellWidget(row, 5)   # *to* jest backup-email

                first  = first_le .text().strip() if first_le  else ""
                last   = last_le  .text().strip() if last_le   else ""
                email  = email_le .text().strip() if email_le  else ""
                facility_id  = combo.currentData()      if combo     else None
                raw_backup   = backup_le.text().strip() if backup_le else ""

                # 3) zbuduj payload, ale backup_email tylko gdy nie pusty
                payload = {
                    "first_name":  first,
                    "last_name":   last,
                    "email":       email,
                    "facility_id": facility_id,
                }
                if raw_backup:
                    payload["backup_email"] = raw_backup

                # 4) update albo create
                if is_update:
                    ConsultantService.update(int(id_item.text()), payload)
                else:
                    res = ConsultantService.create(payload)
                    # uzupełnij wiersz po create
                    self.table.setItem(row, 0, QTableWidgetItem(str(res.user.id)))
                    email_le.setText(res.user.email)
                    QMessageBox.information(
                        self, "Wysłano dane dostępu",
                        f"Hasło wysłano na: {raw_backup}"
                    )

            QMessageBox.information(self, "Sukces", "Zmiany zostały zapisane.")
            self._load_consultants()

        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", str(e))
