import json
import uuid
from datetime import datetime
from typing import List

import pytz
from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/me", response_model=UserDeviceInResponse)
async def read_current_user(
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """Get current user"""
    try:
        result = await session.exec(
            select(Device).where(Device.user_id == current_user.id)
        )
        devices = result.fetchall()
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
    except Exception as ex:
        print(str(ex))
        raise HTTPException(
            status_code=500, detail="Something went wrong. Contact your admin"
        )


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    user_request: UserUpdateProfileRequest,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """Update current user profile"""
    try:
        for k, v in user_request.dict().items():
            setattr(current_user, k, v)
        setattr(current_user, "modified_at", datetime.now(timezone))
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
        result = await session.exec(select(Device).where(Device.user_id == id))
        devices = result.fetchall()
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
    except Exception as ex:
        print(str(ex))
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
):
    """Create new user"""

    result = await session.exec(select(User).where(User.username == new_user.username))
    user = result.one_or_none()
    if user is not None:
        raise HTTPException(status_code=400, detail="Cannot use this email address")
    try:
        user = User(
            username=new_user.username,
            hashed_password=get_password_hash(new_user.password),
            role=new_user.role,
            created_at=datetime.now(timezone),
            modified_at=datetime.now(timezone),
        )
        session.add(user)
        await session.commit()
        return user
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=json.dumps(str(e)))


@router.get("/", response_model=List[BaseUserResponse])
async def get_user_list(
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """Get user list"""
    result = await session.exec(select(User))
    users = result.all()
    return users
