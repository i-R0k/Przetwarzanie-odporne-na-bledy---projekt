import pathlib
print(">>> Ładuję router blockchain z:", pathlib.Path(__file__).resolve())


from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from vetclinic_api.blockchain.core import (
    BlockchainState,
    Storage,
    Transaction,
    compute_block_hash,
)
from vetclinic_api.blockchain.deps import get_storage

router = APIRouter(tags=["blockchain"])


class SubmitTransaction(BaseModel):
    sender: str
    recipient: str
    amount: float = Field(gt=0, description="Dodatnia kwota")


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
