from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


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
        self._chain.append(block)

    def get_mempool(self) -> List[Transaction]:
        return list(self._mempool)

    def add_transaction(self, tx: Transaction) -> None:
        self._mempool.append(tx)

    def clear_mempool(self) -> None:
        self._mempool.clear()
