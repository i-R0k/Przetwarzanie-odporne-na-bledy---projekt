from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox

class AdminSettingsPage(QWidget):
    """
    Panel ustawień administratora.
    """
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Ustawienia systemu")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        # Przykładowe opcje
        self.enable_notifications_cb = QCheckBox("Włącz powiadomienia e-mail")
        self.maintenance_mode_cb = QCheckBox("Tryb konserwacji")

        layout.addWidget(self.enable_notifications_cb)
        layout.addWidget(self.maintenance_mode_cb)

        self.save_btn = QPushButton("Zapisz ustawienia")
        # TODO: podłączyć logikę zapisu
        layout.addWidget(self.save_btn)
