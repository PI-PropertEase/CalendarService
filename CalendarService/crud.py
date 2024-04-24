from sqlalchemy.orm import Session, with_polymorphic
from sqlalchemy import or_

from CalendarService import models
from CalendarService.schemas import Reservation, Event


def create_reservation(db: Session, reservation: Reservation):
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
        service=models.Service(reservation.service.value)
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def there_is_overlapping_events(db: Session, new_event: Event):
    print(db.query(models.Reservation).filter(new_event.begin_datetime < models.Reservation.end_datetime).count())
    return db.query(models.Event).filter(or_(
        models.Event.begin_datetime <= new_event.begin_datetime < models.Event.end_datetime,
        models.Event.begin_datetime < new_event.end_datetime <= models.Event.end_datetime,
    )).count() > 0

def get_events_by_owner_email(db: Session, owner_email: str):
    # include columns for all mapped subclasses
    model = with_polymorphic(models.Event, [models.Reservation])
    return db.query(model).filter(models.Event.owner_email == owner_email).all()