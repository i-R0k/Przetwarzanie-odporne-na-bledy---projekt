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
    QAbstractItemView,
)
from vetclinic_gui.qt_compat import Qt

from vetclinic_gui.services.facility_service import FacilityService

class FacilitiesPage(QWidget):
    """
    Pełny CRUD placówek: przegląd, dodawanie, usuwanie, modyfikacja i zapis zmian,
    z ujednoliconym stylem zgodnym z ConsultantsPage.
    """
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._deleted_ids = set()
        self._setup_ui()
        self._load_facilities()

    def _setup_ui(self):
        # Główny układ
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Tytuł
        title = QLabel("Zarządzanie placówkami")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
            padding-bottom: 12px;
        """)
        layout.addWidget(title)

        # --- Tabela placówek ---
        # kolumny: 0=ID(hidden), 1=Nazwa, 2=Adres, 3=Telefon
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nazwa", "Adres", "Telefon"])
        self.table.hideColumn(0)

        # pionowy nagłówek ukryty, stała wysokość wiersza
        vh = self.table.verticalHeader()
        vh.setVisible(False)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vh.setDefaultSectionSize(48)

        # zachowanie tabeli
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # stylizacja tabeli i edytowalnych pól
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
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 6px;
            }
        """)

        # proporcje kolumn
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # nazwa
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # adres
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # telefon
        hdr.setStretchLastSection(False)

        layout.addWidget(self.table)

        # --- Przyciski operacji ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.add_btn = QPushButton("Dodaj placówkę")
        self.remove_btn = QPushButton("Usuń zaznaczone")
        self.save_btn = QPushButton("Zapisz zmiany")

        # wspólny styl dla przycisków Dodaj/Usuń
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

        # podpięcie akcji
        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _load_facilities(self):
        self.table.setRowCount(0)
        for fac in FacilityService.list():
            row = self.table.rowCount()
            self.table.insertRow(row)
            # ID ukryte
            self.table.setItem(row, 0, QTableWidgetItem(str(fac.id)))
            # Nazwa, Adres jako QLineEdit (że można edytować inline)
            name_le = QLineEdit(fac.name)
            name_le.setFixedHeight(28)
            self.table.setCellWidget(row, 1, name_le)

            addr_le = QLineEdit(fac.address)
            addr_le.setFixedHeight(28)
            self.table.setCellWidget(row, 2, addr_le)

            phone_le = QLineEdit(fac.phone or "")
            phone_le.setFixedHeight(28)
            self.table.setCellWidget(row, 3, phone_le)

    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # puste edytowalne pola
        for col in (1, 2, 3):
            le = QLineEdit()
            le.setFixedHeight(28)
            if col == 1: le.setPlaceholderText("Nazwa")
            if col == 2: le.setPlaceholderText("Adres")
            if col == 3: le.setPlaceholderText("Telefon")
            self.table.setCellWidget(row, col, le)

    def _on_remove(self):
        rows = {item.row() for item in self.table.selectedItems()}
        for row in sorted(rows, reverse=True):
            id_item = self.table.item(row, 0)
            if id_item and id_item.text():
                self._deleted_ids.add(int(id_item.text()))
            self.table.removeRow(row)

    def _on_save(self):
        try:
            # Usuń skasowane
            for fid in self._deleted_ids:
                FacilityService.delete(fid)
            self._deleted_ids.clear()

            # Stwórz/aktualizuj
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                name_le  = self.table.cellWidget(row, 1)
                addr_le  = self.table.cellWidget(row, 2)
                phone_le = self.table.cellWidget(row, 3)

                payload = {
                    "name":    name_le.text().strip()  if name_le  else "",
                    "address": addr_le.text().strip()  if addr_le  else "",
                    "phone":   phone_le.text().strip() if phone_le else "",
                }

                if id_item and id_item.text():
                    FacilityService.update(int(id_item.text()), payload)
                else:
                    payload["created_by"] = self.admin_id
                    FacilityService.create(payload)

            QMessageBox.information(self, "Sukces", "Zmiany zostały zapisane.")
            self._load_facilities()

        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", str(e))
