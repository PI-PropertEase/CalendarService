from sqlalchemy.orm import Session, with_polymorphic
from sqlalchemy import or_, and_

from CalendarService import models
from CalendarService.schemas import Reservation, Event


def create_reservation(db: Session, reservation: Reservation):
    print(reservation.__dict__)
    db_reservation = models.Reservation(
        id=reservation.id,
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


def get_reservation_by_id(db: Session, reservation_id: int):
    return db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()


def update_reservation_status(db: Session, reservation: models.Reservation, reservation_status: models.ReservationStatus):
    db.query(models.Reservation).filter(models.Reservation.id == reservation.id).update(
        {models.Reservation.reservation_status: reservation_status}
    )
    db.commit()
    db.refresh(reservation)
    return reservation


def there_is_overlapping_events(db: Session, new_event: Event):
    # reservations = [reservation for reservation in db.query(models.Event).all()]
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
    return db.query(models.Event).filter(
        and_(
            models.Event.owner_email == new_event.owner_email,
            models.Event.property_id == new_event.property_id,
            or_(
                and_(
                    # fully inside
                    new_event.begin_datetime >= models.Event.begin_datetime,
                    new_event.end_datetime <= models.Event.end_datetime
                ),
                and_(
                    # inside to the left
                    new_event.begin_datetime < models.Event.begin_datetime,
                    new_event.end_datetime > models.Event.begin_datetime
                ),
                and_(
                    # inside to the right
                    new_event.begin_datetime < models.Event.end_datetime,
                    new_event.end_datetime > models.Event.end_datetime
                )
            )
        )).count() > 0


def get_events_by_owner_email(db: Session, owner_email: str):
    # include columns for all mapped subclasses
    model = with_polymorphic(models.Event, [models.Reservation])
    return db.query(model).filter(models.Event.owner_email == owner_email).all()