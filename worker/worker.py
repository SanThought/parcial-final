import os
import json
import asyncio
import aio_pika
import pathlib
import sys

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://user:password@rabbitmq:5672/",   # same as in docker-compose.yml
)
RETRY_DELAY = float(os.getenv("RABBITMQ_RETRY_DELAY", 3))  # seconds

OUTPUT_DIR = pathlib.Path("/data")
OUTPUT_DIR.mkdir(exist_ok=True)


async def connect_until_ready() -> aio_pika.RobustConnection:
    """Keep trying to connect to RabbitMQ until it responds."""
    while True:
        try:
            return await aio_pika.connect_robust(RABBITMQ_URL)
        except (aio_pika.exceptions.AMQPConnectionError, OSError) as e:
            print(f"[worker] Broker not ready ({e}); retrying in {RETRY_DELAY}s…",
                  flush=True)
            await asyncio.sleep(RETRY_DELAY)


async def consume() -> None:
    conn = await connect_until_ready()
    channel = await conn.channel()
    queue = await channel.declare_queue("messages", durable=True)

    async with queue.iterator() as it:
        async for msg in it:
            async with msg.process():
                data = json.loads(msg.body.decode())
                out = OUTPUT_DIR / f"{msg.delivery_tag}.json"
                out.write_text(json.dumps(data, indent=2))
                print(f"[worker] Saved {out}", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(consume())
    except KeyboardInterrupt:
        sys.exit(0)

