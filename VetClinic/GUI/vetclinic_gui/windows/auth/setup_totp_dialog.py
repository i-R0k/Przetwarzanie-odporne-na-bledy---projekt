import io, qrcode, requests
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMessageBox
from vetclinic_gui.qt_compat import Qt  # ensure legacy Qt enums are available

API_CONFIRM_TOTP_URL = "http://127.0.0.1:8000/users/confirm-totp"

def round_pixmap(pixmap, radius):
    if pixmap.isNull():
        return pixmap

    # Offscreen/minimal backends na Windows lubią się wykrzaczyć na QPainter;
    # w takim trybie odpuszczamy zaokrąglanie.
    platform = QtGui.QGuiApplication.platformName()
    if platform in ("offscreen", "minimal"):
        return pixmap

    rounded = QtGui.QPixmap(pixmap.size())
    rounded.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(rounded)
    try:
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(
            QtGui.QPainter.RenderHint.SmoothPixmapTransform, True
        )

        path = QtGui.QPainterPath()
        rect = QtCore.QRectF(0, 0, pixmap.width(), pixmap.height())
        path.addRoundedRect(rect, radius, radius)

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
    finally:
        painter.end()

    return rounded

class ProportionalImageLabel(QtWidgets.QLabel):
    """QLabel, która automatycznie przeskalowuje pixmapę zachowując proporcje, a jej sizeHint odzwierciedla te proporcje."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._aspect_ratio = None  
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

    def setPixmap(self, pixmap):

        rounded = round_pixmap(pixmap, 45 )
        self._pixmap = rounded
        if self._pixmap and not self._pixmap.isNull():
            self._aspect_ratio = self._pixmap.width() / self._pixmap.height()
        else:
            self._aspect_ratio = None
        self.updateScaledPixmap()
        self.updateGeometry()

    def updateScaledPixmap(self):
        if not self._pixmap or self._pixmap.isNull():
            return

        # Używamy aktualnego rozmiaru widgetu, ale musimy go zabezpieczyć przed zerową szerokością lub wysokością
        current_size = self.size()
        if current_size.width() > 0 and current_size.height() > 0:
            scaled = self._pixmap.scaled(
                current_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            super().setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap and not self._pixmap.isNull():
            self.updateScaledPixmap()

    def sizeHint(self):
        if self._aspect_ratio is not None:
            # Preferowany rozmiar: bieżąca szerokość, a wysokość na podstawie proporcji
            return QtCore.QSize(self.width(), int(self.width() / self._aspect_ratio))
        else:
            return super().sizeHint()

class SetupTOTPDialog(QtWidgets.QDialog):
    """Dialog do konfiguracji TOTP (QR + 6-cyfrowy kod)."""
    def __init__(self, totp_uri, email, parent=None):
        super().__init__(parent)
        self.totp_uri = totp_uri
        self.email    = email
        self.setWindowTitle("Konfiguracja TOTP")
        self.resize(350, 450)
        self.setObjectName("SetupTOTPDialog")
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        info = QtWidgets.QLabel(
            "Zeskanuj poniższy kod QR w Google Authenticator,\n"
            "a następnie wpisz wygenerowany 6-cyfrowy kod:"
        )
        info.setObjectName("info_label")
        layout.addWidget(info)

        self.qr_label = QtWidgets.QLabel()
        layout.addWidget(self.qr_label)
        self._generate_qr()

        self.totp_input = QtWidgets.QLineEdit()
        self.totp_input.setPlaceholderText("Wpisz 6-cyfrowy kod TOTP")
        self.totp_input.setMaxLength(6)
        layout.addWidget(self.totp_input)

        btn = QtWidgets.QPushButton("Potwierdź TOTP")
        btn.clicked.connect(self.confirm_totp)
        layout.addWidget(btn)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)

        self.setStyleSheet("""
            #SetupTOTPDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-family: Arial, sans-serif;
                font-size: 12pt;
                color: #333;
            }
            QLineEdit {
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 5px;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #2d89ef;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1b5fbd;
            }
            #SetupTOTPDialog QLineEdit:hover {
                border: 1px solid #66afe9;
            }
            #info_label{
                font-size: 10pt;
                color: #555;
                font-family: arial, sans-serif;
            }
        """)

    def _generate_qr(self):
        qr = qrcode.QRCode(
            version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10, border=4
        )
        qr.add_data(self.totp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO(); img.save(buf, format="PNG")
        qimg = QtGui.QImage(); qimg.loadFromData(buf.getvalue(), "PNG")
        pm = QtGui.QPixmap.fromImage(qimg)
        self.qr_label.setPixmap(round_pixmap(pm, 45))
        self.qr_label.setScaledContents(True)

    def confirm_totp(self):
        code = self.totp_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Błąd", "Wprowadź kod TOTP!")
            return
        resp = requests.post(API_CONFIRM_TOTP_URL, json={
            "email": self.email, "totp_code": code
        })
        if resp.status_code == 200:
            QMessageBox.information(self, "Sukces", "TOTP skonfigurowany pomyślnie!")
            self.accept()
        else:
            QMessageBox.warning(self, "Błąd", "Niepoprawny kod TOTP.")
            self.status_label.setText("Błąd potwierdzenia TOTP.")
