import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

API_PATH = Path(__file__).resolve().parent.parent
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

import pytest

from vetclinic_api.crypto.ed25519 import generate_keypair
from vetclinic_api.main import app
import vetclinic_api.blockchain.deps as deps


@pytest.fixture(scope="session", autouse=True)
def _qt_finalize(qapp):
    """
    Trzyma QApplication przez całą sesję i domyka event-loop bez zostawiania śmieci.
    """
    yield
    try:
        qapp.processEvents()
        qapp.quit()
        qapp.processEvents()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _leader_keys_env(monkeypatch):
    priv_b64, pub_b64 = generate_keypair()
    monkeypatch.setenv("LEADER_PRIV_KEY", priv_b64)
    monkeypatch.setenv("LEADER_PUB_KEY", pub_b64)


@pytest.fixture(autouse=True)
def _clean_dependency_overrides():
    """
    Ensure dependency overrides from one test do not leak into another.
    """
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _fresh_storage():
    """
    Reset storage reference before each test so DB state does not leak.
    """
    deps._storage = None
    yield
