from __future__ import annotations

from vetclinic_api.blockchain.core import build_genesis_block, compute_block_hash
from vetclinic_api.metrics import (
    NODE_NAME,
    blockchain_chain_height,
    blockchain_mempool_size,
    set_chain_status,
)


def test_genesis_block_is_deterministic():
    genesis1 = build_genesis_block()
    genesis2 = build_genesis_block()
    assert genesis1.timestamp == genesis2.timestamp
    assert compute_block_hash(genesis1) == compute_block_hash(genesis2)


def test_set_chain_status_sets_gauges():
    set_chain_status(height=5, mempool_size=3, node="test-node")
    assert blockchain_chain_height.labels("test-node")._value.get() == 5
    assert blockchain_mempool_size.labels("test-node")._value.get() == 3

    # default uses NODE_NAME
    set_chain_status(height=7, mempool_size=1)
    assert blockchain_chain_height.labels(NODE_NAME)._value.get() == 7
