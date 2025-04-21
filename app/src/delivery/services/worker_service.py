import asyncio
import json
import logging
from dataclasses import dataclass, field

import aio_pika
from dishka import AsyncContainer
from pydantic import ValidationError

from app.config import Settings
from app.di import get_container
from app.src.delivery.entities import (
    RegisterParcelDTO,
    RegisterParcelWithUserDTO,
)
from app.src.delivery.services.parcels_service import (
    ParcelService,
    ParcelServiceError,
)
from app.src.users.services import UserService, UserServiceError

logger = logging.getLogger(__name__)


class BackgroundWorkerError(Exception):
    pass


@dataclass
class BackgroundWorkerService:
    settings: Settings

    rabbitmq_url: str = field(init=False)
    channel: aio_pika.Channel | None = field(init=False)
    connection: aio_pika.Connection | None = field(init=False)
    container: AsyncContainer = field(init=False)

    def __post_init__(self):
        self.channel = None
        self.connection = None
        self.container = get_container()

    async def connect(self):
        if self.connection:
            return
        self.connection = await aio_pika.connect_robust(
            host=self.settings.rabbitmq_host,
            port=self.settings.rabbitmq_port,
            login=self.settings.rabbitmq_user,
            password=self.settings.rabbitmq_password,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        queue = await self.channel.declare_queue(
            self.settings.queue_name,
            durable=True,
        )

        await queue.consume(self.process_message)

        logger.info("Package worker connected and waiting for messages")

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                logger.debug(body)
            except (aio_pika.AMQPException, aio_pika.MessageProcessError) as e:
                logger.error(f"Error processing message: {e}")
                await message.reject(requeue=True)
                return

            await self.handle_parcel(body)

    async def handle_parcel(self, message_body) -> None:
        try:
            message: RegisterParcelWithUserDTO = (
                RegisterParcelWithUserDTO.model_validate(message_body)
            )
            user_service: UserService = await self.container.get(UserService)
            parcel_service: ParcelService = await self.container.get(
                ParcelService,
            )
            parcel = await parcel_service.create_parcel(
                user=await user_service.get_or_create(message.user_id),
                parcel_dto=RegisterParcelDTO.model_validate(
                    message,
                ),
            )
            logger.info("Worker handled parcel: %s", parcel)
        except (ValidationError, UserServiceError, ParcelServiceError) as ex:
            raise BackgroundWorkerError(ex) from ex

    async def run(self):
        await self.connect()
        try:
            await asyncio.Future()
        finally:
            await self.close()

    async def close(self):
        if not self.connection:
            return
        await self.connection.close()
        self.connection = None
        self.channel = None