"""
schema.py — SQLAlchemy ORM models for the Signa threat database.

Single table:
  - threat_hashes : main lookup table (one row per known malware hash)
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, Float, Text, create_engine
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ThreatHash(Base):
    __tablename__ = "threat_hashes"

    sha256     = Column(String(64), primary_key=True)
    family     = Column(String(100), nullable=True)
    severity   = Column(String(20),  nullable=True)
    confidence = Column(Float,       nullable=True)
    source     = Column(String(100), nullable=True)
    first_seen = Column(DateTime,    nullable=True)
    last_seen  = Column(DateTime,    nullable=True)
    notes      = Column(Text,        nullable=True)
