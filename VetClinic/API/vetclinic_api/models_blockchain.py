from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from vetclinic_api.core.database import Base


class BlockDB(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, unique=True, nullable=False)
    previous_hash = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    nonce = Column(Integer, nullable=False)
    hash = Column(String(128), nullable=False)
    merkle_root = Column(String(128), nullable=True, default="")
    leader_sig = Column(Text, nullable=True, default="")

    transactions = relationship(
        "TransactionDB", back_populates="block", cascade="all, delete-orphan"
    )


class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=True, index=True)

    tx_id = Column(String(128), nullable=True, unique=True)
    payload = Column(Text, nullable=True)
    sender_pub = Column(String(256), nullable=True)
    signature = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    committed = Column(Boolean, default=False, nullable=False)

    block = relationship("BlockDB", back_populates="transactions")
