import sys

import pytest


def test_entrypoint_main_doctor(monkeypatch, qapp):
    from vetclinic_gui import main as main_mod

    # Reuse shared qapp and short-circuit exec/exit.
    monkeypatch.setattr(main_mod, "QApplication", lambda argv: qapp)
    monkeypatch.setattr(qapp, "exec", lambda: 0)
    monkeypatch.setattr(main_mod.sys, "exit", lambda code=0: None)
    monkeypatch.setattr(main_mod.QInputDialog, "getItem", lambda *a, **k: ("Lekarz", True))
    monkeypatch.setattr(main_mod.QInputDialog, "getInt", lambda *a, **k: (7, True))
    monkeypatch.setattr(main_mod.ClientService, "list", lambda: [])

    created = {}

    class DummyMainWindow:
        def __init__(self, user_role, doctor_id=None, client_id=None):
            created.update(role=user_role, doctor=doctor_id, client=client_id)

        def show(self):
            created["shown"] = True

    monkeypatch.setattr(main_mod, "MainWindow", DummyMainWindow)

    main_mod.main()

    assert created["role"] == "doctor"
    assert created["doctor"] == 7
    assert created.get("shown") is True


def test_entrypoint_main_client(monkeypatch, qapp):
    from vetclinic_gui import main as main_mod

    # First getItem returns role, second returns client selection.
    calls = iter([("Klient", True), ("Jan Kowalski (#5)", True)])
    monkeypatch.setattr(main_mod.QInputDialog, "getItem", lambda *a, **k: next(calls))
    monkeypatch.setattr(main_mod, "QApplication", lambda argv: qapp)
    monkeypatch.setattr(qapp, "exec", lambda: 0)
    monkeypatch.setattr(main_mod.sys, "exit", lambda code=0: None)
    monkeypatch.setattr(main_mod.QInputDialog, "getInt", lambda *a, **k: (1, True))

    class DummyClient:
        def __init__(self, cid, first, last):
            self.id = cid
            self.first_name = first
            self.last_name = last

    monkeypatch.setattr(main_mod.ClientService, "list", lambda: [DummyClient(5, "Jan", "Kowalski")])

    captured = {}

    class DummyMainWindow:
        def __init__(self, user_role, doctor_id=None, client_id=None):
            captured.update(role=user_role, doctor=doctor_id, client=client_id)

        def show(self):
            captured["shown"] = True

    monkeypatch.setattr(main_mod, "MainWindow", DummyMainWindow)

    main_mod.main()

    assert captured["role"] == "client"
    assert captured["client"] == 5
    assert captured.get("shown") is True


def test_entrypoint_dunder_main(monkeypatch, qapp):
    from vetclinic_gui import __main__ as entry

    monkeypatch.setattr(entry, "QApplication", lambda argv: qapp)
    monkeypatch.setattr(qapp, "exec", lambda: 0)
    monkeypatch.setattr(entry.sys, "exit", lambda code=0: None)

    shown = {}

    class DummyLogin:
        def __init__(self):
            shown["instantiated"] = True

        def show(self):
            shown["shown"] = True

    monkeypatch.setattr(entry, "LoginWindow", DummyLogin)
    entry.main()
    assert shown.get("shown") is True


def test_qt_compat_aliases():
    from vetclinic_gui.qt_compat import Qt

    assert hasattr(Qt, "AlignCenter")
    assert Qt.AlignCenter == Qt.AlignmentFlag.AlignCenter


def test_blockchain_service_http(monkeypatch):
    from vetclinic_gui.services import blockchain_service as svc

    class Resp:
        def __init__(self, status=200, payload=None):
            self.status_code = status
            self._payload = payload or {}

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("error")

    posted = {}
    def fake_post(url, json=None, timeout=0):
        posted["data"] = (url, json)
        return Resp(payload={"ok": True})

    monkeypatch.setattr(svc.requests, "post", fake_post)
    monkeypatch.setattr(
        svc.requests, "get", lambda url, timeout=0: Resp(payload={"id": 10})
    )

    assert svc.add_record_on_chain(10, "hash", owner="me")["ok"] is True
    assert posted["data"][0].endswith("/blockchain/record")
    assert posted["data"][1]["owner"] == "me"

    record = svc.get_record_on_chain(10)
    assert record["id"] == 10

    # 404 path returns None
    monkeypatch.setattr(svc.requests, "get", lambda url, timeout=0: Resp(status=404))
    assert svc.get_record_on_chain(99) is None

    # list by owner
    monkeypatch.setattr(
        svc.requests,
        "get",
        lambda url, timeout=0: Resp(payload={"record_ids": [5]}),
    )
    assert svc.get_records_by_owner("x") == [5]


def test_appointments_service_free_slots():
    from vetclinic_gui.services import appointments_service as svc

    assert svc.AppointmentService.get_free_slots(1, "bad-date") == []
    # Sunday
    assert svc.AppointmentService.get_free_slots(1, "2024-09-29") == []


def test_cluster_admin_widget_smoke(monkeypatch, qtbot):
    from vetclinic_gui.windows.Admin.cluster_admin_widget import ClusterAdminWidget, NODES

    monkeypatch.setattr(ClusterAdminWidget, "refresh_cluster", lambda self: None)
    monkeypatch.setattr(ClusterAdminWidget, "_load_network_state", lambda self: None)

    widget = ClusterAdminWidget()
    qtbot.addWidget(widget)
    assert widget.table.rowCount() == len(NODES)


def test_login_window_builds(monkeypatch, qtbot):
    from vetclinic_gui.windows.login_window import LoginWindow

    # Avoid real network/auth calls by stubbing service.
    class DummyAuth:
        def __init__(self):
            self.logged_in = False

    monkeypatch.setattr("vetclinic_gui.windows.login_window.AuthService", lambda: DummyAuth())
    win = LoginWindow()
    qtbot.addWidget(win)
    assert win.windowTitle()
