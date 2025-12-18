import hashlib
import json
from datetime import datetime
from decimal import Decimal

from vetclinic_api.blockchain.core import (
    InMemoryStorage,
    Transaction,
    TxPayload,
    compute_block_hash,
    mine_block,
)


def test_genesis_block_exists():
    storage = InMemoryStorage()
    chain = storage.get_chain()

    assert len(chain) == 1
    genesis = chain[0]
    assert genesis.index == 0
    assert genesis.previous_hash == "0" * 64
    assert len(genesis.transactions) == 0

    block_hash = compute_block_hash(genesis)
    assert isinstance(block_hash, str)
    assert len(block_hash) == 64

def _make_transaction(sender: str, recipient: str, amount: float) -> Transaction:
    payload = TxPayload(
        sender=sender,
        recipient=recipient,
        amount=Decimal(str(amount)),
    )
    timestamp = datetime.utcnow()
    raw = json.dumps(
        {
            "payload": payload.model_dump(mode="json"),
            "timestamp": timestamp.isoformat(),
        },
        sort_keys=True,
    ).encode("utf-8")
    tx_id = hashlib.sha256(raw).hexdigest()
    return Transaction(
        id=tx_id,
        payload=payload,
        sender_pub="test-sender-pub",
        signature="test-signature",
        timestamp=timestamp,
    )


def test_mine_block_moves_txs_from_mempool_to_chain():
    storage = InMemoryStorage()

    storage.add_transaction(_make_transaction("a", "b", 1.0))
    storage.add_transaction(_make_transaction("c", "d", 2.0))

    old_chain = storage.get_chain()
    old_height = len(old_chain) - 1

    block = mine_block(storage)

    new_chain = storage.get_chain()
    assert len(new_chain) == old_height + 2  # genesis + nowy blok
    assert new_chain[-1].index == old_chain[-1].index + 1

    assert storage.get_mempool() == []

    block_hash = compute_block_hash(block)
    assert block_hash.startswith("0000")
