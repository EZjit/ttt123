from dataclasses import dataclass

import aio_pika

from app.config import Settings


@dataclass
class PublisherService:
    settings: Settings

    @property
    async def connection(self):
        self._connection = getattr(
            self,
            "_connection",
            None,
        ) or await aio_pika.connect_robust(
            host=self.settings.rabbitmq_host,
            port=self.settings.rabbitmq_port,
            login=self.settings.rabbitmq_user,
            password=self.settings.rabbitmq_password,
        )
        return self._connection

    async def publish_message(self, message: str):
        connection = await self.connection
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(
                self.settings.queue_name,
                durable=True,
            )
            await channel.default_exchange.publish(
                aio_pika.Message(body=message.encode()),
                routing_key=queue.name,
            )

    async def close(self):
        if not self._connection:
            return
        await self._connection.close()
        self._connection = None
        self._channel = None