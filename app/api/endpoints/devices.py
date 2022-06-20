import uuid
from datetime import datetime
from typing import List, Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.core.config import settings
from app.model.models import Device, Invoice, Status, User
from app.schemas.requests import DeviceAssignRequest, DeviceCreateRequest
from app.schemas.responses import (
    DeviceAssignResponse,
    DeviceCreatedResponse,
    DeviceResponse,
)

timezone = pytz.timezone(settings.TIMEZONE)
router = APIRouter()


@router.get("/", response_model=List[DeviceResponse])
async def get_device_list(
    status: Status = None,
    session: AsyncSession = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user),
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
):
    """Get device list of current user"""
    if status:
        result = await session.exec(
            select(
                Device.id,
                Device.name,
                Device.serial_num,
                Device.status,
                Device.description,
                Device.lat,
                Device.lon,
                Device.user_id,
                User.username,
            )
            .join(User, isouter=True)
            .where(Device.status == status)
        )
    else:
        result = await session.exec(
            select(
                Device.id,
                Device.name,
                Device.serial_num,
                Device.status,
                Device.description,
                Device.lat,
                Device.lon,
                Device.user_id,
                User.username,
            ).join(User, isouter=True)
        )
    devices = result.fetchall()
    response = []
    for dev in devices:
        response.append(
            {
                "id": dev.id,
                "name": dev.name,
                "serial_num": dev.serial_num,
                "status": dev.status,
                "lat": dev.lat,
                "lon": dev.lon,
                "description": dev.description,
                "owner": {"user_id": dev.user_id, "username": dev.username},
            }
        )
    return response  # devices


@router.post("/", response_model=DeviceCreatedResponse)
async def add_device(
    new_device: DeviceCreateRequest,
    session: AsyncSession = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Add device

    When create/add device, status will be set to Inactive
    """
    result = await session.exec(select(Device).where(Device.name == new_device.name))
    if result.first():
        raise HTTPException(
            status_code=400,
            detail="Device with {} already exist".format(new_device.name),
        )
    try:
        device = Device(
            name=new_device.name,
            serial_num=new_device.serial_num,
            description=new_device.description,
            created_at=datetime.now(timezone),
            modified_at=datetime.now(timezone),
            status=Status.created,
        )
        session.add(device)
        await session.commit()
        return device
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. Rollback has occured"
        )


@router.post("/{device_id}/assign/{user_id}", response_model=DeviceAssignResponse)
async def assign_device_to_user(
    req: DeviceAssignRequest,
    device_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """
    Assign device to specific user

    Prerequisite:
    1. Device has not been assigned to a user yet
    2. Device does not have invoices

    When device has been assigned to a user, device status would be set to Active
    * Attribute 'lat' is latitude coordinate (mandatory)
    * Attribute 'lon' is longitude coordinate (mandatory)
    """
    result = await session.exec(select(Device).where(Device.id == device_id))
    device = result.one_or_none()
    if device is None:
        raise HTTPException(
            status_code=400, detail="Device id {} not found".format(device_id)
        )
    if device.status == Status.active:
        raise HTTPException(
            status_code=400,
            detail="Device id {} has been assigned to a user".format(device_id),
        )
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.one_or_none()
    if user is None:
        raise HTTPException(
            status_code=400, detail="User id {} not found".format(user_id)
        )
    try:
        device.user_id = user.id
        device.lat = req.lat
        device.lon = req.lon
        device.serial_num = req.serial_num
        device.description = req.description
        device.status = Status.active
        device.modified_at = datetime.now(timezone)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. Rollback has occured"
        )


@router.post("/{device_id}/unassign/{user_id}", response_model=DeviceAssignResponse)
async def unassign_device_from_user(
    device_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """
    Unassign device from user

    When device is unassigned from a user, status will be set to Inactive

    """

    result = await session.exec(select(Device).where(Device.id == device_id))
    device = result.one_or_none()
    if device is None:
        raise HTTPException(
            status_code=400, detail="Device id {} not found".format(device_id)
        )
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.one_or_none()
    if user is None:
        raise HTTPException(
            status_code=400, detail="User id {} not found".format(user_id)
        )
    try:
        device.user_id = None
        device.modified_at = datetime.now(timezone)
        device.status = Status.inactive
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. Rollback has occured"
        )


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_devices_profile(
    device_id: uuid.UUID,
    device_data: DeviceAssignRequest,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """
    Update device profile
    Prerequistes:
    1. Update can be applied to device with any statuses except Inactive
    """
    result = await session.exec(select(Device).where(Device.id == device_id))
    device = result.one_or_none()
    if device is None:
        raise HTTPException(status_code=400, detail=f"Device {device_id} not found")
    if device.status == Status.inactive:
        raise HTTPException(status_code=400, detail=f"Device {device_id} is inactive")
    try:
        for k, v in device_data.dict().items():
            setattr(device, k, v)
        setattr(device, "modified_at", datetime.now(timezone))
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device
    except Exception as ex:
        print(str(ex))
        raise HTTPException(
            status_code=500, detail="Something went wrong. Contact your admin"
        )


@router.delete("/{id}")
async def delete_device(
    id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """
    Delete device

    Prerequisite:
    1. Device with status 'Created'
    2. Device does not have any user assigned
    3. Device does not have any invoices
    """
    result = await session.exec(select(Device).where(Device.id == id))
    device = result.one_or_none()
    if device is None:
        raise HTTPException(status_code=400, detail=f"Device {id} not found")
    if device.status == Status.active:
        raise HTTPException(
            status_code=400,
            detail=f"Device {id} has been assigned to a user. Unassigned it first",
        )
    if device.status == Status.inactive:
        # check whether device has invoices
        result = await session.exec(
            select(Invoice, Device)
            .join(Device)
            .where(Device.id == id)
            .where(Device.status == Status.inactive)
        )
        devices = result.fetchmany(1)
        if len(devices) != 0:
            raise HTTPException(status_code=400, detail="Device has invoices")

    try:
        await session.exec(delete(Device).where(Device.id == id))
        await session.commit()
        return {"Ok": True, "message": f"Device {id} has been deleted"}
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. Contact you admin"
        )
