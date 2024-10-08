from typing import Callable

from sqlalchemy.orm import Session, with_polymorphic
from sqlalchemy import or_, and_
from sqlalchemy import update
from CalendarService import models
from CalendarService.schemas import Reservation, BaseEvent, Cleaning, BaseEventWithId
from fastapi_mail import FastMail, MessageSchema, MessageType
from CalendarService import email_config
from fastapi import HTTPException


def get_all_events_by_owner_email_and_filter_reservations_by_status(
        db: Session, owner_email: str, reservation_status: models.ReservationStatus):
    # include columns for all mapped subclasses
    model = with_polymorphic(models.BaseEvent, "*")
    return db.query(model).filter(and_(
        models.BaseEvent.owner_email == owner_email,
        or_(
            models.BaseEvent.type != "reservation",
            models.Reservation.reservation_status == reservation_status
        ))).all()


def get_specific_events_by_owner_email(db: Session, owner_email: str, EventClass):
    return db.query(EventClass).filter(models.BaseEvent.owner_email == owner_email).all()


def get_specific_events_by_owner_email_and_property_id(db: Session, owner_email: str, property_id: int, EventClass):
    return db.query(EventClass).filter(and_(
        models.BaseEvent.owner_email == owner_email,
        models.BaseEvent.property_id == property_id
    )).all()


def get_confirmed_reservations_by_property_id(db: Session, property_id: int):
    return db.query(models.Reservation).filter(and_(
        models.Reservation.property_id == property_id,
        models.Reservation.reservation_status == models.ReservationStatus.CONFIRMED
    )).all()


def update_event(db: Session, event_to_update: models.BaseEvent, update_parameters: dict):
    for field_name, field_value in update_parameters.items():
        setattr(event_to_update, field_name, field_value)
    db.commit()
    db.refresh(event_to_update)
    return event_to_update


def get_management_event_by_owner_email_and_event_id(db: Session, ManagementEventClass, owner_email: str,
                                                     management_event_id: int):
    return db.query(ManagementEventClass).filter(and_(
        models.ManagementEvent.owner_email == owner_email, models.ManagementEvent.id == management_event_id
    )).first()


def get_management_event_by_id(db: Session, ManagementEventClass, management_event_id: int):
    return db.query(ManagementEventClass).get(management_event_id)


def create_management_event(db: Session, management_event, ManagementEventClass):
    db_event = ManagementEventClass(**management_event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_management_event(db: Session, management_event: models.ManagementEvent):
    db.delete(management_event)
    db.commit()
    return management_event


def create_reservation(db: Session, reservation: Reservation):
    print(reservation.__dict__)
    db_reservation = models.Reservation(
        external_id=reservation.external_id,
        property_id=reservation.property_id,
        owner_email=reservation.owner_email,
        begin_datetime=reservation.begin_datetime,
        end_datetime=reservation.end_datetime,
        client_email=reservation.client_email,
        client_name=reservation.client_name,
        client_phone=reservation.client_phone,
        cost=reservation.cost,
        reservation_status=models.ReservationStatus(reservation.reservation_status),
        service=models.Service(reservation.service.value),
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def get_reservation_by_internal_id(db: Session, reservation_internal_id: int):
    return db.query(models.Reservation).get(reservation_internal_id)


def get_reservation_by_external_id(db: Session, reservation_external_id: int):
    return db.query(models.Reservation).filter(models.Reservation.external_id == reservation_external_id).first()


def update_reservation_status(db: Session, reservation: models.Reservation,
                              reservation_status: models.ReservationStatus):
    db.query(models.Reservation).filter(models.Reservation.id == reservation.id).update(
        {models.Reservation.reservation_status: reservation_status}
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def there_are_overlapping_events(db: Session, new_event: BaseEvent):
    # reservations = [reservation for reservation in db.query(models.BaseEvent).all()]
    # print(reservations)
    # print("new_event", new_event)
    # for reservation in reservations:
    #     print("reservation", reservation.__dict__)
    #     print("reservation.owner_email == new_event.owner_email", reservation.owner_email == new_event.owner_email )
    #     print("reservation.property_id == new_event.property_id", reservation.property_id == new_event.property_id)
    #     print("new_event.begin_datetime > reservation.begin_datetime", new_event.begin_datetime > reservation.begin_datetime )
    #     print("new_event.end_datetime < reservation.end_datetime", new_event.end_datetime < reservation.end_datetime )
    #     print("new_event.begin_datetime < reservation.begin_datetime", new_event.begin_datetime < reservation.begin_datetime)
    #     print("new_event.end_datetime > reservation.begin_datetime", new_event.end_datetime > reservation.begin_datetime)
    #     print("new_event.begin_datetime < reservation.end_datetime", new_event.begin_datetime < reservation.end_datetime)
    #     print("new_event.end_datetime > reservation.end_datetime", new_event.end_datetime > reservation.end_datetime)
    #     print()
    return db.query(models.BaseEvent).filter(
        and_(
            models.BaseEvent.owner_email == new_event.owner_email,
            models.BaseEvent.property_id == new_event.property_id,
            or_(
                and_(
                    # fully inside
                    new_event.begin_datetime >= models.BaseEvent.begin_datetime,
                    new_event.end_datetime <= models.BaseEvent.end_datetime
                ),
                and_(
                    # inside to the left
                    new_event.begin_datetime < models.BaseEvent.begin_datetime,
                    new_event.end_datetime > models.BaseEvent.begin_datetime
                ),
                and_(
                    # inside to the right
                    new_event.begin_datetime < models.BaseEvent.end_datetime,
                    new_event.end_datetime > models.BaseEvent.end_datetime
                )
            )
        )).count() > 0


def there_are_overlapping_events_excluding_updating_event(db: Session, updating_event: BaseEventWithId):
    # reservations = [reservation for reservation in db.query(models.BaseEventWithId).all()]
    # print(reservations)
    # print("new_event", new_event)
    # for reservation in reservations:
    #     print("reservation", reservation.__dict__)
    #     print("reservation.owner_email == new_event.owner_email", reservation.owner_email == new_event.owner_email )
    #     print("reservation.property_id == new_event.property_id", reservation.property_id == new_event.property_id)
    #     print("new_event.begin_datetime > reservation.begin_datetime", new_event.begin_datetime > reservation.begin_datetime )
    #     print("new_event.end_datetime < reservation.end_datetime", new_event.end_datetime < reservation.end_datetime )
    #     print("new_event.begin_datetime < reservation.begin_datetime", new_event.begin_datetime < reservation.begin_datetime)
    #     print("new_event.end_datetime > reservation.begin_datetime", new_event.end_datetime > reservation.begin_datetime)
    #     print("new_event.begin_datetime < reservation.end_datetime", new_event.begin_datetime < reservation.end_datetime)
    #     print("new_event.end_datetime > reservation.end_datetime", new_event.end_datetime > reservation.end_datetime)
    #     print()
    return db.query(models.BaseEvent).filter(
        and_(
            models.BaseEvent.id != updating_event.id,
            models.BaseEvent.owner_email == updating_event.owner_email,
            models.BaseEvent.property_id == updating_event.property_id,
            or_(
                and_(
                    # fully inside
                    updating_event.begin_datetime >= models.BaseEvent.begin_datetime,
                    updating_event.end_datetime <= models.BaseEvent.end_datetime
                ),
                and_(
                    # inside to the left
                    updating_event.begin_datetime < models.BaseEvent.begin_datetime,
                    updating_event.end_datetime > models.BaseEvent.begin_datetime
                ),
                and_(
                    # inside to the right
                    updating_event.begin_datetime < models.BaseEvent.end_datetime,
                    updating_event.end_datetime > models.BaseEvent.end_datetime
                )
            )
        )).count() > 0


def add_to_email_property_id_mapping(db: Session, email: str, property_id: int):
    db_email_property_id_mapping = db.query(models.EmailPropertyIdMapping).get(email)
    if db_email_property_id_mapping is None:
        db_email_property_id_mapping = models.EmailPropertyIdMapping(email=email, properties_ids=[property_id])
        db.add(db_email_property_id_mapping)
    else:
        db_email_property_id_mapping.properties_ids.append(property_id)
    db.commit()


def get_property_ids_by_email(db: Session, email: str) -> list[int]:
    db_email_property_id_mapping = db.query(models.EmailPropertyIdMapping).get(email)
    return db_email_property_id_mapping.properties_ids if db_email_property_id_mapping is not None else []


async def send_email_to_reservation_client(db: Session, key: str, reservation: Reservation):
    print(f"Sending email to reservation {reservation.id}'s client: {reservation.client_email}")

    message = MessageSchema(
        subject=f"Key to open the door for your reservation from {reservation.begin_datetime} to {reservation.end_datetime}.",
        recipients=[reservation.client_email],
        body=email_config.template.substitute({
            "client_name": reservation.client_name,
            "key": key,
            "begin_time": reservation.begin_datetime,
            "end_time": reservation.end_datetime
        }),
        subtype=MessageType.html)

    fm = FastMail(email_config.conf)
    await fm.send_message(message)


