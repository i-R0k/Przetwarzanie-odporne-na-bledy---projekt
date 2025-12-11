from __future__ import annotations

import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from vetclinic_api.crypto.ed25519 import (
    generate_keypair,
    sign_message,
    verify_signature,
)


def _load_keys(priv_b64: str, pub_b64: str) -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    priv = Ed25519PrivateKey.from_private_bytes(base64.b64decode(priv_b64))
    pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))
    return priv, pub


def test_generate_keypair_sign_and_verify():
    priv_b64, pub_b64 = generate_keypair()
    priv, pub = _load_keys(priv_b64, pub_b64)
    message = b"hello blockchain"
    signature = sign_message(priv, message)
    assert verify_signature(pub, message, signature) is True


def test_verify_signature_fails_on_modified_message():
    priv_b64, pub_b64 = generate_keypair()
    priv, pub = _load_keys(priv_b64, pub_b64)
    signature = sign_message(priv, b"original")
    assert verify_signature(pub, b"modified", signature) is False
