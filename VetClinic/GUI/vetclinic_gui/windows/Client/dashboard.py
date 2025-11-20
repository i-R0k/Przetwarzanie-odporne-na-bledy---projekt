import sys

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


class DashboardWindow(QMainWindow):
    def __init__(self, client_id: int):
        super().__init__()
        self.client_id = client_id

        self.animals = AnimalService.list_by_owner(client_id) or []
        self.animal_id = self.animals[0].id if self.animals else None

        self.highlighted_dates = []
        self.current_appointments = []

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
        self.med_table.setSelectionMode(QTableWidget.NoSelection)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow(client_id=1)
    window.show()
    sys.exit(app.exec_())
