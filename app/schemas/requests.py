import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, condecimal

from app.model.models import Role


class BaseRequest(BaseModel):
    # may define additional fields or config shared across requests
    pass


class RefreshTokenRequest(BaseRequest):
    refresh_token: str


class UserUpdatePasswordRequest(BaseRequest):
    password: str


class UserUpdateProfileRequest(BaseRequest):
    nik: str
    first_name: Optional[str]
    last_name: Optional[str]
    address: Optional[str]


class UserCreateRequest(BaseRequest):
    username: EmailStr
    password: str
    role: Role


class DeviceCreateRequest(BaseRequest):
    name: str


class DeviceAssignRequest(BaseRequest):
    lat: float
    lon: float


class InvoiceBaseRequest(BaseRequest):
    invoice_num: str
    invoice_date: datetime.datetime
    device_name: str
    tax_value: condecimal(max_digits=15, decimal_places=2)
    total_value: condecimal(max_digits=15, decimal_places=2)
