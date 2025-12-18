from PyQt6 import QtWidgets
import requests
from PyQt6.QtWidgets import QMessageBox

API_CHANGE_PWD_URL = "http://127.0.0.1:8000/users/change-password"

class ChangePasswordDialog(QtWidgets.QDialog):
    """Dialog do wymuszonej zmiany hasła (pierwsze logowanie)."""
    def __init__(self, email, otp_code, parent=None):
        super().__init__(parent)
        self.email    = email
        self.otp_code = otp_code
        self.setWindowTitle("Zmiana hasła")
        self.resize(300, 180)
        layout = QtWidgets.QFormLayout(self)
        self.new_pwd = QtWidgets.QLineEdit(); self.new_pwd.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.confirm = QtWidgets.QLineEdit(); self.confirm.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout.addRow("Nowe hasło:", self.new_pwd)
        layout.addRow("Powtórz hasło:", self.confirm)
        btn = QtWidgets.QPushButton("Zmień hasło")
        btn.clicked.connect(self.attempt_change)
        layout.addRow(btn)

    def attempt_change(self):
        n = self.new_pwd.text().strip(); c = self.confirm.text().strip()
        if not n or n != c:
            QMessageBox.warning(self, "Błąd", "Hasła są puste lub się nie zgadzają.")
            return
        resp = requests.post(API_CHANGE_PWD_URL, json={
            "email": self.email,
            "old_password": self.otp_code,
            "new_password": n,
            "reset_totp": False
        })
        if resp.status_code == 200:
            QMessageBox.information(self, "OK", "Hasło zmieniono; teraz skonfiguruj TOTP.")
            self.accept()
        else:
            QMessageBox.warning(self, "Błąd", resp.json().get("detail",""))

class ResetTOTPDialog(QtWidgets.QDialog):
    """Dialog do resetu TOTP + zmiany hasła (utrata dostępu)."""
    def __init__(self, email, parent=None):
        super().__init__(parent)
        self.email    = email
        self.totp_uri = None
        self.setWindowTitle("Reset TOTP i zmiana hasła")
        self.resize(350, 220)
        layout = QtWidgets.QFormLayout(self)
        self.old_pwd = QtWidgets.QLineEdit(); self.old_pwd.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.new_pwd = QtWidgets.QLineEdit(); self.new_pwd.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.confirm = QtWidgets.QLineEdit(); self.confirm.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout.addRow("Obecne hasło:", self.old_pwd)
        layout.addRow("Nowe hasło:", self.new_pwd)
        layout.addRow("Powtórz nowe hasło:", self.confirm)
        btn = QtWidgets.QPushButton("Resetuj TOTP + zmień hasło")
        btn.clicked.connect(self.attempt_reset)
        layout.addRow(btn)

    def attempt_reset(self):
        o = self.old_pwd.text().strip()
        n = self.new_pwd.text().strip()
        c = self.confirm.text().strip()
        if not o or not n or n != c:
            QMessageBox.warning(self, "Błąd", "Sprawdź wpisane hasła.")
            return
        resp = requests.post(API_CHANGE_PWD_URL, json={
            "email": self.email,
            "old_password": o,
            "new_password": n,
            "reset_totp": True
        })
        if resp.status_code == 200:
            self.totp_uri = resp.json().get("totp_uri")
            QMessageBox.information(self, "OK", "Hasło zmieniono i TOTP zresetowano.")
            self.accept()
        else:
            QMessageBox.warning(self, "Błąd", resp.json().get("detail",""))
