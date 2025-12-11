import sys
import hashlib
import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QBrush, QColor, QCursor, QFont, QTextCharFormat

from vetclinic_gui.services.animals_service import AnimalService
from vetclinic_gui.services.appointments_service import AppointmentService
from vetclinic_gui.services.medical_records_service import MedicalRecordService
from vetclinic_gui.services import blockchain_service


class DashboardWindow(QMainWindow):
    def __init__(self, client_id: int):
        super().__init__()
        self.client_id = client_id

        self.animals = AnimalService.list_by_owner(client_id) or []
        self.animal_id = self.animals[0].id if self.animals else None

        self.highlighted_dates = []
        self.current_appointments = []
        self.row_records = {}

        self.setWindowTitle("VetClinic - Dashboard klienta")
        self.setMinimumSize(1080, 720)
        self.showMaximized()

        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        content_layout.addLayout(self._create_top_bar())
        content_layout.addWidget(self._create_medical_card(), 1)
        content_layout.addWidget(self._create_clinic_visits(), 1)

        main_layout.addWidget(content)

    def _create_top_bar(self):
        layout = QHBoxLayout()

        self.combo_animal = QComboBox()
        for animal in self.animals:
            self.combo_animal.addItem(animal.name, animal.id)
        self.combo_animal.currentIndexChanged.connect(self.on_animal_changed)
        layout.addWidget(self.combo_animal)

        layout.addStretch()

        appt_btn = QPushButton("Umów wizytę")
        appt_btn.setCursor(Qt.PointingHandCursor)
        appt_btn.setStyleSheet(
            "QPushButton { padding:8px 16px; background-color:#38a2db; color:#fff; "
            "border:none; border-radius:15px; }"
            "QPushButton:hover { background-color:#2e97c9; }"
        )
        layout.addWidget(appt_btn)

        return layout

    def on_animal_changed(self, index: int):
        if index < 0:
            return
        self.animal_id = self.combo_animal.currentData()
        self.refresh_data()

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

    def _create_medical_card(self) -> QGroupBox:
        group = QGroupBox("Karta medyczna")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        header = QHBoxLayout()
        lbl = QLabel("Karta medyczna")
        lbl.setFont(QFont("Arial", 12, QFont.Bold))
        header.addWidget(lbl)
        header.addStretch()
        btn = QToolButton()
        btn.setText("\u22EE")
        header.addWidget(btn)
        layout.addLayout(header)

        self.med_table = QTableWidget(0, 4)
        self.med_table.setHorizontalHeaderLabels(
            ["Opis", "Data wizyty", "Status", "Notatki"]
        )
        self.med_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.med_table.setSelectionMode(QTableWidget.SingleSelection)
        self.med_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.med_table.setFrameShape(QFrame.NoFrame)
        self.med_table.setShowGrid(False)
        self.med_table.verticalHeader().setVisible(False)
        self.med_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.med_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.med_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.med_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.med_table.setColumnWidth(3, 20)
        self.med_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.med_table.setStyleSheet(
            """
            QHeaderView::section {
                background-color: #ffffff; border:none; padding:8px;
                font-weight:600; color:#111827; border-bottom:2px solid #e5e7eb;
            }
            QTableWidget {
                border:none; background:transparent;
            }
            QTableWidget::item {
                border-bottom:1px solid #e5e7eb; padding:10px 6px;
            }
        """
        )
        layout.addWidget(self.med_table)

        status_row = QHBoxLayout()
        self.lbl_onchain = QLabel("On-chain: ?")
        self.btn_chain_refresh = QPushButton("Odśwież status on-chain")
        self.btn_chain_anchor = QPushButton("Zapisz hash w blockchainie")
        status_row.addWidget(self.lbl_onchain)
        status_row.addStretch()
        status_row.addWidget(self.btn_chain_refresh)
        status_row.addWidget(self.btn_chain_anchor)
        layout.addLayout(status_row)

        self.med_table.itemSelectionChanged.connect(self._on_record_selection)
        self.btn_chain_refresh.clicked.connect(self._refresh_onchain_status)
        self.btn_chain_anchor.clicked.connect(self._anchor_record_on_chain)

        return group

    def _create_clinic_visits(self) -> QGroupBox:
        group = QGroupBox("Wizyty kliniczne")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        self.clinic_calendar = QCalendarWidget()
        self.clinic_calendar.setFirstDayOfWeek(Qt.Monday)
        layout.addWidget(self.clinic_calendar)

        self.visit_date_lbl = QLabel()
        self.visit_date_lbl.setStyleSheet(
            "color: #38a2db; font-weight: bold; font-size: 14px; padding-left:8px;"
        )
        self.visit_desc_lbl = QLabel()
        self.visit_desc_lbl.setWordWrap(True)
        self.visit_desc_lbl.setStyleSheet(
            "color: #4b5563; font-size:13px; padding:2px 8px;"
        )
        layout.addWidget(self.visit_date_lbl)
        layout.addWidget(self.visit_desc_lbl)

        self.clinic_calendar.selectionChanged.connect(self._clinic_on_date_changed)
        return group

    def refresh_data(self):
        try:
            all_appts = AppointmentService.list_by_owner(self.client_id) or []
        except Exception as exc:
            QToolTip.showText(QCursor.pos(), f"Błąd pobierania wizyt: {exc}")
            all_appts = []

        appts = [a for a in all_appts if a.animal_id == self.animal_id]
        appts.sort(key=lambda a: a.visit_datetime, reverse=True)
        self.current_appointments = appts

        self.med_table.setRowCount(0)
        self.row_records = {}

        for row, appt in enumerate(appts):
            recs = MedicalRecordService.list_by_appointment(appt.id) or []

            if recs:
                desc = " | ".join(r.description for r in recs if r.description)
            else:
                desc = appt.reason or ""

            self.med_table.insertRow(row)

            item_desc = QTableWidgetItem(desc)
            item_desc.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.med_table.setItem(row, 0, item_desc)

            dt_str = appt.visit_datetime.strftime("%d.%m.%Y, %H:%M")
            item_dt = QTableWidgetItem(dt_str)
            item_dt.setTextAlignment(Qt.AlignCenter)
            item_dt.setForeground(QBrush(QColor("#F53838")))
            self.med_table.setItem(row, 1, item_dt)

            item_status = QTableWidgetItem(appt.priority or "")
            item_status.setTextAlignment(Qt.AlignCenter)
            self.med_table.setItem(row, 2, item_status)

            item_notes = QTableWidgetItem(appt.notes or "")
            item_notes.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.med_table.setItem(row, 3, item_notes)

            latest_record = None
            if recs:
                latest_record = sorted(
                    recs, key=lambda r: getattr(r, "created_at", datetime.min)
                )[-1]
            self.row_records[row] = latest_record

        if self.med_table.rowCount() > 0:
            self.med_table.selectRow(0)
            self._refresh_onchain_status()
        else:
            self.lbl_onchain.setText("On-chain: brak rekordów")

        for d in self.highlighted_dates:
            self.clinic_calendar.setDateTextFormat(d, QTextCharFormat())
        self.highlighted_dates.clear()
        days = {
            QDate(
                a.visit_datetime.date().year,
                a.visit_datetime.date().month,
                a.visit_datetime.date().day,
            )
            for a in appts
        }
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor(56, 162, 219, 50)))
        for d in days:
            self.clinic_calendar.setDateTextFormat(d, fmt)
        self.highlighted_dates = list(days)
        self._clinic_on_date_changed()

    def _clinic_on_date_changed(self):
        sel = self.clinic_calendar.selectedDate().toPyDate()
        todays = [a for a in self.current_appointments if a.visit_datetime.date() == sel]
        if not todays:
            self.visit_date_lbl.clear()
            self.visit_desc_lbl.clear()
            return
        appt = sorted(todays, key=lambda x: x.visit_datetime)[0]
        self.visit_date_lbl.setText(appt.visit_datetime.strftime("%d.%m.%Y, %H:%M"))
        desc = appt.reason or ""
        doc = f"Dr {appt.doctor.first_name} {appt.doctor.last_name}"
        self.visit_desc_lbl.setText(f"{desc} - {doc}")

    def _on_record_selection(self):
        self._refresh_onchain_status()

    def _get_selected_record(self):
        selection = self.med_table.selectionModel()
        if not selection:
            return None
        rows = selection.selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return self.row_records.get(row)

    def _record_as_dict(self, record):
        return {
            "id": record.id,
            "description": record.description or "",
            "appointment_id": record.appointment_id,
            "animal_id": record.animal_id,
            "created_at": record.created_at.isoformat()
            if getattr(record, "created_at", None)
            else "",
        }

    def _compute_record_hash(self, record):
        data = json.dumps(self._record_as_dict(record), sort_keys=True).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def _refresh_onchain_status(self):
        record = self._get_selected_record()
        if record is None:
            self.lbl_onchain.setText("On-chain: brak rekordu")
            return
        try:
            chain_rec = blockchain_service.get_record_on_chain(record.id)
        except Exception as exc:
            self.lbl_onchain.setText(f"On-chain: BŁĄD ({exc})")
            return

        local_hash = self._compute_record_hash(record)
        if chain_rec is None:
            self.lbl_onchain.setText("On-chain: NIE")
            return

        on_hash = chain_rec.get("data_hash")
        if on_hash == local_hash:
            block_idx = chain_rec.get("block_index")
            self.lbl_onchain.setText(f"On-chain: TAK (blok #{block_idx})")
        else:
            self.lbl_onchain.setText(
                f"On-chain: ROZBIEŻNY (on-chain {on_hash[:8]}..., lokalny {local_hash[:8]}...)"
            )

    def _anchor_record_on_chain(self):
        record = self._get_selected_record()
        if record is None:
            QMessageBox.warning(self, "Blockchain", "Brak rekordu do zapisania.")
            return
        local_hash = self._compute_record_hash(record)
        try:
            blockchain_service.add_record_on_chain(
                record_id=record.id,
                data_hash=local_hash,
                owner=str(self.client_id),
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Blockchain", f"Błąd wysyłania transakcji: {exc}"
            )
            return
        QMessageBox.information(
            self, "Blockchain", "Hash rekordu został wysłany jako transakcja."
        )
        self._refresh_onchain_status()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow(client_id=1)
    window.show()
    sys.exit(app.exec_())
