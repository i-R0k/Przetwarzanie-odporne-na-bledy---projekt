from __future__ import annotations

import json
from typing import Any, Dict

import requests
from PyQt5 import QtCore, QtWidgets

NODES: Dict[int, str] = {
    1: "http://localhost:8001",
    2: "http://localhost:8002",
    3: "http://localhost:8003",
    4: "http://localhost:8004",
    5: "http://localhost:8005",
    6: "http://localhost:8006",
}
LEADER_ID = 1


class ClusterAdminWidget(QtWidgets.QWidget):
    """
    Panel administracyjny do podglądu klastra blockchain i sterowania FAULT_*.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
        self.refresh_cluster()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Node", "URL", "Height", "Last hash", "Valid", "Faults"]
        )
        self.table.setRowCount(len(NODES))
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        for row, (node_id, url) in enumerate(NODES.items()):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(node_id)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(url))
            for col in range(2, 6):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem("-"))

        layout.addWidget(self.table)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("Odśwież stan klastra")
        self.btn_mine = QtWidgets.QPushButton("Uruchom konsensus (leader)")
        self.btn_send_tx = QtWidgets.QPushButton("Wyślij testową transakcję")
        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_mine)
        btn_row.addWidget(self.btn_send_tx)
        layout.addLayout(btn_row)

        faults_group = QtWidgets.QGroupBox("Symulacja błędów dla wybranego węzła (FAULT_*)")
        fg_layout = QtWidgets.QGridLayout(faults_group)

        self.combo_node = QtWidgets.QComboBox()
        for node_id in NODES.keys():
            self.combo_node.addItem(f"Node {node_id}", node_id)

        self.chk_offline = QtWidgets.QCheckBox("FAULT_OFFLINE")
        self.chk_byzantine = QtWidgets.QCheckBox("FAULT_BYZANTINE")
        self.chk_flapping = QtWidgets.QCheckBox("FAULT_FLAPPING")

        self.spin_slow = QtWidgets.QSpinBox()
        self.spin_slow.setRange(0, 60000)
        self.spin_slow.setSuffix(" ms")

        self.spin_flapping_mod = QtWidgets.QSpinBox()
        self.spin_flapping_mod.setRange(0, 10)

        self.double_drop = QtWidgets.QDoubleSpinBox()
        self.double_drop.setRange(0.0, 1.0)
        self.double_drop.setSingleStep(0.1)
        self.double_drop.setDecimals(2)

        self.btn_load_faults = QtWidgets.QPushButton("Pobierz FAULT_* z węzła")
        self.btn_apply_faults = QtWidgets.QPushButton("Zastosuj FAULT_* na węźle")

        row = 0
        fg_layout.addWidget(QtWidgets.QLabel("Węzeł:"), row, 0)
        fg_layout.addWidget(self.combo_node, row, 1, 1, 3)

        row += 1
        fg_layout.addWidget(self.chk_offline, row, 0)
        fg_layout.addWidget(self.chk_byzantine, row, 1)
        fg_layout.addWidget(self.chk_flapping, row, 2)

        row += 1
        fg_layout.addWidget(QtWidgets.QLabel("FAULT_SLOW_MS:"), row, 0)
        fg_layout.addWidget(self.spin_slow, row, 1)

        row += 1
        fg_layout.addWidget(QtWidgets.QLabel("FAULT_FLAPPING_MOD:"), row, 0)
        fg_layout.addWidget(self.spin_flapping_mod, row, 1)

        row += 1
        fg_layout.addWidget(QtWidgets.QLabel("FAULT_DROP_RPC_PROB:"), row, 0)
        fg_layout.addWidget(self.double_drop, row, 1)

        row += 1
        fg_layout.addWidget(self.btn_load_faults, row, 0, 1, 2)
        fg_layout.addWidget(self.btn_apply_faults, row, 2, 1, 2)

        layout.addWidget(faults_group)
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        self.btn_refresh.clicked.connect(self.refresh_cluster)
        self.btn_mine.clicked.connect(self.mine_distributed)
        self.btn_send_tx.clicked.connect(self.send_test_tx)
        self.btn_load_faults.clicked.connect(self.load_faults_for_selected)
        self.btn_apply_faults.clicked.connect(self.apply_faults_for_selected)

    def _show_error(self, msg: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Błąd", msg)

    def _show_info(self, msg: str) -> None:
        QtWidgets.QMessageBox.information(self, "Info", msg)

    def _get_node_base_url(self, node_id: int) -> str:
        return NODES[node_id].rstrip("/")

    def refresh_cluster(self) -> None:
        for row, (node_id, base_url) in enumerate(NODES.items()):
            height = "-"
            last_hash = "-"
            valid_str = "-"
            faults_desc = ""

            try:
                s_resp = requests.get(f"{base_url}/chain/status", timeout=3.0)
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    height = str(s_data.get("height", "-"))
                    last_hash_full = s_data.get("last_block_hash", "")
                    last_hash = last_hash_full[:10] + "..." if last_hash_full else "-"
                else:
                    faults_desc = f"status HTTP {s_resp.status_code}"
            except Exception as exc:
                faults_desc = f"STATUS ERR: {exc}"

            try:
                v_resp = requests.get(f"{base_url}/chain/verify", timeout=3.0)
                if v_resp.status_code == 200:
                    v_data = v_resp.json()
                    is_valid = bool(v_data.get("valid"))
                    valid_str = "OK" if is_valid else "INVALID"
                    if not is_valid:
                        errs = v_data.get("errors") or []
                        if errs:
                            reason = errs[0].get("reason", "?")
                            faults_desc = (
                                f"{faults_desc}; " if faults_desc else ""
                            ) + f"chain error: {reason}"
                else:
                    faults_desc = (
                        f"{faults_desc}; " if faults_desc else ""
                    ) + f"verify HTTP {v_resp.status_code}"
            except Exception as exc:
                faults_desc = (
                    f"{faults_desc}; " if faults_desc else ""
                ) + f"VERIFY ERR: {exc}"

            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(height))
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(last_hash))
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(valid_str))
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(faults_desc or "-"))

    def mine_distributed(self) -> None:
        base_url = self._get_node_base_url(LEADER_ID)
        url = f"{base_url}/chain/mine_distributed"
        try:
            resp = requests.post(url, json={}, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                self._show_info(f"mine_distributed OK:\n{json.dumps(data, indent=2)}")
            else:
                self._show_error(f"mine_distributed HTTP {resp.status_code}: {resp.text}")
        except Exception as exc:
            self._show_error(f"mine_distributed error: {exc}")
        self.refresh_cluster()

    def send_test_tx(self) -> None:
        node_id = LEADER_ID
        base_url = self._get_node_base_url(node_id)
        url = f"{base_url}/tx/submit"

        sender, ok1 = QtWidgets.QInputDialog.getText(self, "Sender", "Sender:", text="alice")
        if not ok1:
            return
        recipient, ok2 = QtWidgets.QInputDialog.getText(
            self, "Recipient", "Recipient:", text="bob"
        )
        if not ok2:
            return
        amount, ok3 = QtWidgets.QInputDialog.getDouble(
            self, "Amount", "Amount:", 1.0, 0.0, 1e9, 2
        )
        if not ok3:
            return

        payload = {"sender": sender, "recipient": recipient, "amount": amount}

        try:
            resp = requests.post(url, json=payload, timeout=5.0)
            if resp.status_code == 200:
                self._show_info(f"Tx submitted:\n{json.dumps(resp.json(), indent=2)}")
            else:
                self._show_error(f"tx/submit HTTP {resp.status_code}: {resp.text}")
        except Exception as exc:
            self._show_error(f"tx/submit error: {exc}")

        self.refresh_cluster()

    def _get_selected_node_id(self) -> int:
        idx = self.combo_node.currentIndex()
        return int(self.combo_node.itemData(idx))

    def load_faults_for_selected(self) -> None:
        node_id = self._get_selected_node_id()
        base_url = self._get_node_base_url(node_id)
        url = f"{base_url}/admin/faults"
        try:
            resp = requests.get(url, timeout=3.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self._show_error(f"/admin/faults error: {exc}")
            return

        self.chk_offline.setChecked(bool(data.get("offline")))
        self.chk_byzantine.setChecked(bool(data.get("byzantine")))
        self.chk_flapping.setChecked(bool(data.get("flapping")))
        self.spin_slow.setValue(int(data.get("slow_ms") or 0))
        self.spin_flapping_mod.setValue(int(data.get("flapping_mod") or 0))
        self.double_drop.setValue(float(data.get("drop_rpc_prob") or 0.0))

    def apply_faults_for_selected(self) -> None:
        node_id = self._get_selected_node_id()
        base_url = self._get_node_base_url(node_id)
        url = f"{base_url}/admin/faults"

        payload: Dict[str, Any] = {
            "offline": self.chk_offline.isChecked(),
            "byzantine": self.chk_byzantine.isChecked(),
            "flapping": self.chk_flapping.isChecked(),
            "slow_ms": self.spin_slow.value(),
            "flapping_mod": self.spin_flapping_mod.value(),
            "drop_rpc_prob": self.double_drop.value(),
        }

        try:
            resp = requests.put(url, json=payload, timeout=5.0)
            resp.raise_for_status()
            self._show_info(f"FAULT_* zaktualizowane:\n{json.dumps(resp.json(), indent=2)}")
        except Exception as exc:
            self._show_error(f"/admin/faults PUT error: {exc}")

        self.refresh_cluster()
