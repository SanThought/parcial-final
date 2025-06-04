# api/app.py
import os
import json
import secrets
import aio_pika
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")

security = HTTPBasic()
app = FastAPI(title="Message producer")


def verify(creds: HTTPBasicCredentials = Depends(security)):
    u_ok = secrets.compare_digest(
        creds.username, os.getenv("BASIC_AUTH_USERNAME", "admin")
    )
    p_ok = secrets.compare_digest(
        creds.password, os.getenv("BASIC_AUTH_PASSWORD", "secret")
    )
    if not (u_ok and p_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return creds.username


@app.post("/api/message", dependencies=[Depends(verify)])
async def publish(body: dict):
    # Publish to RabbitMQ queue "messages"
    conn = await aio_pika.connect_robust(RABBITMQ_URL)
    ch = await conn.channel()
    q = await ch.declare_queue("messages", durable=True)
    await ch.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=q.name,
    )
    return {"status": "queued"}


@app.get("/api/health")
def health():
    return {"status": "ok"}

