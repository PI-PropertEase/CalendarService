from aio_pika import connect_robust, ExchangeType

from CalendarService.crud import create_reservation, there_is_overlapping_events
from CalendarService.database import SessionLocal
from CalendarService.messaging_converters import from_reservation_create
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_TO_CALENDAR_QUEUE, WRAPPER_TO_CALENDAR_ROUTING_KEY, routing_key_by_service
)
from ProjectUtils.MessagingService.schemas import from_json, MessageType, MessageFactory, to_json_aoi_bytes
from sqlalchemy.orm import Session

# TODO: fix this in the future
channel.close()  # don't use the channel from this file, we need to use an async channel


async def consume(loop):
    global async_exchange

    connection = await connect_robust(host="rabbit_mq", loop=loop)
    async_channel = await connection.channel()

    wrappers_queue = await async_channel.declare_queue(WRAPPER_TO_CALENDAR_QUEUE, durable=True)

    async_exchange = await async_channel.declare_exchange(
        name=EXCHANGE_NAME, type=ExchangeType.TOPIC, durable=True
    )

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
                    await import_reservations(db, body["service"], body["reservations"])


async def import_reservations(db: Session, service_value: str, reservations):
    for reservation in reservations:
        reservation_schema = from_reservation_create(service_value, reservation)
        if there_is_overlapping_events(db, reservation_schema):
            print("overlapping event", reservation_schema.__dict__)
            await async_exchange.publish(
                routing_key=routing_key_by_service[service_value],
                message=to_json_aoi_bytes(MessageFactory.create_overlap_import_reservation_message(reservation))
            )
        else:
            if reservation_schema.reservation_status in ["confirmed", "pending"]:
                # confirmed -> already confirmed on external service and are now just importing it
                # pending   -> external service awaiting CalendarService confirmation
                if reservation_schema.reservation_status == "pending":
                    reservation_schema.reservation_status = "confirmed"
                    # TODO post confirm reservation message
                create_reservation(db, reservation_schema)
            else:
                # canceled -> TODO don't know yet
                pass


