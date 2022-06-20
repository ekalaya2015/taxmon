# Celery worker
# Task: deliver invoice data to aws kinesis
import json

import boto3
from celery import Celery

app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost")


@app.task(name="invoice")
def task_put_invoice(**args):
    data = {
        "invoice_num": args["invoice_num"],
        "device_name": args["device_name"],
        "username": args["username"],
        "tax_value": args["tax_value"],
        "total_value": args["total_value"],
        "invoice_date": args["invoice_date"],
    }
    client = boto3.client("kinesis", region_name="us-east-2")
    client.put_record(
        StreamName="invoices", Data=json.dumps(data), PartitionKey="partitionkey"
    )
    return {
        "Ok": True,
        "data": data,
        "message": "invoice data has been delivered to pipeline",
    }
