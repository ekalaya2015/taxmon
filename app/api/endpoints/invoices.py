import json
from datetime import datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.core.config import settings
from app.model.models import Device, Invoice, User
from app.schemas.requests import InvoiceBaseRequest
from app.schemas.responses import InvoiceBaseResponse

timezone = pytz.timezone(settings.TIMEZONE)
router = APIRouter()


@router.post("/", response_model=InvoiceBaseResponse)
async def submit_invoice(
    invoice_request: InvoiceBaseRequest,
    current_user: User = Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_session),
):
    """
    Submit invoice data.

    Requirements for submitting invoice data through API are:
    1. Device has been registered/added (as Administrator)
    2. Device has been assigned to a user (as Administrator)
    3. Login to get token then use the access token as Bearer token
    """
    result = await session.exec(
        select(User, Device).join(Device).where(User.id == current_user.id)
    )
    userdevice = result.one_or_none()
    found: bool = False
    if userdevice is None:
        raise HTTPException(
            status_code=400,
            detail=f"User does not have device {invoice_request.device_name}",
        )
    for o in userdevice._data:
        if type(o) is Device:
            if o.name == invoice_request.device_name:
                found = True
                break
    if not found:
        raise HTTPException(
            status_code=400,
            detail=f"this user does not have {invoice_request.device_name}",
        )
    try:
        invoice = Invoice(
            invoice_num=invoice_request.invoice_num,
            invoice_date=invoice_request.invoice_date,
            device_name=invoice_request.device_name,
            user_id=current_user.id,
            tax_value=invoice_request.tax_value,
            total_value=invoice_request.total_value,
            create_at=datetime.now(timezone),
            modified_at=datetime.now(timezone),
        )
        session.add(invoice)
        await session.commit()
        await session.refresh(invoice)
        return invoice
    except Exception as ex:
        print(str(ex))
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. Contact your admin"
        )
