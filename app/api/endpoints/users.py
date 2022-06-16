import smtplib
import uuid
from datetime import datetime
from typing import List
from pydantic import EmailStr

import pytz
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.core.config import settings
from app.core.security import get_password_hash
from app.model.models import Device, User
from app.schemas.requests import (
    UserCreateRequest,
    UserUpdatePasswordRequest,
    UserUpdateProfileRequest,
)
from app.schemas.responses import BaseUserResponse, UserDeviceInResponse, UserResponse

router = APIRouter()
timezone = pytz.timezone(settings.TIMEZONE)
smtpuser = "emtres.co.id"
sender = "ridwan.fardani@gmail.com"
smtp_server = "mail.smtp2go.com"
port = 2525


def send_email(receiver:EmailStr, message:str):
    with smtplib.SMTP(smtp_server, port) as server:
        server.login(smtpuser, "skjdlkasjd")
        server.sendmail(sender, receiver, message)


@router.get("/me", response_model=UserDeviceInResponse)
async def read_current_user(
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """Get current user"""
    try:
        # print(current_user.create_at.__class__)
        result = await session.exec(
            select(User, Device).join(Device).where(User.id == current_user.id)
        )
        userdevice = result.one_or_none()
        devices = []
        for o in userdevice._data:
            if type(o) is Device:
                devices.append(o)
        response = UserDeviceInResponse(
            id=current_user.id,
            username=current_user.username,
            nik=current_user.nik,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            address=current_user.address,
            role=current_user.role,
            devices=devices,
        )
        return response
    except Exception:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Contact your admin"
        )


@router.post("/profile", response_model=UserResponse)
async def update_profile(
    user_request: UserUpdateProfileRequest,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """Update current user profile"""
    try:
        current_user.first_name = user_request.first_name
        current_user.last_name = user_request.last_name
        current_user.nik = user_request.nik
        current_user.address = user_request.address
        current_user.modified_at = datetime.now(timezone)
        session.add(current_user)
        await session.commit()
        await session.refresh(current_user)
        return current_user
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. rollback has occured"
        )


@router.get("/{id}", response_model=UserDeviceInResponse)
async def get_user_by_id(
    id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """Get user detail by id"""

    result = await session.exec(select(User).where(User.id == id))
    user = result.one_or_none()
    if user is None:
        raise HTTPException(status_code=400, detail=f"User with id {id} not found")
    try:
        result = await session.exec(
            select(User, Device).join(Device).where(User.id == id)
        )
        userdevice = result.fetchall()
        devices = []
        for o in userdevice:
            if type(o) is Device:
                devices.append(o)
        response = UserDeviceInResponse(
            id=user.id,
            username=user.username,
            nik=user.nik,
            first_name=user.first_name,
            last_name=user.last_name,
            address=user.address,
            role=user.role,
            devices=devices,
        )
        return response
    except Exception:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Contact your admin"
        )


@router.delete("/{id}")
async def delete_user_by_id(
    id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """
    Delete user by id
    Prerequisites:
    1. User does not have device assigned
    """
    # check whether user has devices assigned
    result = await session.exec(select(User).where(User.id == id))
    user = result.one_or_none()
    if user is None:
        raise HTTPException(status_code=400, detail=f"No user with {id}")
    if hasattr(user, "devices"):
        raise HTTPException(
            status_code=400, detail=f"User {id} has devices. can not be deleted. "
        )
    try:
        await session.exec(delete(User).where(User.id == id))
        await session.commit()
        return {"ok": True, "message": f"Delete {id} was successful"}
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. rollback has occured"
        )


@router.post("/reset-password", response_model=BaseUserResponse)
async def reset_current_user_password(
    user_update_password: UserUpdatePasswordRequest,
    session: AsyncSession = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """Update current user password"""
    try:
        current_user.hashed_password = get_password_hash(user_update_password.password)
        current_user.modified_at = datetime.now(timezone)
        session.add(current_user)
        await session.commit()
        return current_user
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. rollback has occured"
        )


@router.post("/register", response_model=BaseUserResponse)
async def register_new_user(
    new_user: UserCreateRequest,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
    backround_task: BackgroundTasks = None,
):
    """Create new user"""

    result = await session.exec(select(User).where(User.username == new_user.username))
    user = result.one_or_none()
    if user is not None:
        raise HTTPException(status_code=400, detail="Cannot use this email address")
    try:
        # password=generate_random_password()
        user = User(
            username=new_user.username,
            hashed_password=get_password_hash(new_user.password),
            role=new_user.role,
            created_at=datetime.now(timezone),
            modified_at=datetime.now(timezone),
        )
        session.add(user)
        await session.commit()
        # msg=f"""
        # From: ridwan.fardani@gmail.com
        # Subject: Tax Monitoring - User Password

        # Your password is {password}
        # """
        # backround_task.add_task(send_email,new_user.username,msg)
        return user
    except Exception:
        await session.commit()
        raise HTTPException(
            status_code=500, detail="Something went wrong. rollback has occured"
        )


@router.get("/", response_model=List[BaseUserResponse])
async def get_user_list(
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """Get user list"""
    result = await session.exec(select(User))
    users = result.all()
    return users
