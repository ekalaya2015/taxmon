from datetime import datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api import deps
from app.core.config import settings
from app.model.models import Device, User
from app.schemas.requests import InvoiceBaseRequest
from app.schemas.responses import InvoiceBaseResponse

# import boto3
from app.worker import task_put_invoice

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
    result = await session.exec(select(Device).where(Device.user_id == current_user.id))
    devices = result.fetchall()
    if len(devices) == 0:
        raise HTTPException(status_code=400, detail="User has no device(s)")
    found = False
    for dev in devices:
        if dev.name == invoice_request.device_name:
            found = True
    if not found:
        raise HTTPException(
            status_code=400, detail=f"User has no device {invoice_request.device_name}"
        )
    try:
        invoice = InvoiceBaseResponse(
            invoice_num=invoice_request.invoice_num,
            invoice_date=invoice_request.invoice_date,
            device_name=invoice_request.device_name,
            username=current_user.username,
            tax_value=invoice_request.tax_value,
            total_value=invoice_request.total_value,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            created_at=datetime.now(timezone),
            modified_at=datetime.now(timezone),
        )
        session.add(invoice)
        await session.commit()
        await session.refresh(invoice)
        print(invoice.json())
        # # TODO: put record in kinesis stream
        task = task_put_invoice.delay(
            invoice_request.invoice_num,
            invoice_request.device_name,
            invoice_request.username,
            str((float(invoice_request.tax_value))),
            str(float(invoice_request.total_value)),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        return invoice

    except Exception as ex:
        print(str(ex))
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Something went wrong. Contact your admin"
        )
