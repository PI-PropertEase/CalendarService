from aio_pika import connect_robust, ExchangeType

from CalendarService.crud import create_reservation, there_are_overlapping_events, get_reservation_by_external_id, \
    update_reservation_status
from CalendarService.database import SessionLocal
from CalendarService.messaging_converters import from_reservation_create
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_TO_CALENDAR_QUEUE, WRAPPER_TO_CALENDAR_ROUTING_KEY, routing_key_by_service, WRAPPER_BROADCAST_ROUTING_KEY
)
from ProjectUtils.MessagingService.schemas import from_json, MessageType, MessageFactory, to_json_aoi_bytes
from sqlalchemy.orm import Session

from CalendarService import models

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
                case MessageType.RESERVATION_IMPORT:
                    body = message.body
                    await import_reservations(db, body["service"], body["reservations"])


async def import_reservations(db: Session, service_value: str, reservations):
    # reservations -> apenas reservas novas ou canceladas
    for reservation in reservations:
        reservation_schema = from_reservation_create(service_value, reservation)
        if reservation_schema.reservation_status == "canceled":
            # canceled -> either cancelling existing reservation or importing canceled reservation
            reservation_with_same_id = get_reservation_by_external_id(db, reservation_schema.external_id)
            if reservation_with_same_id is not None:
                # if the reservation already exists
                # there is the chance that is already propagated to other services
                print("before_update", reservation_with_same_id.__dict__)
                print("after_cancelled",
                      update_reservation_status(db, reservation_with_same_id, models.ReservationStatus.CANCELED))
                await async_exchange.publish(
                    routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
                    message=to_json_aoi_bytes(MessageFactory.create_cancel_reservation_message(reservation))
                )
            else:
                reservation_schema.reservation_status = "canceled"
                create_reservation(db, reservation_schema)
        else:
            # confirmed -> already confirmed on external service and are now just importing it
            # pending   -> external service awaiting CalendarService confirmation
            if there_are_overlapping_events(db, reservation_schema):
                print("overlapping event", reservation_schema.__dict__)
                await async_exchange.publish(
                    routing_key=routing_key_by_service[service_value],
                    message=to_json_aoi_bytes(MessageFactory.create_overlap_import_reservation_message(reservation))
                )
                reservation_schema.reservation_status = "canceled"
                create_reservation(db, reservation_schema)
            else:
                if reservation_schema.reservation_status == "pending":
                    reservation_schema.reservation_status = "confirmed"
                    await async_exchange.publish(
                        routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
                        message=to_json_aoi_bytes(MessageFactory.create_confirm_reservation_message(reservation))
                    )
                create_reservation(db, reservation_schema)


async def propagate_event_creation_to_wrappers(db_event):
    await async_exchange.publish(
        routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
        message=to_json_aoi_bytes(
            MessageFactory.create_management_event_creation_update_message(
                MessageType.MANAGEMENT_EVENT_CREATE,
                db_event.property_id, db_event.id, db_event.begin_datetime, db_event.end_datetime
            )
        )
    )


async def propagate_event_update_to_wrappers(db_event):
    await async_exchange.publish(
        routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
        message=to_json_aoi_bytes(
            MessageFactory.create_management_event_creation_update_message(
                MessageType.MANAGEMENT_EVENT_UPDATE,
                db_event.property_id, db_event.id, db_event.begin_datetime, db_event.end_datetime
            )
        )
    )


async def propagate_event_deletion_to_wrappers(db_event):
    await async_exchange.publish(
        routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
        message=to_json_aoi_bytes(
            MessageFactory.create_management_event_deletion_message(db_event.property_id, db_event.id)
        )
    )
