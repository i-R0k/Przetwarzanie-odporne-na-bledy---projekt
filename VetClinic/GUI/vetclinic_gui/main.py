import sys
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
from vetclinic_gui.windows.main_window import MainWindow
from vetclinic_gui.services.clients_service import ClientService

def main():
    app = QApplication(sys.argv)

    # 1) Wybór roli
    roles = ["Administrator", "Recepcjonista", "Lekarz", "Klient"]
    role_name, ok = QInputDialog.getItem(
        None,
        "Wybór grupy użytkownika",
        "Zaloguj się jako:",
        roles,
        0,
        False
    )
    if not ok:
        QMessageBox.information(None, "Koniec", "Nie wybrano roli. Kończę.")
        sys.exit(0)

    role_map = {
        "Administrator": "admin",
        "Recepcjonista": "receptionist",
        "Lekarz":        "doctor",
        "Klient":        "client"
    }
    user_role = role_map[role_name]

    doctor_id = None
    client_id = None

    # 2a) Jeżeli to lekarz – poproś o ID
    if user_role == "doctor":
        doctor_id, ok = QInputDialog.getInt(
            None,
            "ID lekarza",
            "Podaj identyfikator lekarza (liczba całkowita):",
            value=1,
            min=1,
            max=9999,
            step=1
        )
        if not ok:
            QMessageBox.information(None, "Koniec", "Nie podano ID lekarza. Kończę.")
            sys.exit(0)

    # 2b) Jeżeli to klient – wyświetl listę klientów do wyboru
    if user_role == "client":
        try:
            clients = ClientService.list() or []
        except Exception as e:
            QMessageBox.critical(None, "Błąd", f"Nie udało się pobrać listy klientów:\n{e}")
            sys.exit(1)

        # Przygotuj listę w formacie "Imię Nazwisko (ID)"
        client_labels = [f"{c.first_name} {c.last_name} (#{c.id})" for c in clients]
        if not client_labels:
            QMessageBox.information(None, "Brak klientów", "Brak zarejestrowanych klientów w systemie.")
            sys.exit(0)

        selected_label, ok = QInputDialog.getItem(
            None,
            "Wybór klienta",
            "Wybierz klienta:",
            client_labels,
            0,
            False
        )
        if not ok:
            QMessageBox.information(None, "Koniec", "Nie wybrano klienta. Kończę.")
            sys.exit(0)

        # Parsuj ID z wybranego tekstu "Imię Nazwisko (#ID)"
        try:
            client_id = int(selected_label.split("#")[-1].rstrip(")"))
        except ValueError:
            QMessageBox.critical(None, "Błąd", "Nieprawidłowy format wybranego klienta.")
            sys.exit(1)

    # 3) Uruchom główne okno, przekazując user_role, doctor_id i client_id
    window = MainWindow(user_role=user_role, doctor_id=doctor_id, client_id=client_id)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
