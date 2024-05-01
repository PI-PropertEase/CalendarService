import pytest
import asyncio
import CalendarService.messaging_operations
from fixtures import test_db
from unittest.mock import call, AsyncMock
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from ProjectUtils.MessagingService.schemas import Service
from CalendarService.crud import create_reservation
from CalendarService.messaging_operations import import_reservations
from CalendarService.messaging_converters import from_reservation_create
from CalendarService import models
from ProjectUtils.MessagingService.queue_definitions import routing_key_by_service
import ProjectUtils.MessagingService.schemas

pytest_plugins = ('pytest_asyncio',)

# O que testar:
#   1. importar reservas normalmente - confirmed & cancelled
#   2. importar reserva cancelled que já existia e estava confirmed - deve enviar mensagem
#   3. importar reserva pending - deve passar a confirmed e mandar mensagem para os outros fazerem o mesmo
#   4. importar overlapping reservation

@pytest.mark.asyncio
async def test_import_reservations_new_reservations(test_db: Session, mocker: MockerFixture):
    reservations_import_body = [
        {
           "_id": 1,
            "reservation_status": "confirmed",
            "property_id": 1,
            "owner_email": "cool_guy@gmail.com",
            "begin_datetime": "2024-05-06 12:00:00",
            "end_datetime": "2024-05-08 12:00:00",
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351969999999",
            "cost": 350.50,
        },
        {
            "_id": 2,
            "reservation_status": "canceled",
            "property_id": 4,
            "owner_email": "cool_guy@gmail.com",
            "begin_datetime": "2024-05-06 12:00:00",
            "end_datetime": "2024-05-08 12:00:00",
            "client_email": "a@gmail.com",
            "client_name": "Test2",
            "client_phone": "+351969999999",
            "cost": 350.50,
        }
    ]



    exchange_mock = AsyncMock()
    mocker.patch.object(CalendarService.messaging_operations, "async_exchange", exchange_mock)
    create_reservations_spy = mocker.spy(CalendarService.messaging_operations, "create_reservation")
    there_are_overlapping_events_spy = mocker.spy(CalendarService.messaging_operations, "there_are_overlapping_events")

    # act
    await import_reservations(test_db, Service.ZOOKING.value, reservations_import_body)

    # assert
    assert create_reservations_spy.call_count == 2
    create_reservation_args_list = [
        call(test_db, from_reservation_create(Service.ZOOKING.value, reservations_import_body[0])),
        call(test_db, from_reservation_create(Service.ZOOKING.value, reservations_import_body[1])),
    ]
    assert create_reservations_spy.call_args_list == create_reservation_args_list
    there_are_overlapping_events_spy.assert_called_once_with(
        test_db, from_reservation_create(Service.ZOOKING.value, reservations_import_body[0])
    )
    assert test_db.query(models.Reservation).count() == 2
    assert exchange_mock.publish.call_count == 0


@pytest.mark.asyncio
async def test_import_reservations_new_pending_reservation(test_db: Session, mocker: MockerFixture):
    """
        When importing a new pending reservation, we will make its status "confirmed" and send that
        message back to the wrapper
    """
    reservations_import_body = [
        {
           "_id": 1,
            "reservation_status": "pending",
            "property_id": 1,
            "owner_email": "cool_guy@gmail.com",
            "begin_datetime": "2024-05-06 12:00:00",
            "end_datetime": "2024-05-08 12:00:00",
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351969999999",
            "cost": 350.50,
        },
    ]
    
    exchange_mock = AsyncMock()
    mocker.patch.object(CalendarService.messaging_operations, "async_exchange", exchange_mock)
    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    create_reservations_spy = mocker.spy(CalendarService.messaging_operations, "create_reservation")
    confirm_reservation_message_spy = mocker.spy(ProjectUtils.MessagingService.schemas.MessageFactory, "create_confirm_reservation_message")

    # act
    await import_reservations(test_db, Service.ZOOKING.value, reservations_import_body)

    created_reservation = from_reservation_create(Service.ZOOKING.value, reservations_import_body[0])
    created_reservation.reservation_status = "confirmed"
    create_reservations_spy.assert_called_once_with(
        test_db, created_reservation
    )
    # assert
    assert test_db.query(models.Reservation).count() == 1
    # reservation should be confirmed
    assert test_db.query(models.Reservation).first().reservation_status == models.ReservationStatus.CONFIRMED
    confirm_reservation_message_spy.assert_called_once_with(
        reservations_import_body[0]
    )
    assert exchange_mock.publish.call_count == 1


@pytest.mark.asyncio
async def test_import_reservations_existing_reservation_now_cancelled(test_db: Session, mocker: MockerFixture):
    """
        When a reservation is imported, and it already exists, but its status passes from
        'CONFIRMED' to 'CANCELED', we should update our existing reservation's status to
        canceled aswell.
    """
    existing_reservation = {
        "_id": 1,
        "reservation_status": "confirmed",
        "property_id": 1,
        "owner_email": "cool_guy@gmail.com",
        "begin_datetime": "2024-05-06 12:00:00",
        "end_datetime": "2024-05-08 12:00:00",
        "client_email": "cool_client@gmail.com",
        "client_name": "Test",
        "client_phone": "+351969999999",
        "cost": 350.50,
    }
    
    # create confirmed reservation
    existing_reservation_in_db = create_reservation(test_db, from_reservation_create(Service.ZOOKING.value, existing_reservation))
    
    # make it cancelled, and import it
    existing_reservation["reservation_status"] = "canceled"
    reservations_import_body = [
        existing_reservation
    ]

    exchange_mock = AsyncMock()
    mocker.patch.object(CalendarService.messaging_operations, "async_exchange", exchange_mock)
    create_reservations_spy = mocker.spy(CalendarService.messaging_operations, "create_reservation")
    update_reservation_status_spy = mocker.spy(CalendarService.messaging_operations, "update_reservation_status")

    # act
    await import_reservations(test_db, Service.ZOOKING.value, reservations_import_body)

    # assert
    update_reservation_status_spy.assert_called_once_with(
        test_db, existing_reservation_in_db, models.ReservationStatus.CANCELED
    )
    assert create_reservations_spy.call_count == 0
    assert test_db.query(models.Reservation).count() == 1
    assert exchange_mock.publish.call_count == 0


@pytest.mark.asyncio
async def test_import_reservation_overlapping_reservation(test_db: Session, mocker: MockerFixture):
    """
        When a reservation is imported, and it already exists, but its status passes from
        'CONFIRMED' to 'CANCELED', we should update our existing reservation's status to
        canceled aswell.
    """
    existing_reservation = {
        "_id": 1,
        "reservation_status": "confirmed",
        "property_id": 1,
        "owner_email": "cool_guy@gmail.com",
        "begin_datetime": "2024-05-06 12:00:00",
        "end_datetime": "2024-05-08 12:00:00",
        "client_email": "cool_client@gmail.com",
        "client_name": "Test",
        "client_phone": "+351969999999",
        "cost": 350.50,
    }
    
    # create confirmed reservation
    existing_reservation_in_db = create_reservation(test_db, from_reservation_create(Service.ZOOKING.value, existing_reservation))
    
    # new reservation but its overlappimg, to the right
    reservations_import_body = [
        {
            "_id": 2,
            "reservation_status": "confirmed",
            "property_id": 1,
            "owner_email": "cool_guy@gmail.com",
            "begin_datetime": "2024-05-07 12:00:00",
            "end_datetime": "2024-05-09 12:00:00",
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351969999999",
            "cost": 350.50,
        }
    ]

    exchange_mock = AsyncMock()
    mocker.patch.object(CalendarService.messaging_operations, "async_exchange", exchange_mock)
    create_reservations_spy = mocker.spy(CalendarService.messaging_operations, "create_reservation")
    pverlapping_reservation_message_spy = mocker.spy(ProjectUtils.MessagingService.schemas.MessageFactory, "create_overlap_import_reservation_message")


    # act
    await import_reservations(test_db, Service.ZOOKING.value, reservations_import_body)

    # assert
    pverlapping_reservation_message_spy.assert_called_once_with(
        reservations_import_body[0]
    )
    assert create_reservations_spy.call_count == 0
    assert test_db.query(models.Reservation).count() == 1
    assert exchange_mock.publish.call_count == 1