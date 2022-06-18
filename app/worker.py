# Celery worker
# Task: deliver invoice data to aws kinesis
import json

import boto3
from celery import Celery

app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost")


@app.task(name="invoice")
def task_put_invoice(
    invoice_num, device_name, username, tax_value, total_value, created_at
):
    data = {
        "invoice_num": invoice_num,
        "device_name": device_name,
        "username": username,
        "tax_value": tax_value,
        "total_value": total_value,
        "created_at": created_at,
    }
    client = boto3.client("kinesis", region_name="us-east-2")
    client.put_record(
        StreamName="invoices", Data=json.dumps(data), PartitionKey="partitionkey"
    )
    return {"Ok": True, "message": "invoice data has been delivered to pipeline"}
