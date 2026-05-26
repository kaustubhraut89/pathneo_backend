import aio_pika
import json
from app.core.config import settings

RABBITMQ_URL = "amqp://guest:guest@localhost/"

async def get_connection():
    return await aio_pika.connect_robust(RABBITMQ_URL)

async def publish_message(queue_name: str, message: dict):
    """Send a message to a queue."""
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )
        print(f"Message sent to queue: {queue_name}")