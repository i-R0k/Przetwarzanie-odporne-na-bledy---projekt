from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator

from vetclinic_api.blockchain.core import (
    BlockchainState,
    Storage,
    Transaction,
    compute_block_hash,
    mine_block,
)
from vetclinic_api.blockchain.deps import get_storage

router = APIRouter(tags=["blockchain"])


class SubmitTransaction(BaseModel):
    sender: str = Field(min_length=3, max_length=128)
    recipient: str = Field(min_length=3, max_length=128)
    amount: float = Field(gt=0, lt=1e9)

    @validator("sender", "recipient")
    def strip_and_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("value must not be empty")
        return v


@router.post("/tx/submit", status_code=202)
def submit_transaction(
    tx: SubmitTransaction,
    storage: Storage = Depends(get_storage),
):
    transaction = Transaction(**tx.model_dump())
    storage.add_transaction(transaction)
    return {"status": "accepted"}


@router.get("/chain/status")
def chain_status(
    storage: Storage = Depends(get_storage),
):
    chain = storage.get_chain()
    mempool = storage.get_mempool()
    state = BlockchainState(chain=chain, mempool=mempool)

    last_block_hash = compute_block_hash(chain[-1]) if chain else None

    return {
        "height": len(chain) - 1 if chain else -1,
        "last_block_hash": last_block_hash,
        "mempool_size": len(mempool),
        "chain": state.chain,
        "mempool": state.mempool,
    }


@router.post("/chain/mine")
def mine_block_endpoint(
    storage: Storage = Depends(get_storage),
):
    """
    Kopie nowy blok z aktualnego mempoola.
    Jesli mempool jest pusty, zwraca 400.
    """
    try:
        block = mine_block(storage)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    block_hash = compute_block_hash(block)
    return {
        "status": "mined",
        "block_hash": block_hash,
        "block": block,
    }
