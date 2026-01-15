from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy import JSON as SAJSON

# NOTE:
# Use SQLAlchemy's JSON column type via sa_column=Column(SAJSON)
# so SQLModel can map Python dicts to a JSON column in SQLite.

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    scans: List["Scan"] = Relationship(back_populates="user")


class Scan(SQLModel, table=True):
    """
    Represents one saved scan (a snapshot). Each Scan belongs to a user
    and contains multiple ScanItem rows (JSON kept for convenience).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: Optional[str] = Field(default="Scan")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Use a JSON column for raw JSON data
    raw_json: Optional[dict] = Field(default=None, sa_column=Column(SAJSON()))
    # A human-friendly summary (e.g., count, best network)
    summary: Optional[str] = Field(default=None)

    user: Optional[User] = Relationship(back_populates="scans")
    items: List["ScanItem"] = Relationship(back_populates="scan")


class ScanItem(SQLModel, table=True):
    """
    Optional detailed row-per-network if you want normalized storage.
    We keep raw_json on Scan so ScanItem is optional and simple.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: int = Field(foreign_key="scan.id", index=True)
    bssid: Optional[str] = Field(default=None, index=True)
    ssid: Optional[str] = Field(default=None)
    rssi: Optional[int] = Field(default=None)
    extra: Optional[dict] = Field(default=None, sa_column=Column(SAJSON()))

    scan: Optional[Scan] = Relationship(back_populates="items")
