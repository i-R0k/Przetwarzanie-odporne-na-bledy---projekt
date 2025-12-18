from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from vetclinic_api.blockchain.core import (
    Block,
    Transaction,
    TxPayload,
    compute_block_hash,
    compute_merkle_root,
)


def _make_tx(idx: int) -> Transaction:
    payload = TxPayload(
        sender=f"user{idx}",
        recipient=f"dest{idx}",
        amount=Decimal("1.0"),
    )
    return Transaction(
        id=f"tx{idx}",
        payload=payload,
        sender_pub="pub",
        signature=f"sig{idx}",
        timestamp=datetime.utcnow(),
    )


def test_compute_merkle_root_changes_with_transactions():
    txs = [_make_tx(1), _make_tx(2)]
    root1 = compute_merkle_root(txs)
    txs_modified = [_make_tx(1), _make_tx(3)]
    root2 = compute_merkle_root(txs_modified)
    assert root1 != root2


def test_compute_block_hash_depends_on_header_only():
    txs = [_make_tx(1)]
    block = Block(
        index=1,
        previous_hash="0" * 64,
        timestamp=datetime.utcnow(),
        transactions=txs,
        nonce=5,
        merkle_root=compute_merkle_root(txs),
        leader_sig="",
    )
    hash1 = compute_block_hash(block)
    hash2 = compute_block_hash(block)
    assert hash1 == hash2

    block_modified = block.model_copy(update={"nonce": block.nonce + 1})
    assert compute_block_hash(block_modified) != hash1
