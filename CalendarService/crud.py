from sqlalchemy.orm import Session, with_polymorphic
from sqlalchemy import or_, and_

from CalendarService import models
from CalendarService.schemas import Reservation, BaseEvent, Cleaning

def get_events_by_owner_email(db: Session, owner_email: str):
    # include columns for all mapped subclasses
    model = with_polymorphic(models.BaseEvent, "*")
    return db.query(model).filter(models.BaseEvent.owner_email == owner_email).all()

def get_management_event_by_owner_email_and_event_id(db: Session, ManagementEventClass, owner_email: str, management_event_id: int):
    return db.query(ManagementEventClass).filter(and_(
        models.ManagementEvent.owner_email == owner_email, models.ManagementEvent.id == management_event_id
    )).first()


def delete_management_event(db: Session, management_event: models.ManagementEvent):
    db.delete(management_event)
    db.commit()


def create_cleaning(db: Session, cleaning_event: Cleaning):
    db_event = models.Cleaning(
        property_id=cleaning_event.property_id,
        owner_email=cleaning_event.owner_email,
        begin_datetime=cleaning_event.begin_datetime,
        end_datetime=cleaning_event.end_datetime,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_cleaning_by_id(db: Session, cleaning_id: int):
    return db.query(models.Cleaning).get(cleaning_id)

def create_maintenance(db: Session, maintenance_event: Cleaning):
    db_event = models.Maintenance(
        property_id=maintenance_event.property_id,
        owner_email=maintenance_event.owner_email,
        begin_datetime=maintenance_event.begin_datetime,
        end_datetime=maintenance_event.end_datetime,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_maintenance_by_id(db: Session, maintenance_id: int):
    return db.query(models.Maintenance).get(maintenance_id)





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


def update_reservation_status(db: Session, reservation: models.Reservation, reservation_status: models.ReservationStatus):
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

