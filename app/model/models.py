"""
SQL Alchemy models declaration.
https://docs.sqlalchemy.org/en/14/orm/declarative_styles.html#example-two-dataclasses-with-declarative-table
Dataclass style for powerful autocompletion support.

https://alembic.sqlalchemy.org/en/latest/tutorial.html
Note, it is used by alembic migrations logic, see `alembic/env.py`

Alembic shortcuts:
# create migration
alembic revision --autogenerate -m "migration_name"

# apply all migrations
alembic upgrade head
"""

import datetime
import enum
import uuid
from typing import List, Optional

import pytz
from pydantic import EmailStr, condecimal
from sqlmodel import VARCHAR, Column, DateTime, Enum, Field, Relationship, SQLModel

from app.core.config import settings

timezone = pytz.timezone(settings.TIMEZONE)
KINESIS_PROXY_URL = (
    "https://4801rs7zrb.execute-api.us-east-2.amazonaws.com/dev/streams/invoices/record"
)


class Role(str, enum.Enum):
    admin = "Administrator"
    merchant = "Merchant"


class Status(str, enum.Enum):
    created = "Created"
    inactive = "Inactive"
    active = "Active"
    off = "Off"
    on = "On"


class User(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    username: EmailStr = Field(sa_column=Column("username", VARCHAR, unique=True))
    hashed_password: str
    nik: Optional[str] = Field(
        sa_column=Column("nik", VARCHAR, unique=True), max_length=16
    )
    first_name: Optional[str]
    last_name: Optional[str]
    address: Optional[str]
    role: Role = Field(sa_column=Column(Enum(Role)))
    created_at: datetime.datetime = Field(
        sa_column=Column("created_at", DateTime(timezone=True)), nullable=False
    )
    modified_at: datetime.datetime = Field(
        sa_column=Column("modified_at", DateTime(timezone=True)), nullable=False
    )
    devices: List["Device"] = Relationship(back_populates="owner")


class Device(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: Optional[str] = Field(
        sa_column=Column("name", VARCHAR, unique=True), primary_key=True
    )
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    serial_num: Optional[str]
    description: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    status: Status = Field(sa_column=Column(Enum(Status)))
    created_at: datetime.datetime = Field(
        sa_column=Column("created_at", DateTime(timezone=True)), nullable=False
    )
    modified_at: datetime.datetime = Field(
        sa_column=Column("modified_at", DateTime(timezone=True)), nullable=False
    )
    owner: Optional[User] = Relationship(back_populates="devices")


class Invoice(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    invoice_num: Optional[str]
    invoice_date: datetime.datetime = Field(
        sa_column=Column("invoice_date", DateTime(timezone=True)), nullable=False
    )
    device_name: Optional[str] = Field(default=None, foreign_key="device.name")
    username: Optional[EmailStr] = Field(default=None, foreign_key="user.username")
    tax_value: condecimal(max_digits=15, decimal_places=2) = Field(default=0)
    total_value: condecimal(max_digits=15, decimal_places=2) = Field(default=0)
    created_at: datetime.datetime = Field(
        sa_column=Column("created_at", DateTime(timezone=True)), nullable=False
    )
    modified_at: datetime.datetime = Field(
        sa_column=Column("modified_at", DateTime(timezone=True)), nullable=False
    )
