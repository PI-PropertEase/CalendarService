from sqlalchemy.orm import Session

from CalendarService import models
from CalendarService.schemas import Reservation


def create_reservation(db: Session, reservation: Reservation):
    db_reservation = models.Reservation(
        id=reservation.id,
        property_id=reservation.property_id,
        status=reservation.status,
        begin_datetime=reservation.begin_datetime,
        end_datetime=reservation.end_datetime,
        client_name=reservation.client_name,
        client_phone=reservation.client_phone,
        cost=reservation.cost,
        service=reservation.service
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation
