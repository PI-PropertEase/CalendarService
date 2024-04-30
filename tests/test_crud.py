import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from CalendarService import models
from datetime import datetime
from CalendarService import crud


@pytest.fixture
def test_db():
    print("Creating in-memory database...")
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    print("Cleaning up in-memory database...")
    models.Base.metadata.create_all(bind=engine)


def test_get_events_by_owner_email(test_db: Session):
    owner_email = "cool_guy@gmail.com"
    db_event1 = models.Cleaning(
        property_id=1,
        owner_email=owner_email,
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    db_event2 = models.Cleaning(
        property_id=2,
        owner_email="not_a_cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    db_event3 = models.Reservation(
        external_id=1,
        property_id=1,
        owner_email=owner_email,
        begin_datetime=datetime(2024, 5, 9, 12, 0, 0),
        end_datetime=datetime(2024, 5, 13, 12, 0, 0),
        client_email="anything@gmail.com",
        client_name="yeah",
        client_phone="+351969999999",
        cost=350.50,
        reservation_status=models.ReservationStatus.CONFIRMED,
        service=models.Service.ZOOKING,
    )
    db_event4 = models.Maintenance(
        property_id=1,
        owner_email=owner_email,
        begin_datetime=datetime(2024, 4, 25, 12, 0, 0),
        end_datetime=datetime(2024, 4, 28, 12, 0, 0),
    )
    test_db.add(db_event1)
    test_db.add(db_event2)
    test_db.add(db_event3)
    test_db.add(db_event4)
    test_db.commit()

    events_by_owner_email = crud.get_events_by_owner_email(test_db, owner_email)

    assert len(events_by_owner_email) == 3
    assert all([e.owner_email == owner_email for e in events_by_owner_email])



def test_get_management_event_by_owner_email_and_event_id(test_db: Session):
    owner_email = "cool_guy@gmail.com"
    db_event1 = models.Cleaning(
        property_id=1,
        owner_email=owner_email,
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    db_event2 = models.Maintenance(
        property_id=1,
        owner_email="not_a_cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    test_db.add(db_event1)
    test_db.add(db_event2)
    test_db.refresh(db_event1)
    test_db.refresh(db_event2)
    test_db.commit()

    cleaning_event = crud.get_management_event_by_owner_email_and_event_id(
        test_db, models.Cleaning, owner_email, db_event1.id
    )
    maintenance_event = crud.get_management_event_by_owner_email_and_event_id(
        test_db, models.Maintenance, owner_email, db_event2.id
    )

    assert cleaning_event is not None
    assert cleaning_event.owner_email == owner_email
    assert cleaning_event.id == db_event1.id
    assert maintenance_event is not None
    assert maintenance_event.owner_email == owner_email
    assert maintenance_event.id == db_event2.id


def test_delete_management_event(test_db: Session):
    owner_email = "cool_guy@gmail.com"
    db_event1 = models.Cleaning(
        property_id=1,
        owner_email=owner_email,
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    db_event2 = models.Maintenance(
        property_id=1,
        owner_email="not_a_cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    test_db.add(db_event1)
    test_db.add(db_event2)
    test_db.refresh(db_event1)
    test_db.refresh(db_event2)
    test_db.commit()

    crud.delete_management_event(test_db, db_event1)

    remaining_management_events = test_db.query(models.ManagementEvent).all()

    assert len(remaining_management_events) == 1
    assert remaining_management_events[0].id == db_event2.id


def test_create_cleaning(test_db: Session):
    db_event1 = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )

    created_cleaning = crud.create_cleaning(test_db, db_event1)

    assert created_cleaning is not None
    assert isinstance(created_cleaning, models.Cleaning)
    assert created_cleaning.owner_email == db_event1.owner_email
    assert created_cleaning.begin_datetime == db_event1.begin_datetime
    assert created_cleaning.end_datetime == db_event1.end_datetime
    assert created_cleaning.property_id == db_event1.property_id


def test_get_cleaning_by_id(test_db: Session):
    db_event1 = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    test_db.add(db_event1)
    test_db.refresh(db_event1)
    test_db.commit()

    cleaning_event = crud.get_cleaning_by_id(db_event1.id)

    assert cleaning_event is not None
    assert cleaning_event.id == db_event1.id
    assert isinstance(cleaning_event, models.Cleaning)


def test_create_maintenance(test_db: Session):
    db_event1 = models.Maintenance(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )

    created_maintenance = crud.create_maintenance(test_db, db_event1)

    assert created_maintenance is not None
    assert isinstance(created_maintenance, models.Maintenance)
    assert created_maintenance.owner_email == db_event1.owner_email
    assert created_maintenance.begin_datetime == db_event1.begin_datetime
    assert created_maintenance.end_datetime == db_event1.end_datetime
    assert created_maintenance.property_id == db_event1.property_id


def test_get_maintenance_by_id(test_db: Session):
    db_event1 = models.Maintenance(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    test_db.add(db_event1)
    test_db.refresh(db_event1)
    test_db.commit()

    maintenance_event = crud.get_maintenance_by_id(db_event1.id)

    assert maintenance_event is not None
    assert maintenance_event.id == db_event1.id
    assert isinstance(maintenance_event, models.Maintenance)


def test_create_reservation(test_db: Session):
    db_event1 = models.Reservation(
        external_id=1,
        property_id=1,
        owner_email="hello_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 9, 12, 0, 0),
        end_datetime=datetime(2024, 5, 13, 12, 0, 0),
        client_email="anything@gmail.com",
        client_name="yeah",
        client_phone="+351969999999",
        cost=350.50,
        reservation_status=models.ReservationStatus.CONFIRMED,
        service=models.Service.ZOOKING,
    )

    created_reservation = crud.create_reservation(test_db, db_event1)

    assert created_reservation is not None
    assert isinstance(created_reservation, models.Reservation)
    assert created_reservation.external_id == db_event1.external_id
    assert created_reservation.property_id == db_event1.property_id
    assert created_reservation.owner_email == db_event1.owner_email
    assert created_reservation.begin_datetime == db_event1.begin_datetime
    assert created_reservation.end_datetime == db_event1.end_datetime
    assert created_reservation.reservation_status == db_event1.reservation_status
    assert created_reservation.service == db_event1.service


def test_get_reservation_by_internal_id(test_db: Session):
    db_event1 = models.Reservation(
        external_id=1,
        property_id=1,
        owner_email="hello_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 9, 12, 0, 0),
        end_datetime=datetime(2024, 5, 13, 12, 0, 0),
        client_email="anything@gmail.com",
        client_name="yeah",
        client_phone="+351969999999",
        cost=350.50,
        reservation_status=models.ReservationStatus.CONFIRMED,
        service=models.Service.ZOOKING,
    )
    test_db.add(db_event1)
    test_db.refresh(db_event1)
    test_db.commit()

    reservation_event = crud.get_reservation_by_internal_id(test_db, db_event1.id)

    assert reservation_event is not None
    assert reservation_event == db_event1
    assert isinstance(reservation_event, models.Reservation)

def test_get_reservation_by_external_id(test_db: Session):
    db_event1 = models.Reservation(
        external_id=700,
        property_id=1,
        owner_email="hello_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 9, 12, 0, 0),
        end_datetime=datetime(2024, 5, 13, 12, 0, 0),
        client_email="anything@gmail.com",
        client_name="yeah",
        client_phone="+351969999999",
        cost=350.50,
        reservation_status=models.ReservationStatus.CONFIRMED,
        service=models.Service.ZOOKING,
    )
    test_db.add(db_event1)
    test_db.refresh(db_event1)
    test_db.commit()

    reservation_event = crud.get_reservation_by_external_id(test_db, db_event1.external_id)

    assert reservation_event is not None
    assert reservation_event == db_event1
    assert isinstance(reservation_event, models.Reservation)

def test_update_reservation_status(test_db: Session):
    db_event1 = models.Reservation(
        external_id=700,
        property_id=1,
        owner_email="hello_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 9, 12, 0, 0),
        end_datetime=datetime(2024, 5, 13, 12, 0, 0),
        client_email="anything@gmail.com",
        client_name="yeah",
        client_phone="+351969999999",
        cost=350.50,
        reservation_status=models.ReservationStatus.CONFIRMED,
        service=models.Service.ZOOKING,
    )
    test_db.add(db_event1)
    test_db.refresh(db_event1)
    test_db.commit()

    crud.update_reservation_status(test_db, db_event1, models.ReservationStatus.CANCELLED)

    updated_reservation = test_db.query(models.Reservation).get(db_event1.id)

    assert updated_reservation is not None
    assert updated_reservation.reservation_status == models.ReservationStatus.CANCELLED



def test_there_are_overlapping_events(test_db: Session):
    db_event1 = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )
    db_event2 = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 9, 12, 0, 0),
        end_datetime=datetime(2024, 5, 11, 12, 0, 0),
    )
    db_event3 = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 11, 12, 0, 0),
        end_datetime=datetime(2024, 5, 15, 12, 0, 0),
    )
    test_db.add(db_event1)
    test_db.add(db_event2)
    test_db.add(db_event3)
    test_db.commit()

    # occupied intervals: 06/05-08/05, 09/05-15/05

    # same exact interval as the first interval - 06/05-08/05
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 6, 12, 0, 0),
        end_datetime=datetime(2024, 5, 8, 12, 0, 0),
    )

    assert crud.there_are_overlapping_events(test_db, new_event)

    # overlap from the left of the 1st interval
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 5, 12, 0, 0),
        end_datetime=datetime(2024, 5, 7, 12, 0, 0),
    )

    assert crud.there_are_overlapping_events(test_db, new_event)

    # overlap from the right of the 1st interval
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 14, 12, 0, 0),
        end_datetime=datetime(2024, 5, 16, 12, 0, 0),
    )

    assert crud.there_are_overlapping_events(test_db, new_event)

    # overlaps with both intervals, and is in the middle of them
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 7, 12, 0, 0),
        end_datetime=datetime(2024, 5, 10, 12, 0, 0),
    )

    assert crud.there_are_overlapping_events(test_db, new_event)

    # fits both interval inside of itself
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 5, 12, 0, 0),
        end_datetime=datetime(2024, 5, 16, 12, 0, 0),
    )

    assert crud.there_are_overlapping_events(test_db, new_event) 


    # fits both interval inside of itself
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 5, 12, 0, 0),
        end_datetime=datetime(2024, 5, 16, 12, 0, 0),
    )

    assert crud.there_are_overlapping_events(test_db, new_event)

    # doesn't overlap to the left
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 3, 12, 0, 0),
        end_datetime=datetime(2024, 5, 5, 12, 0, 0),
    )

    assert not crud.there_are_overlapping_events(test_db, new_event) 

    # doesn't overlap to the right by 1 second
    new_event = models.Cleaning(
        property_id=1,
        owner_email="cool_guy@gmail.com",
        begin_datetime=datetime(2024, 5, 15, 12, 0, 1),
        end_datetime=datetime(2024, 5, 16, 12, 0, 0),
    )

    assert not crud.there_are_overlapping_events(test_db, new_event)
