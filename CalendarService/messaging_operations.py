from aio_pika import connect_robust

from CalendarService.crud import create_reservation, there_is_overlapping_events
from CalendarService.database import SessionLocal
from CalendarService.messaging_converters import from_reservation_create
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_TO_CALENDAR_QUEUE, WRAPPER_TO_CALENDAR_ROUTING_KEY,
)
from ProjectUtils.MessagingService.schemas import from_json, MessageType
from sqlalchemy.orm import Session

# TODO: fix this in the future
channel.close()  # don't use the channel from this file, we need to use an async channel


async def consume(loop):
    connection = await connect_robust(host="rabbit_mq", loop=loop)
    channel = await connection.channel()

    wrappers_queue = await channel.declare_queue(WRAPPER_TO_CALENDAR_QUEUE, durable=True)

    await wrappers_queue.bind(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY)

    await wrappers_queue.consume(callback=consume_wrappers_message)

    return connection


async def consume_wrappers_message(incoming_message):
    async with incoming_message.process():
        message = from_json(incoming_message.body)
        print("\nconsume_wrappers_message", message.__dict__)
        with SessionLocal() as db:
            match message.message_type:
                case MessageType.RESERVATION_CREATE:
                    pass
                    # reservation = from_reservation_create(from_json(incoming_message.body))
                    # create_reservation(db, reservation=reservation)
                case MessageType.RESERVATION_UPDATE:
                    pass
                case MessageType.RESERVATION_DELETE:
                    pass
                case MessageType.RESERVATION_IMPORT:
                    body = message.body
                    import_reservations(db, body["service"], body["reservations"])


def import_reservations(db: Session, service_value: str, reservations):
    for reservation in reservations:
        reservation_schema = from_reservation_create(service_value, reservation)
        if there_is_overlapping_events(db, reservation_schema):
            print("overlapping event", reservation_schema.__dict__)
            continue
        create_reservation(db, reservation_schema)

