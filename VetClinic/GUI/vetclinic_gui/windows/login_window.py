import sys, os
import requests
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMessageBox
from vetclinic_gui.qt_compat import Qt  # patches QtCore.Qt enum aliases
from vetclinic_gui.services.auth_service import AuthService
from vetclinic_gui.windows.auth.setup_totp_dialog import SetupTOTPDialog
from vetclinic_gui.windows.auth.password_dialogs import ChangePasswordDialog, ResetTOTPDialog
from vetclinic_gui.windows.main_window import MainWindow
from vetclinic_gui.windows.auth.setup_totp_dialog import round_pixmap
from vetclinic_gui.windows.auth.setup_totp_dialog import ProportionalImageLabel

API_LOGIN_URL        = "http://127.0.0.1:8000/users/login"
API_CHANGE_PWD_URL   = "http://127.0.0.1:8000/users/change-password"
API_CONFIRM_TOTP_URL = "http://127.0.0.1:8000/users/confirm-totp"

class LoginWindow(QtWidgets.QWidget):
    """Okno logowania z obsługą OTP-mail, TOTP i reset TOTP."""
    def __init__(self):
        super().__init__()
        self.auth = AuthService()
        self.setWindowTitle("VetClinic - Logowanie")
        self.setFixedSize(1000, 650)
        self._build_ui()

    def _build_ui(self):
        # Główny layout horyzontalny z marginesami
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(40, 15, 15, 15)

        # ========== LEWA CZĘŚĆ: FORMULARZ ==========
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Nagłówek z łamaniem linii
        label_title = QtWidgets.QLabel("Cześć!\nWitaj ponownie")
        font_title = QtGui.QFont("Arial", 22, QtGui.QFont.Weight.Bold)
        label_title.setFont(font_title)
        
        label_subtitle = QtWidgets.QLabel("Witamy w VetClinic!")
        font_subtitle = QtGui.QFont("Arial", 12)
        label_subtitle.setFont(font_subtitle)
        label_subtitle.setStyleSheet("color: #666;")
        
        # Pola logowania
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("przykładowy@przykład.pl")

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Hasło")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        # Jednorazowe hasło (OTP-mail), domyślnie ukryte
        self.otp_input = QtWidgets.QLineEdit()
        self.otp_input.setPlaceholderText("Jednorazowe hasło")
        self.otp_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.otp_input.setVisible(False)

        # TOTP, domyślnie ukryte
        self.totp_input = QtWidgets.QLineEdit()
        self.totp_input.setPlaceholderText("Wprowadź 6-cyfrowy kod TOTP")
        self.totp_input.setMaxLength(6)
        self.totp_input.setVisible(False)

        # Reset TOTP button, domyślnie ukryty
        self.reset_totp_btn = QtWidgets.QPushButton("Nie mam dostępu do Authenticatora")
        self.reset_totp_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.reset_totp_btn.setVisible(False)
        self.reset_totp_btn.clicked.connect(self.handle_reset_totp)

        # Przycisk logowania
        self.login_button = QtWidgets.QPushButton("Zaloguj")
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedHeight(40)
        self.login_button.clicked.connect(self.handle_login)

        # Dodajemy widgety do layoutu w kolejności:
        left_layout.addStretch(1)
        left_layout.addWidget(label_title)
        left_layout.addWidget(label_subtitle)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.email_input)
        left_layout.addWidget(self.password_input)
        left_layout.addWidget(self.otp_input)
        left_layout.addWidget(self.totp_input)
        left_layout.addWidget(self.reset_totp_btn)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.login_button)
        left_layout.addStretch(2)

        
        # ========== PRAWA CZĘŚĆ: OBRAZ ==========
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addStretch(1)
        
        self.image_label = ProportionalImageLabel()
        self.image_label.setMinimumWidth(1024)
        self.image_label.setMinimumSize(450, 400)
        
        current_dir = os.path.dirname(os.path.abspath(__file__)) 
        image_path = os.path.join(current_dir, "..", "Resources", "Login_picture.png")
        pixmap = QtGui.QPixmap(image_path)
        if pixmap.isNull():
            print("Nie udało się załadować obrazu z:", image_path)
        else:
            self.image_label.setPixmap(pixmap)
        
        # Dodajemy obraz do prawego layoutu
        right_layout.addWidget(self.image_label, alignment=QtCore.Qt.AlignCenter)
        right_layout.addStretch(1)
        
        # Dodajemy oba widgety do głównego layoutu – lewa i prawa część
        main_layout.addWidget(left_widget, stretch=1)
        main_layout.addWidget(right_widget, stretch=1)
        self.setLayout(main_layout)
        
        # Stylizacja QSS – jednolite tło i zaokrąglone rogi dla obrazka
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
            #loginButton {
                background-color: #2d89ef;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 15px;
            }
            #loginButton:hover {
                background-color: #1b5fbd;
            }
            QLabel {
                font-family: Arial, sans-serif;
            }
            /* Zaokrąglamy rogi obrazu na etykiecie */
            QLabel:hasPixmap {
                border-radius: 20px;
                overflow: hidden;
                border: 2px solid #ccc;
            }
        """)

    def handle_login(self):
        email = self.email_input.text().strip()
        pwd   = self.password_input.text().strip()
        otp   = self.otp_input.text().strip()  if getattr(self, "otp_input", None) and self.otp_input.isVisible()   else None
        totp  = self.totp_input.text().strip() if getattr(self, "totp_input", None) and self.totp_input.isVisible() else None

        if not email or not pwd:
            return QMessageBox.warning(self, "Błąd", "Podaj email i hasło.")

        payload = {"email": email, "password": pwd}
        if otp:
            payload["otp_code"] = otp
        if totp:
            payload["totp_code"] = totp

        try:
            resp = requests.post(API_LOGIN_URL, json=payload)

            # 1) Pierwsze logowanie → wymaga zmiany hasła
            if resp.status_code == 202:
                dlg = ChangePasswordDialog(email, otp or pwd, self)
                if dlg.exec() == QtWidgets.QDialog.Accepted:
                    # po zmianie hasła ponawiamy logowanie
                    self.password_input.setText(dlg.new_pwd.text())
                    return self.handle_login()
                return

            # 2) Provisioning TOTP
            elif resp.status_code == 201:
                uri = resp.json().get("totp_uri")
                if uri:
                    SetupTOTPDialog(uri, email, self).exec()
                # pokazujemy pole na kod TOTP
                self.totp_input.setVisible(True)
                return

            # 3) Pełne logowanie OK
            elif resp.status_code == 200:
                data         = resp.json()
                raw_role     = data.get("role", "").lower()
                role_map     = {
                    "klient":        "client",
                    "lekarz":        "doctor",
                    "recepcjonista": "receptionist",
                    "admin":         "admin",
                }
                normalized   = role_map.get(raw_role, raw_role)
                user_id      = data.get("user_id")

                # przygotowujemy odpowiednie ID
                doctor_id       = user_id if normalized == "doctor"     else None
                receptionist_id = user_id if normalized == "receptionist" else None
                client_id       = user_id if normalized == "client"     else None

                # przejście do głównego okna
                self.hide()
                self.main_window = MainWindow(
                    normalized,
                    doctor_id       = doctor_id,
                    receptionist_id = receptionist_id,
                    client_id       = client_id,
                )
                return self.main_window.show()

            # 4) Kod TOTP wymagany
            elif resp.status_code == 400 and "Kod TOTP wymagany" in resp.json().get("detail", ""):
                self.totp_input.setVisible(True)
                if hasattr(self, "reset_totp_btn"):
                    self.reset_totp_btn.setVisible(True)
                return

            # 5) Inne błędy
            else:
                detail = resp.json().get("detail", "Logowanie nie powiodło się")
                return QMessageBox.warning(self, "Błąd", detail)

        except Exception as e:
            return QMessageBox.critical(self, "Błąd", f"Problem z API: {e}")


    def handle_reset_totp(self):
        email = self.email_input.text().strip()
        if not email:
            return QMessageBox.warning(self, "Błąd", "Podaj email.")
        dlg = ResetTOTPDialog(email, self)
        if dlg.exec() == QtWidgets.QDialog.Accepted and dlg.totp_uri:
            SetupTOTPDialog(dlg.totp_uri, email, self).exec()
            self.totp_input.setVisible(True)
            self.reset_totp_btn.setVisible(False)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = LoginWindow()
    w.show()
    sys.exit(app.exec())
