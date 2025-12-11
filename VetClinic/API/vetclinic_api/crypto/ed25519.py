from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


@dataclass
class LeaderKeys:
    priv: Ed25519PrivateKey
    pub: Ed25519PublicKey


def generate_keypair() -> tuple[str, str]:
    """
    Generates an Ed25519 keypair and returns both keys encoded as base64 strings.
    """
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return (
        base64.b64encode(priv_bytes).decode("ascii"),
        base64.b64encode(pub_bytes).decode("ascii"),
    )


def load_leader_keys_from_env() -> LeaderKeys:
    priv_b64 = os.getenv("LEADER_PRIV_KEY")
    pub_b64 = os.getenv("LEADER_PUB_KEY")
    if not priv_b64 or not pub_b64:
        raise RuntimeError("Leader keys not configured in environment")

    priv_raw = base64.b64decode(priv_b64)
    pub_raw = base64.b64decode(pub_b64)

    priv = Ed25519PrivateKey.from_private_bytes(priv_raw)
    pub = Ed25519PublicKey.from_public_bytes(pub_raw)

    return LeaderKeys(priv=priv, pub=pub)


def sign_message(priv: Ed25519PrivateKey, data: bytes) -> str:
    sig = priv.sign(data)
    return base64.b64encode(sig).decode("ascii")


def verify_signature(pub: Ed25519PublicKey, data: bytes, signature_b64: str) -> bool:
    try:
        sig = base64.b64decode(signature_b64)
        pub.verify(sig, data)
        return True
    except Exception:
        return False
