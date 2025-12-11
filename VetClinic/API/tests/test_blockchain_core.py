from vetclinic_api.blockchain.core import (
    InMemoryStorage,
    Transaction,
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


def test_mine_block_moves_txs_from_mempool_to_chain():
    storage = InMemoryStorage()

    storage.add_transaction(Transaction(sender="a", recipient="b", amount=1.0))
    storage.add_transaction(Transaction(sender="c", recipient="d", amount=2.0))

    old_chain = storage.get_chain()
    old_height = len(old_chain) - 1

    block = mine_block(storage)

    new_chain = storage.get_chain()
    assert len(new_chain) == old_height + 2  # genesis + nowy blok
    assert new_chain[-1].index == old_chain[-1].index + 1

    assert storage.get_mempool() == []

    block_hash = compute_block_hash(block)
    assert block_hash.startswith("0000")
