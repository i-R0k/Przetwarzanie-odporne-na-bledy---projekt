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
    QCheckBox,
    QAbstractItemView,
)
from vetclinic_gui.qt_compat import Qt

from vetclinic_gui.services.clients_service import ClientService

class ClientsPage(QWidget):
    """
    Pełny CRUD klientów: przegląd, dodawanie, usuwanie wielu,
    modyfikacja i zapis zmian. Backup email nie jest już polem.
    """
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._deleted_ids = set()
        self._setup_ui()
        self._load_clients()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Tytuł
        title = QLabel("Zarządzanie klientami")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
            padding-bottom: 12px;
        """)
        layout.addWidget(title)

        # Tabela: checkbox, ID, Imię, Nazwisko, Email, Telefon, Adres, Kod poczt.
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "", "ID", "Imię", "Nazwisko", "Email",
            "Telefon", "Adres", "Kod poczt."
        ])
        self.table.hideColumn(1)  # chowamy kolumnę ID

        # Wysokość wiersza
        vh = self.table.verticalHeader()
        vh.setVisible(False)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vh.setDefaultSectionSize(48)

        # Styl i zachowanie tabeli
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
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

        # Proporcje kolumn
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # checkbox
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # ID
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Imię
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Nazwisko
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Email
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Telefon
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)           # Adres
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Kod poczt.

        layout.addWidget(self.table)

        # Przyciski
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.add_btn    = QPushButton("Dodaj klienta")
        self.remove_btn = QPushButton("Usuń zaznaczone")
        self.save_btn   = QPushButton("Zapisz zmiany")

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

    def _load_clients(self):
        self.table.setRowCount(0)
        clients = ClientService.list() or []

        for cli in clients:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 1) checkbox
            chk = QCheckBox()
            chk.setFixedHeight(28)
            self.table.setCellWidget(row, 0, chk)

            # 2) ID (nieedytowalne)
            id_item = QTableWidgetItem(str(cli.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, id_item)

            # 3) pola QLineEdit: first_name, last_name, email, phone, address, postal_code
            fields = [
                ("first_name", 2),
                ("last_name",  3),
                ("email",      4),
                ("phone_number",5),
                ("address",    6),
                ("postal_code",7),
            ]
            for attr, col in fields:
                le = QLineEdit(str(getattr(cli, attr) or ""))
                le.setFixedHeight(28)
                self.table.setCellWidget(row, col, le)

    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # checkbox
        chk = QCheckBox()
        chk.setFixedHeight(28)
        self.table.setCellWidget(row, 0, chk)

        # puste ID
        self.table.setItem(row, 1, QTableWidgetItem(""))

        # puste QLineEdit-y
        placeholders = ["Imię","Nazwisko","Email","Telefon","Adres","Kod poczt."]
        for i, ph in enumerate(placeholders, start=2):
            le = QLineEdit()
            le.setFixedHeight(28)
            le.setPlaceholderText(ph)
            self.table.setCellWidget(row, i, le)

    def _on_remove(self):
        # zaznaczone checkboxy → usuń z DB i z tabeli
        rows_to_delete = []
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 0)
            if chk and chk.isChecked():
                id_item = self.table.item(r, 1)
                if id_item and id_item.text().isdigit():
                    try:
                        ClientService.delete(int(id_item.text()))
                    except Exception as e:
                        QMessageBox.critical(
                            self, "Błąd usuwania",
                            f"Nie udało się usunąć klienta: {e}"
                        )
                rows_to_delete.append(r)
        for r in reversed(rows_to_delete):
            self.table.removeRow(r)

    def _on_save(self):
        try:
            # dla każdego wiersza: utwórz lub zaktualizuj klienta
            for r in range(self.table.rowCount()):
                id_item = self.table.item(r, 1)
                # zbierz dane
                mapping = [
                    ("first_name",   2),
                    ("last_name",    3),
                    ("email",        4),
                    ("phone_number", 5),
                    ("address",      6),
                    ("postal_code",  7),
                ]
                payload = {}
                for key, col in mapping:
                    txt = self.table.cellWidget(r, col).text().strip()
                    payload[key] = txt

                if id_item and id_item.text().isdigit():
                    # aktualizacja
                    ClientService.update(int(id_item.text()), payload)
                else:
                    # nowy klient
                    ClientService.create(payload)

            QMessageBox.information(self, "Sukces", "Zmiany zostały zapisane.")
            self._load_clients()

        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", str(e))
