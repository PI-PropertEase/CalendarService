from aio_pika import connect_robust

from CalendarService.crud import create_reservation
from CalendarService.database import SessionLocal
from CalendarService.messaging_converters import from_reservation_create
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_TO_APP_QUEUE, WRAPPER_BROADCAST_ROUTING_KEY,
)
from ProjectUtils.MessagingService.schemas import from_json, MessageType

# TODO: fix this in the future
channel.close()  # don't use the channel from this file, we need to use an async channel


async def consume(loop):
    connection = await connect_robust(host="localhost", loop=loop)
    channel = await connection.channel()

    wrappers_queue = await channel.declare_queue(WRAPPER_TO_APP_QUEUE, durable=True)

    await wrappers_queue.bind(exchange=EXCHANGE_NAME, routing_key=WRAPPER_BROADCAST_ROUTING_KEY)

    await wrappers_queue.consume(callback=consume_wrappers_message)

    return connection


async def consume_wrappers_message(incoming_message):
    async with incoming_message.process():
        message = from_json(incoming_message.body)
        with SessionLocal() as db:
            match message.message_type:
                case MessageType.RESERVATION_CREATE:
                    print("incoming message", incoming_message)
                    reservation = from_reservation_create(from_json(incoming_message.body))
                    print(reservation)
                    create_reservation(db, reservation=reservation)
                case MessageType.RESERVATION_UPDATE:
                    pass
                case MessageType.RESERVATION_DELETE:
                    pass
