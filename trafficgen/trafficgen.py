import os
import random
import time

import requests

API_ADMIN = os.getenv("ADMIN_API", "http://node1:8000")
LEADER = os.getenv("LEADER_URL", "http://node1:8000")
NODES = os.getenv(
    "NODES",
    "http://node1:8000,http://node2:8000,http://node3:8000,http://node4:8000,http://node5:8000,http://node6:8000",
).split(",")

SESSION = requests.Session()
SESSION.timeout = 2.0


def get_state():
    try:
        r = SESSION.get(f"{API_ADMIN}/admin/network/sim", timeout=2.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        # if admin API is temporarily unavailable, reduce traffic
        return {"traffic_enabled": True, "traffic_rps": 0.5, "chaos_enabled": False}


def submit_tx():
    payload_ok = {
        "sender": "alice",
        "recipient": "bob",
        "amount": round(random.uniform(0.1, 50.0), 2),
    }
    payload_bad = {"sender": "alice"}  # celowo popsute -> 4xx
    body = payload_bad if random.random() < 0.05 else payload_ok
    try:
        SESSION.post(f"{LEADER}/tx/submit", json=body, timeout=2.0)
    except Exception:
        pass


def hit_status():
    url = random.choice(NODES) + "/chain/status"
    try:
        SESSION.get(url, timeout=2.0)
    except Exception:
        pass


def hit_verify():
    url = random.choice(NODES) + "/chain/verify"
    try:
        SESSION.get(url, timeout=2.0)
    except Exception:
        pass


def mine_distributed():
    try:
        SESSION.post(f"{LEADER}/chain/mine_distributed", timeout=5.0)
    except Exception:
        pass


def main():
    while True:
        state = get_state()
        if not state.get("traffic_enabled", True):
            time.sleep(1.0)
            continue

        rps = float(state.get("traffic_rps", 1.0))
        rps = max(0.1, min(50.0, rps))
        interval = 1.0 / rps

        x = random.random()
        if x < 0.55:
            hit_status()
        elif x < 0.85:
            submit_tx()
        elif x < 0.95:
            hit_verify()
        else:
            mine_distributed()

        time.sleep(interval)


if __name__ == "__main__":
    main()
