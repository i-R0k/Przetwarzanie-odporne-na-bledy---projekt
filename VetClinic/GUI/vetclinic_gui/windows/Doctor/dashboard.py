import sys

from vetclinic_gui.qt_compat import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QHeaderView,
    QSizePolicy,
    QToolTip,
    QAbstractItemView,
)
from PyQt6.QtCore import QDate, QDateTime, QTime
from PyQt6.QtGui import (
    QFont,
    QBrush,
    QColor,
    QCursor,
    QPainter,
    QPen,
    QGradient,
    QLinearGradient,
)
try:
    from PyQt6.QtCharts import (
        QChart,
        QChartView,
        QLineSeries,
        QScatterSeries,
        QAreaSeries,
        QDateTimeAxis,
        QValueAxis,
    )
    _CHARTS_AVAILABLE = True
except Exception:
    QChart = QChartView = QLineSeries = QScatterSeries = QAreaSeries = None  # type: ignore
    QDateTimeAxis = QValueAxis = None  # type: ignore
    _CHARTS_AVAILABLE = False

from vetclinic_gui.services.animals_service      import AnimalService
from vetclinic_gui.services.clients_service      import ClientService
from vetclinic_gui.services.appointments_service import AppointmentService


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        # główny layout strony (tylko content, bez sidebaru)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- górny pasek ---
        top_bar = self._create_top_bar()
        layout.addLayout(top_bar)

        # --- wiersz 1: nadchodzące + poprzednie wizyty ---
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        upcoming = self._create_upcoming_visits()
        previous = self._create_previous_visits()
        for w in (upcoming, previous):
            w.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            w.setMinimumWidth(0)
        row1.addWidget(upcoming, 1)
        row1.addWidget(previous, 1)
        layout.addLayout(row1, 3)

        # --- wiersz 2: statystyki wizyt ---
        row2 = QHBoxLayout()
        stats = self._create_appointments_stats()
        stats.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row2.addWidget(stats)
        layout.addLayout(row2, 2)

    def _create_top_bar(self):
        layout = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Szukaj pacjenta...")
        search.setFixedHeight(30)
        search.setStyleSheet(
            "QLineEdit { border:1px solid #d1d5db; border-radius:15px; padding-left:10px; }"
        )
        layout.addWidget(search)
        layout.addStretch()
        logout = QPushButton("Wyloguj")
        logout.setCursor(Qt.PointingHandCursor)
        logout.setStyleSheet(
            "QPushButton { padding:8px 16px; background-color:#f87171; color:#fff; border:none; border-radius:15px; }"
            "QPushButton:hover { background-color:#ef4444; }"
        )
        layout.addWidget(logout)
        return layout

    def _create_upcoming_visits(self) -> QGroupBox:
        """
        Tworzy sekcję ‘Nadchodzące wizyty’:
        Kolumny: Data | Pacjent | Godzina | Powód i uwagi
        Łączymy pola Appointment.reason oraz Appointment.notes w jednej kolumnie.
        """
        group = QGroupBox()
        group.setStyleSheet(self._groupbox_css())

        layout = QVBoxLayout(group)

        # Nagłówek sekcji
        header = QHBoxLayout()
        title = QLabel("Nadchodzące wizyty")
        title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")  # trzy pionowe kropki
        menu_btn.setStyleSheet(
            "QToolButton { border: none; font-size: 16px; color: #6b7280; }"
            "QToolButton:hover { color: #111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        # Tabela z 4 kolumnami (ostatnia to „Powód i uwagi”)
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Data", "Pacjent", "Godzina", "Powód i uwagi"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)

        # Ustawienia rozmiarów kolumn
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Data
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Pacjent
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Godzina
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Powód i uwagi
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setWordWrap(True)

        # Stylizacja nagłówków i wierszy
        table.setStyleSheet("""
            QTableWidget { border: none; background-color: transparent; }
            QHeaderView::section {
                background-color: #ffffff;
                border: none;
                padding: 8px;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget::item {
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 6px;
            }
        """)

        # 1) Pobranie wizyt z API
        try:
            all_visits = AppointmentService.list()
        except Exception as e:
            QToolTip.showText(QCursor.pos(), f"Błąd pobierania wizyt: {e}")
            layout.addWidget(table)
            return group

        # 2) Przygotuj słownik id_zwierzaka -> nazwa
        animals = {a.id: a.name for a in AnimalService.list() or []}
        today_date = QDate.currentDate().toPyDate()

        # 3) Filtrowanie: tylko wizyty, których data >= dzisiaj
        upcoming_visits = [
            v for v in all_visits
            if hasattr(v, "visit_datetime") and v.visit_datetime.date() >= today_date
        ]
        # 4) Sortowanie rosnąco po dacie/godzinie
        upcoming_visits.sort(key=lambda v: v.visit_datetime)

        # 5) Wypełnianie tabeli
        for visit in upcoming_visits:
            row = table.rowCount()
            table.insertRow(row)

            dt          = visit.visit_datetime
            date_str    = dt.date().strftime("%d.%m.%Y")
            time_str    = dt.strftime("%H:%M")
            animal_name = animals.get(visit.animal_id, "")
            reason_str  = visit.reason or ""
            notes_str   = visit.notes or ""
            # Łączymy reason i notes w jeden ciąg:
            if notes_str:
                combined = f"{reason_str} – {notes_str}"
            else:
                combined = reason_str

            # Kolumna „Data”
            table.setItem(row, 0, QTableWidgetItem(date_str))

            # Kolumna „Pacjent”
            item_animal = QTableWidgetItem(animal_name)
            item_animal.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, item_animal)

            # Kolumna „Godzina”
            table.setItem(row, 2, QTableWidgetItem(time_str))

            # Kolumna „Powód i uwagi”
            table.setItem(row, 3, QTableWidgetItem(combined))

        layout.addWidget(table)
        return group


    def _create_previous_visits(self) -> QGroupBox:
        """
        Tworzy sekcję ‘Poprzednie wizyty’:
        Kolumny: Data | Pacjent | Priorytet | Powód i uwagi
        Łączymy Appointment.reason oraz Appointment.notes.
        Priorytet wyświetlamy z pola Appointment.priority i kolorujemy.
        """
        group = QGroupBox()
        group.setStyleSheet(self._groupbox_css())

        layout = QVBoxLayout(group)

        # Nagłówek sekcji
        header = QHBoxLayout()
        title = QLabel("Poprzednie wizyty")
        title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")
        menu_btn.setStyleSheet(
            "QToolButton { border: none; font-size: 16px; color: #6b7280; }"
            "QToolButton:hover { color:#111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        # Tabela z 4 kolumnami: Data, Pacjent, Priorytet, Powód i uwagi
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Data", "Pacjent", "Priorytet", "Powód i uwagi"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)

        # Ustawienia rozmiarów kolumn
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Data
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Pacjent
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Priorytet
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Powód i uwagi
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setWordWrap(True)

        # Stylizacja nagłówków i wierszy
        table.setStyleSheet("""
            QTableWidget { border: none; background-color: transparent; }
            QHeaderView::section {
                background-color: #ffffff;
                border: none;
                padding: 8px;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget::item {
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 6px;
            }
        """)

        # 1) Pobranie wizyt z API
        try:
            all_visits = AppointmentService.list()
        except Exception as e:
            QToolTip.showText(QCursor.pos(), f"Błąd pobierania wizyt: {e}")
            layout.addWidget(table)
            return group

        # 2) Przygotuj słownik id_zwierzaka -> nazwa
        animals = {a.id: a.name for a in AnimalService.list() or []}
        today_date = QDate.currentDate().toPyDate()

        # 3) Filtrowanie: tylko wizyty sprzed dzisiaj
        previous_visits = [
            v for v in all_visits
            if hasattr(v, "visit_datetime") and v.visit_datetime.date() < today_date
        ]
        # 4) Sortowanie malejąco (najpierw najnowsze)
        previous_visits.sort(key=lambda v: v.visit_datetime, reverse=True)

        # 5) Wypełnianie tabeli
        for visit in previous_visits:
            row = table.rowCount()
            table.insertRow(row)

            dt          = visit.visit_datetime
            date_str    = dt.date().strftime("%d.%m.%Y")
            animal_name = animals.get(visit.animal_id, "")
            priority    = visit.priority or "normalna"
            reason_str  = visit.reason or ""
            notes_str   = visit.notes or ""
            # Łączymy reason i notes:
            if notes_str:
                combined = f"{reason_str} – {notes_str}"
            else:
                combined = reason_str

            # Kolumna „Data”
            table.setItem(row, 0, QTableWidgetItem(date_str))

            # Kolumna „Pacjent”
            item_animal = QTableWidgetItem(animal_name)
            item_animal.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, item_animal)

            # Kolumna „Priorytet” (kolor: zielony=normalna, pomarańcz=pilna, czerwony=nagła)
            pr_item = QTableWidgetItem(priority)
            if priority == "pilna":
                pr_item.setForeground(QBrush(QColor("#FBBF24")))  # pomarańczowy
            elif priority == "nagła":
                pr_item.setForeground(QBrush(QColor("#EF4444")))  # czerwony
            else:
                pr_item.setForeground(QBrush(QColor("#10B981")))  # zielony dla "normalna"
            table.setItem(row, 2, pr_item)

            # Kolumna „Powód i uwagi”
            table.setItem(row, 3, QTableWidgetItem(combined))

        layout.addWidget(table)
        return group


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

    def _create_appointments_stats(self) -> QGroupBox:
        group = QGroupBox()
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        header = QHBoxLayout()
        title = QLabel("Statystyki wizyt")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("⋮")
        menu_btn.setStyleSheet(
            "QToolButton { border:none; font-size:16px; color:#6b7280; }"
            "QToolButton:hover { color:#111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        if not _CHARTS_AVAILABLE:
            fallback = QLabel("Charts unavailable")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fallback)
            return group

        try:
            all_visits = AppointmentService.list()
        except Exception as exc:
            QToolTip.showText(QCursor.pos(), f"Blad pobierania wizyt: {exc}")
            return group

        today_qdate = QDate.currentDate()
        date_qdates = [today_qdate.addDays(-i) for i in range(9, -1, -1)]

        counts_by_date = {qd.toPyDate(): 0 for qd in date_qdates}
        for visit in all_visits:
            if not hasattr(visit, "visit_datetime"):
                continue
            visit_date = visit.visit_datetime.date()
            if visit_date in counts_by_date:
                counts_by_date[visit_date] += 1

        date_values = [(qd, counts_by_date[qd.toPyDate()]) for qd in date_qdates]
        raw_pts = [
            (QDateTime(qd, QTime(0, 0)).toMSecsSinceEpoch(), count)
            for qd, count in date_values
        ]

        def catmull_rom(points, samples=20):
            def CR(p0, p1, p2, p3, t):
                a = 2 * p1[1]
                b = -p0[1] + p2[1]
                c = 2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]
                d = -p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]

                ax = 2 * p1[0]
                bx = -p0[0] + p2[0]
                cx = 2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]
                dx = -p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]
                t2, t3 = t * t, t * t * t
                y = 0.5 * (a + b * t + c * t2 + d * t3)
                x = 0.5 * (ax + bx * t + cx * t2 + dx * t3)
                return x, y

            dense = []
            n = len(points)
            for i in range(n - 1):
                p0 = points[i - 1] if i - 1 >= 0 else points[i]
                p1 = points[i]
                p2 = points[i + 1]
                p3 = points[i + 2] if i + 2 < n else points[i + 1]
                for s in range(samples):
                    t = s / samples
                    dense.append(CR(p0, p1, p2, p3, t))
            dense.append(points[-1])
            return dense

        dense_pts = catmull_rom(raw_pts, samples=20)

        top = QLineSeries()
        for x, y in dense_pts:
            top.append(x, y)
        pen = QPen(QColor("#38A2DB"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        top.setPen(pen)

        base = QLineSeries()
        for x, _ in dense_pts:
            base.append(x, 0)

        area = QAreaSeries(top, base)
        grad = QLinearGradient(0, 0, 0, 1)
        grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        grad.setColorAt(0.0, QColor(56, 162, 219, 120))
        grad.setColorAt(1.0, QColor(56, 162, 219, 20))
        area.setBrush(QBrush(grad))
        area.setPen(QPen(Qt.NoPen))

        scatter = QScatterSeries()
        scatter.setMarkerSize(8)
        scatter.setColor(QColor("#38A2DB"))
        scatter.setBorderColor(QColor("#ffffff"))
        for qd, cnt in date_values:
            ms = QDateTime(qd, QTime(0, 0)).toMSecsSinceEpoch()
            scatter.append(ms, cnt)

        def show_tt(point, state):
            if state:
                dt_str = QDateTime.fromMSecsSinceEpoch(int(point.x())).date().toString("dd.MM.yyyy")
                QToolTip.showText(QCursor.pos(), f"{dt_str}: {int(point.y())} wizyt")

        scatter.hovered.connect(show_tt)

        chart = QChart()
        chart.addSeries(area)
        chart.addSeries(top)
        chart.addSeries(scatter)
        chart.setBackgroundVisible(False)
        chart.legend().hide()

        axisX = QDateTimeAxis()
        axisX.setFormat("dd.MM.yyyy")
        axisX.setTickCount(len(date_values))
        axisX.setRange(
            QDateTime(date_values[0][0], QTime(0, 0)),
            QDateTime(date_values[-1][0], QTime(0, 0)),
        )
        chart.addAxis(axisX, Qt.AlignBottom)
        for series in (area, top, scatter):
            series.attachAxis(axisX)

        ymax = max(cnt for _, cnt in date_values) * 1.1 if date_values else 1
        axisY = QValueAxis()
        axisY.setRange(0, ymax)
        axisY.setLabelFormat("%d")
        chart.addAxis(axisY, Qt.AlignLeft)
        for series in (area, top, scatter):
            series.attachAxis(axisY)

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        view.setStyleSheet("border:none; background-color:transparent;")
        layout.addWidget(view)

        group._chart = chart
        group._top = top
        group._base = base
        group._area = area
        group._scatter = scatter
        group._axisX = axisX
        group._axisY = axisY
        group._view = view

        return group

