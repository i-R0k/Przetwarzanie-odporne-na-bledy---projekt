import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QMessageBox
pytestmark = pytest.mark.gui

# ============== ZMIANA HASŁA ==============
@patch("vetclinic_gui.windows.auth.password_dialogs.requests.post")
def test_change_password_success(mock_post, qapp):
    from vetclinic_gui.windows.auth.password_dialogs import ChangePasswordDialog
    dialog = ChangePasswordDialog(email="user@test.com", otp_code="123456")
    dialog.new_pwd.setText("haslo123")
    dialog.confirm.setText("haslo123")
    mock_post.return_value.status_code = 200
    with patch.object(QMessageBox, "information") as infomock:
        dialog.attempt_change()
        assert mock_post.called
        assert infomock.called

@patch("vetclinic_gui.windows.auth.password_dialogs.requests.post")
def test_change_password_mismatch_or_empty(mock_post, qapp):
    from vetclinic_gui.windows.auth.password_dialogs import ChangePasswordDialog
    dialog = ChangePasswordDialog(email="u@a.pl", otp_code="xyz")
    dialog.new_pwd.setText("abc")
    dialog.confirm.setText("def")
    with patch.object(QMessageBox, "warning") as warnmock:
        dialog.attempt_change()
        assert warnmock.called
    dialog.new_pwd.setText("")
    dialog.confirm.setText("")
    with patch.object(QMessageBox, "warning") as warnmock2:
        dialog.attempt_change()
        assert warnmock2.called

@patch("vetclinic_gui.windows.auth.password_dialogs.requests.post")
def test_change_password_error_api(mock_post, qapp):
    from vetclinic_gui.windows.auth.password_dialogs import ChangePasswordDialog
    dialog = ChangePasswordDialog(email="u@a.pl", otp_code="xyz")
    dialog.new_pwd.setText("haslo123")
    dialog.confirm.setText("haslo123")
    mock_post.return_value.status_code = 400
    mock_post.return_value.json.return_value = {"detail": "Błąd api"}
    with patch.object(QMessageBox, "warning") as warnmock:
        dialog.attempt_change()
        assert warnmock.called

# ============= RESET TOTP + ZMIANA HASŁA =============

@patch("vetclinic_gui.windows.auth.password_dialogs.requests.post")
def test_reset_totp_success(mock_post, qapp):
    from vetclinic_gui.windows.auth.password_dialogs import ResetTOTPDialog
    dialog = ResetTOTPDialog(email="u@a.pl")
    dialog.old_pwd.setText("starehaslo")
    dialog.new_pwd.setText("nowehaslo")
    dialog.confirm.setText("nowehaslo")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"totp_uri": "otpauth://..."}
    with patch.object(QMessageBox, "information") as infomock:
        dialog.attempt_reset()
        assert infomock.called
        assert dialog.totp_uri == "otpauth://..."

@patch("vetclinic_gui.windows.auth.password_dialogs.requests.post")
def test_reset_totp_missing_or_mismatch(mock_post, qapp):
    from vetclinic_gui.windows.auth.password_dialogs import ResetTOTPDialog
    dialog = ResetTOTPDialog(email="x@a.pl")
    dialog.old_pwd.setText("")
    dialog.new_pwd.setText("abc")
    dialog.confirm.setText("def")
    with patch.object(QMessageBox, "warning") as warnmock:
        dialog.attempt_reset()
        assert warnmock.called

@patch("vetclinic_gui.windows.auth.password_dialogs.requests.post")
def test_reset_totp_error_api(mock_post, qapp):
    from vetclinic_gui.windows.auth.password_dialogs import ResetTOTPDialog
    dialog = ResetTOTPDialog(email="z@a.pl")
    dialog.old_pwd.setText("xxx")
    dialog.new_pwd.setText("yyy")
    dialog.confirm.setText("yyy")
    mock_post.return_value.status_code = 401
    mock_post.return_value.json.return_value = {"detail": "Błąd API"}
    with patch.object(QMessageBox, "warning") as warnmock:
        dialog.attempt_reset()
        assert warnmock.called

# ============== SETUP TOTP DIALOG ==============

@patch("vetclinic_gui.windows.auth.setup_totp_dialog.requests.post")
def test_setup_totp_confirm_success(mock_post, qapp):
    from vetclinic_gui.windows.auth.setup_totp_dialog import SetupTOTPDialog
    dialog = SetupTOTPDialog(totp_uri="otpauth://xxx", email="u@b.pl")
    dialog.totp_input.setText("123456")
    mock_post.return_value.status_code = 200
    with patch.object(QMessageBox, "information") as infomock:
        dialog.confirm_totp()
        assert infomock.called

@patch("vetclinic_gui.windows.auth.setup_totp_dialog.requests.post")
def test_setup_totp_confirm_empty_and_error(mock_post, qapp):
    from vetclinic_gui.windows.auth.setup_totp_dialog import SetupTOTPDialog
    dialog = SetupTOTPDialog(totp_uri="otpauth://xxx", email="u@b.pl")
    dialog.totp_input.setText("")
    with patch.object(QMessageBox, "warning") as warnmock:
        dialog.confirm_totp()
        assert warnmock.called
    # Test niepoprawny kod
    dialog.totp_input.setText("111222")
    mock_post.return_value.status_code = 400
    with patch.object(QMessageBox, "warning") as warnmock2:
        dialog.confirm_totp()
        assert warnmock2.called
        assert dialog.status_label.text() != ""

# ================== ProportionalImageLabel (opcja) ==================
def test_proportional_image_label(qapp, qtbot):
    from vetclinic_gui.windows.auth.setup_totp_dialog import ProportionalImageLabel
    label = ProportionalImageLabel()
    qtbot.addWidget(label)
    label.resize(200, 200)
    label.show()
    qtbot.waitExposed(label)
    # Sprawdź inicjalizację i sizeHint
    size = label.sizeHint()
    assert size.width() > 0
    assert size.height() > 0
