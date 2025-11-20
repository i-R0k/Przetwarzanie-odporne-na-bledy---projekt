from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
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

    transactions = relationship(
        "TransactionDB", back_populates="block", cascade="all, delete-orphan"
    )


class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=True, index=True)

    sender = Column(String(128), nullable=False)
    recipient = Column(String(128), nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    committed = Column(Boolean, default=False, nullable=False)

    block = relationship("BlockDB", back_populates="transactions")
