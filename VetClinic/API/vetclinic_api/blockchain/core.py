from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from vetclinic_api.core.database import SessionLocal
from vetclinic_api.models_blockchain import BlockDB, TransactionDB
from vetclinic_api.crypto.ed25519 import (
    load_leader_keys_from_env,
    sign_message,
    verify_signature,
)

DIFFICULTY_PREFIX = "0000"


class TxPayload(BaseModel):
    sender: str
    recipient: str
    amount: Decimal


class Transaction(BaseModel):
    id: str
    payload: TxPayload
    sender_pub: str
    signature: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_datetime(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


class Block(BaseModel):
    index: int
    previous_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transactions: List[Transaction]
    nonce: int = 0
    merkle_root: str = ""
    leader_sig: str = ""


class BlockchainState(BaseModel):
    chain: List[Block] = Field(default_factory=list)
    mempool: List[Transaction] = Field(default_factory=list)


class BlockProposal(BaseModel):
    block: Block
    hash: str


def compute_merkle_root(txs: List[Transaction]) -> str:
    if not txs:
        return hashlib.sha256(b"").hexdigest()

    h = hashlib.sha256()
    for tx in txs:
        h.update(tx.id.encode("utf-8"))
    return h.hexdigest()


def block_header_bytes(block: Block) -> bytes:
    header = {
        "index": block.index,
        "previous_hash": block.previous_hash,
        "timestamp": block.timestamp.isoformat(),
        "merkle_root": block.merkle_root,
        "nonce": block.nonce,
    }
    return json.dumps(header, sort_keys=True).encode("utf-8")


def compute_block_hash(block: Block) -> str:
    data = (
        str(block.index)
        + block.previous_hash
        + block.timestamp.isoformat()
        + block.merkle_root
        + str(block.nonce)
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def is_valid_new_block(previous: Block, new: Block) -> bool:
    if new.index != previous.index + 1:
        return False
    if new.previous_hash != compute_block_hash(previous):
        return False
    if compute_merkle_root(new.transactions) != new.merkle_root:
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
                merkle_root=compute_merkle_root([]),
                leader_sig="",
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
                        id=t.tx_id,
                        payload=TxPayload.model_validate_json(t.payload),
                        sender_pub=t.sender_pub,
                        signature=t.signature,
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
                        merkle_root=b.merkle_root,
                        leader_sig=b.leader_sig,
                    )
                )

            if not result:
                genesis = Block(
                    index=0,
                    previous_hash="0" * 64,
                    transactions=[],
                    nonce=0,
                    merkle_root=compute_merkle_root([]),
                    leader_sig="",
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
                merkle_root=block.merkle_root,
                leader_sig=block.leader_sig,
            )
            db.add(block_db)
            db.flush()
            for tx in block.transactions:
                existing = (
                    db.query(TransactionDB)
                    .filter(TransactionDB.tx_id == tx.id)
                    .one_or_none()
                )
                if existing:
                    existing.block_id = block_db.id
                    existing.payload = tx.payload.model_dump_json()
                    existing.sender_pub = tx.sender_pub
                    existing.signature = tx.signature
                    existing.timestamp = tx.timestamp
                    existing.committed = True
                else:
                    tx_db = TransactionDB(
                        block_id=block_db.id,
                        tx_id=tx.id,
                        payload=tx.payload.model_dump_json(),
                        sender_pub=tx.sender_pub,
                        signature=tx.signature,
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
                    id=t.tx_id,
                    payload=TxPayload.model_validate_json(t.payload),
                    sender_pub=t.sender_pub,
                    signature=t.signature,
                    timestamp=t.timestamp,
                )
                for t in pending
            ]

    def add_transaction(self, tx: Transaction) -> None:
        with self._session() as db:
            try:
                tx_db = TransactionDB(
                    tx_id=tx.id,
                    payload=tx.payload.model_dump_json(),
                    sender_pub=tx.sender_pub,
                    signature=tx.signature,
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
    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)
    return proposal.block


def build_block_proposal(storage: Storage) -> BlockProposal:
    chain = storage.get_chain()
    mempool = storage.get_mempool()

    if not mempool:
        raise ValueError("No transactions to mine")

    previous = chain[-1]
    previous_hash = compute_block_hash(previous)
    index = previous.index + 1
    nonce = 0
    timestamp = datetime.utcnow()
    merkle_root = compute_merkle_root(mempool)

    while True:
        candidate = Block(
            index=index,
            previous_hash=previous_hash,
            transactions=mempool,
            timestamp=timestamp,
            nonce=nonce,
            merkle_root=merkle_root,
            leader_sig="",
        )
        block_hash = compute_block_hash(candidate)
        if block_hash.startswith(DIFFICULTY_PREFIX):
            break
        nonce += 1

    header_bytes = block_header_bytes(candidate)
    keys = load_leader_keys_from_env()
    candidate.leader_sig = sign_message(keys.priv, header_bytes)

    return BlockProposal(block=candidate, hash=block_hash)


def verify_chain(storage: Storage) -> Dict[str, Any]:
    chain = storage.get_chain()
    if not chain:
        return {"valid": True, "height": 0, "errors": []}

    errors: List[dict] = []
    keys = load_leader_keys_from_env()

    for idx, block in enumerate(chain):
        if idx == 0:
            continue

        prev = chain[idx - 1]

        if block.index != prev.index + 1:
            errors.append({"block": block.index, "reason": "index not consecutive"})

        prev_hash = compute_block_hash(prev)
        if block.previous_hash != prev_hash:
            errors.append({"block": block.index, "reason": "previous_hash mismatch"})

        merkle = compute_merkle_root(block.transactions)
        if block.merkle_root != merkle:
            errors.append({"block": block.index, "reason": "invalid merkle_root"})

        header_bytes = block_header_bytes(block)
        if not verify_signature(keys.pub, header_bytes, block.leader_sig):
            errors.append({"block": block.index, "reason": "invalid leader_sig"})

        for tx in block.transactions:
            if not _verify_transaction(tx, keys=keys):
                errors.append(
                    {
                        "block": block.index,
                        "tx": tx.id,
                        "reason": "invalid transaction",
                    }
                )

    return {
        "valid": len(errors) == 0,
        "height": chain[-1].index,
        "errors": errors,
    }


def _verify_transaction(tx: Transaction, *, keys=None) -> bool:
    payload_dict = tx.payload.model_dump(mode="json")
    raw = json.dumps(
        {"payload": payload_dict, "timestamp": tx.timestamp.isoformat()},
        sort_keys=True,
    ).encode("utf-8")

    expected_id = hashlib.sha256(raw).hexdigest()
    if tx.id != expected_id:
        return False

    leader_keys = keys or load_leader_keys_from_env()
    if not verify_signature(leader_keys.pub, raw, tx.signature):
        return False
    return True
