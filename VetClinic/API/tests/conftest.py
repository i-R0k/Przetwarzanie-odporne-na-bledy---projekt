from __future__ import annotations

import pytest

from vetclinic_api.crypto.ed25519 import generate_keypair


@pytest.fixture(autouse=True)
def leader_keys_env(monkeypatch):
    """
    Ensure leader keys are always available for endpoints that require signing.
    """
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)
