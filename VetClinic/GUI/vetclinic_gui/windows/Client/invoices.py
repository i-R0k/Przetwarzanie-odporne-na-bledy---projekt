from datetime import datetime
import webbrowser

from vetclinic_gui.qt_compat import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QLabel,
    QSizePolicy,
    QPushButton,
    QDialog,
    QHBoxLayout,
    QSpacerItem,
    QToolTip,
    QGraphicsDropShadowEffect,
    QAbstractItemView,
)
from PyQt6.QtGui import QBrush, QColor, QFont

from vetclinic_gui.services.invoice_service import InvoiceService
from vetclinic_gui.services.payment_service import PaymentService
from vetclinic_gui.services.clients_service import ClientService


class PaymentDialog(QDialog):
    """Dialog wyboru metody płatności – dane klienta pobierane z ClientService."""
    def __init__(self, parent, invoice_id: int, client_id: int):
        super().__init__(parent)
        self.invoice_id = invoice_id
        # pobierz dane klienta
        try:
            client = ClientService.get(client_id)
            self.email = client.email
            self.fullname = f"{client.first_name} {client.last_name}"
        except Exception as e:
            QToolTip.showText(self.mapToGlobal(self.pos()),
                              f"Błąd pobierania danych klienta: {e}")
            self.email = None
            self.fullname = None

        self.setWindowTitle("Zapłać fakturę")
        self.setModal(True)
        self.setFixedSize(300, 120)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Wybierz metodę płatności:")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()
        btn_stripe = QPushButton("Stripe")
        btn_payu   = QPushButton("PayU")
        for btn in (btn_stripe, btn_payu):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: #38a2db; color: white; "
                "border: none; border-radius: 6px; padding: 6px 12px; }"
                "QPushButton:hover { background-color: #2e8ac7; }"
            )
        btn_stripe.clicked.connect(self._pay_stripe)
        btn_payu.clicked.connect(self._pay_payu)

        btn_layout.addWidget(btn_stripe)
        btn_layout.addWidget(btn_payu)
        btn_layout.addSpacerItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            )
        )
        layout.addLayout(btn_layout)

    def _pay_stripe(self):
        try:
            url = PaymentService.stripe_checkout(self.invoice_id)
            webbrowser.open(url)
            self.accept()
        except Exception as e:
            QToolTip.showText(self.mapToGlobal(self.pos()), f"Błąd Stripe: {e}")

    def _pay_payu(self):
        if not (self.email and self.fullname):
            QToolTip.showText(self.mapToGlobal(self.pos()),
                              "Brak danych klienta – nie można zainicjować PayU")
            return
        try:
            url = PaymentService.payu_checkout(self.invoice_id, self.email, self.fullname)
            webbrowser.open(url)
            self.accept()
        except Exception as e:
            QToolTip.showText(self.mapToGlobal(self.pos()), f"Błąd PayU: {e}")


class InvoicesWindow(QWidget):
    def __init__(self, client_id: int):
        super().__init__()
        self.client_id = client_id
        self.setWindowTitle("Faktury klienta")
        self.resize(820, 600)
        self.setStyleSheet("background-color: #f5f6fa;")
        self._setup_ui()
        self._load_invoices()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(0)

        # Card container for title and table
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: white; border-radius: 12px; }"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 0)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        # Header inside card
        header = QLabel("Lista faktur")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #333;")
        card_layout.addWidget(header)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: white; border: none; }"
            "QHeaderView::section { background-color: #ececec; color: #555; "
            "font: bold 12px 'Segoe UI'; padding: 8px; }"
            "QTableWidget::item { padding: 8px; }"
        )
        headers = ["ID", "Data wystawienia", "Kwota", "Status", "Akcja"]
        self.table.setHorizontalHeaderLabels(headers)

        hdr = self.table.horizontalHeader()
        # ID kolumna dopasowana do zawartości, pozostałe równo rozciągnięte
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for col in range(1, self.table.columnCount()):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        # **Nowość**: wyższe wiersze
        vh = self.table.verticalHeader()
        vh.setDefaultSectionSize(50)
        vh.setVisible(False)

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        card_layout.addWidget(self.table)

        # Empty state inside card
        self.empty_label = QLabel("Brak faktur do wyświetlenia.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-style: italic; padding: 32px;")
        card_layout.addWidget(self.empty_label)

        root.addWidget(card)

    def _load_invoices(self):
        try:
            invoices = InvoiceService.list_by_client(self.client_id) or []
        except Exception:
            invoices = []

        invoices.sort(
            key=lambda inv: getattr(inv, "created_at", datetime.min),
            reverse=True
        )
        self.table.setRowCount(0)

        if not invoices:
            self.table.hide()
            self.empty_label.show()
            return

        self.empty_label.hide()
        self.table.show()

        for inv in invoices:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            id_item = QTableWidgetItem(str(inv.id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Data wystawienia
            raw = getattr(inv, "created_at", "")
            dt = None
            if isinstance(raw, str):
                try:
                    dt = datetime.fromisoformat(raw)
                except:
                    dt = None
            else:
                dt = raw
            date_str = dt.strftime("%d.%m.%Y") if dt else ""
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setForeground(QBrush(QColor('#d32f2f')))
            self.table.setItem(row, 1, date_item)

            # Kwota
            raw_amt = getattr(inv, "amount", "")
            try:
                amt = float(raw_amt)
                amt_str = f"{amt:,.2f} PLN"
            except:
                amt_str = str(raw_amt)
            amt_item = QTableWidgetItem(amt_str)
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, amt_item)

            # Status
            status_item = QTableWidgetItem(str(inv.status).capitalize())
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, status_item)

            # Akcja: stylowany przycisk Zapłać
            pay_btn = QPushButton("Zapłać")
            pay_btn.setCursor(Qt.PointingHandCursor)
            pay_btn.setStyleSheet(
                "QPushButton { background-color: #38a2db; color: white; border: none; "
                "border-radius: 6px; padding: 6px 16px; }"
                "QPushButton:hover { background-color: #2e8ac7; }"
            )
            pay_btn.clicked.connect(
                lambda _, iid=inv.id: PaymentDialog(self, iid, self.client_id).exec()
            )
            self.table.setCellWidget(row, 4, pay_btn)
