import datetime
import uuid
from typing import List, Optional

from pydantic import BaseModel, EmailStr, condecimal

from app.model.models import Role, Status


class BaseResponse(BaseModel):
    # may define additional fields or config shared across responses
    # class Config:
    #     orm_mode = True
    pass


class AccessTokenResponse(BaseResponse):
    token_type: str
    access_token: str
    expires_at: int
    issued_at: int
    refresh_token: str
    refresh_token_expires_at: int
    refresh_token_issued_at: int


class UserResponse(BaseResponse):
    id: uuid.UUID
    username: EmailStr
    nik: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    address: Optional[str]
    role: Role


class BaseUserResponse(BaseResponse):
    id: uuid.UUID
    username: EmailStr
    role: Role


class UserDeviceResponse(BaseResponse):
    user_id: Optional[uuid.UUID]
    username: Optional[str]


class DeviceCreatedResponse(BaseResponse):
    id: uuid.UUID
    name: str
    lat: Optional[float]
    lon: Optional[float]
    status: Status
    # user_id:Optional[uuid.UUID]


class DeviceResponse(BaseResponse):
    id: uuid.UUID
    name: str
    status: Optional[Status]
    serial_num: str
    description: str
    owner: Optional[UserDeviceResponse] = None


class DeviceAssignResponse(BaseResponse):
    id: uuid.UUID
    name: str
    user_id: Optional[uuid.UUID]
    status: Status


class UserDeviceReadResponse(UserResponse):
    role: Role
    devices: List[DeviceCreatedResponse] = []


class UserDeviceInResponse(UserResponse):
    devices: List[DeviceCreatedResponse] = []


class InvoiceBaseResponse(BaseResponse):
    id: uuid.UUID
    device_name: str
    username: str
    invoice_num: str
    invoice_date: datetime.datetime
    tax_value: condecimal(max_digits=15, decimal_places=2)
    total_value: condecimal(max_digits=15, decimal_places=2)
