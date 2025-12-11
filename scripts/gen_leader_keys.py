from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.crypto.ed25519 import generate_keypair  # noqa: E402


def main() -> None:
    priv, pub = generate_keypair()
    print(f"LEADER_PRIV_KEY={priv}")
    print(f"LEADER_PUB_KEY={pub}")


if __name__ == "__main__":
    main()
