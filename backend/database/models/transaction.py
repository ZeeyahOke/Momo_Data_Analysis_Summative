from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class TransactionType(Base):
    """Model for transaction types"""
    __tablename__ = 'transaction_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    # Relationship with transactions
    transactions = relationship("Transaction", back_populates="type")

    def __repr__(self):
        return f"<TransactionType(name='{self.name}')>"

class Transaction(Base):
    """Model for transactions"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(50), unique=True, nullable=True)
    type_id = Column(Integer, ForeignKey('transaction_types.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    balance = Column(Float, nullable=True)
    sender = Column(String(100), nullable=True)
    receiver = Column(String(100), nullable=True)
    raw_body = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)

    # Relationship with transaction type
    type = relationship("TransactionType", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.type.name}', amount={self.amount})>" 