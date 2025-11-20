from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from vetclinic_api.core.database import SessionLocal
from vetclinic_api.models_blockchain import BlockDB, TransactionDB

DIFFICULTY_PREFIX = "0000"


class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Block(BaseModel):
    index: int
    previous_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transactions: List[Transaction]
    nonce: int = 0


class BlockchainState(BaseModel):
    chain: List[Block] = Field(default_factory=list)
    mempool: List[Transaction] = Field(default_factory=list)


def compute_block_hash(block: Block) -> str:
    payload = json.dumps(block.dict(), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_valid_new_block(previous: Block, new: Block) -> bool:
    if new.index != previous.index + 1:
        return False
    if new.previous_hash != compute_block_hash(previous):
        return False
    block_hash = compute_block_hash(new)
    return block_hash.startswith(DIFFICULTY_PREFIX)


class Storage(ABC):
    @abstractmethod
    def get_chain(self) -> List[Block]:
        raise NotImplementedError

    @abstractmethod
    def add_block(self, block: Block) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_mempool(self) -> List[Transaction]:
        raise NotImplementedError

    @abstractmethod
    def add_transaction(self, tx: Transaction) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_mempool(self) -> None:
        raise NotImplementedError


class InMemoryStorage(Storage):
    def __init__(self) -> None:
        self._chain: List[Block] = []
        self._mempool: List[Transaction] = []

        if not self._chain:
            genesis = Block(
                index=0,
                previous_hash="0" * 64,
                transactions=[],
                nonce=0,
            )
            self._chain.append(genesis)

    def get_chain(self) -> List[Block]:
        return list(self._chain)

    def add_block(self, block: Block) -> None:
        last = self._chain[-1]
        if not is_valid_new_block(last, block):
            raise ValueError("Invalid block")
        self._chain.append(block)
        self._mempool.clear()

    def get_mempool(self) -> List[Transaction]:
        return list(self._mempool)

    def add_transaction(self, tx: Transaction) -> None:
        self._mempool.append(tx)

    def clear_mempool(self) -> None:
        self._mempool.clear()


class SQLAlchemyStorage(Storage):
    def __init__(self, session_factory: type = SessionLocal) -> None:
        self._session_factory = session_factory

    def _session(self) -> Session:
        return self._session_factory()

    def get_chain(self) -> List[Block]:
        with self._session() as db:
            blocks_db = db.query(BlockDB).order_by(BlockDB.index.asc()).all()
            result: List[Block] = []
            for b in blocks_db:
                txs = [
                    Transaction(
                        sender=t.sender,
                        recipient=t.recipient,
                        amount=t.amount,
                        timestamp=t.timestamp,
                    )
                    for t in sorted(b.transactions, key=lambda t: t.id)
                ]
                result.append(
                    Block(
                        index=b.index,
                        previous_hash=b.previous_hash,
                        timestamp=b.timestamp,
                        transactions=txs,
                        nonce=b.nonce,
                    )
                )

            if not result:
                genesis = Block(
                    index=0,
                    previous_hash="0" * 64,
                    transactions=[],
                    nonce=0,
                )
                self._persist_block(genesis, db=db)
                result = [genesis]
            return result

    def _persist_block(self, block: Block, db: Session | None = None) -> None:
        close = False
        if db is None:
            db = self._session()
            close = True
        try:
            block_hash = compute_block_hash(block)
            block_db = BlockDB(
                index=block.index,
                previous_hash=block.previous_hash,
                timestamp=block.timestamp,
                nonce=block.nonce,
                hash=block_hash,
            )
            db.add(block_db)
            db.flush()
            for tx in block.transactions:
                tx_db = TransactionDB(
                    block_id=block_db.id,
                    sender=tx.sender,
                    recipient=tx.recipient,
                    amount=tx.amount,
                    timestamp=tx.timestamp,
                    committed=True,
                )
                db.add(tx_db)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            if close:
                db.close()

    def add_block(self, block: Block) -> None:
        chain = self.get_chain()
        last = chain[-1]
        if not is_valid_new_block(last, block):
            raise ValueError("Invalid block")
        with self._session() as db:
            self._persist_block(block, db=db)
            db.query(TransactionDB).filter(TransactionDB.committed.is_(False)).delete()
            db.commit()

    def get_mempool(self) -> List[Transaction]:
        with self._session() as db:
            pending = (
                db.query(TransactionDB)
                .filter(TransactionDB.committed.is_(False))
                .order_by(TransactionDB.id.asc())
                .all()
            )
            return [
                Transaction(
                    sender=t.sender,
                    recipient=t.recipient,
                    amount=t.amount,
                    timestamp=t.timestamp,
                )
                for t in pending
            ]

    def add_transaction(self, tx: Transaction) -> None:
        with self._session() as db:
            try:
                tx_db = TransactionDB(
                    sender=tx.sender,
                    recipient=tx.recipient,
                    amount=tx.amount,
                    timestamp=tx.timestamp,
                    committed=False,
                )
                db.add(tx_db)
                db.commit()
            except Exception:
                db.rollback()
                raise

    def clear_mempool(self) -> None:
        with self._session() as db:
            db.query(TransactionDB).filter(TransactionDB.committed.is_(False)).delete()
            db.commit()


def mine_block(storage: Storage) -> Block:
    chain = storage.get_chain()
    mempool = storage.get_mempool()

    if not mempool:
        raise ValueError("No transactions to mine")

    previous = chain[-1]
    previous_hash = compute_block_hash(previous)
    index = previous.index + 1
    nonce = 0

    while True:
        candidate = Block(
            index=index,
            previous_hash=previous_hash,
            transactions=mempool,
            nonce=nonce,
        )
        block_hash = compute_block_hash(candidate)
        if block_hash.startswith(DIFFICULTY_PREFIX):
            break
        nonce += 1

    storage.add_block(candidate)
    return candidate
