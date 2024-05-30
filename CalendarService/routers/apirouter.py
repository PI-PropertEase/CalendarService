from fastapi import APIRouter, Depends, status, HTTPException, Request

from CalendarService.dependencies import get_user, get_db, get_user_email, get_update_management_event_schema, \
    get_management_event_model, \
    InitializeUpdateEventAccordingToEndpoint, get_event_model
from CalendarService import crud
from CalendarService.messaging_operations import propagate_event_creation_to_wrappers, \
    propagate_event_update_to_wrappers, propagate_event_deletion_to_wrappers
from CalendarService.schemas import Cleaning, Maintenance, UniformEventWithId, UserBase, UpdateCleaning, \
    BaseEvent, CleaningWithId, MaintenanceWithId, BaseEventWithId, UpdateMaintenance, ReservationWithId, KeyInput
from sqlalchemy.orm import Session
from CalendarService import models
from CalendarService.dependencies import InitializeEventWithOwnerEmail
from pydantic import EmailStr

from ProjectUtils.MessagingService.schemas import MessageFactory

# deny by default with dependency get_user
api_router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(get_user)])


@api_router.get("/management/types", response_model=list[str], status_code=status.HTTP_200_OK, summary="List available management event types.")
async def read_management_event_types():
    return models.management_event_types


@api_router.get("", response_model=list[UniformEventWithId], status_code=status.HTTP_200_OK, 
                summary="List of all events of a specific user, including reservations and cleaning/maintenance events.")
async def read_events_by_owner_email(reservation_status: models.ReservationStatus,
    owner_email: str = Depends(get_user_email), db: Session = Depends(get_db)):
    return crud.get_all_events_by_owner_email_and_filter_reservations_by_status(
        db, owner_email, reservation_status
    )


@api_router.get("/reservation", response_model=list[ReservationWithId], status_code=status.HTTP_200_OK, 
                summary="List of reservations related to a user and his properties.", 
                description="Returns list of reservations related to all, or a specific property, of a specific user based on his authorization bearer token.")
@api_router.get("/management/cleaning", response_model=list[CleaningWithId], status_code=status.HTTP_200_OK, 
                summary="List of cleaning events related to a user and his properties", 
                description="Returns list of cleaning events related to all, or a specific property, of a specific user based on his authorization bearer token.")
@api_router.get("/management/maintenance", response_model=list[MaintenanceWithId], status_code=status.HTTP_200_OK, 
                summary="List of maintenance events related to a user and his properties", 
                description="Returns list of maintenance events related to all, or a specific property, of a specific user based on his authorization bearer token.")
async def read_specific_events_by_owner_email(
        owner_email: str = Depends(get_user_email),
        property_id: int = None,
        event_model: models.Reservation | models.Cleaning | models.Maintenance = Depends(get_event_model),
        db: Session = Depends(get_db)
):
    if property_id is None:
        return crud.get_specific_events_by_owner_email(db, owner_email, event_model)
    return crud.get_specific_events_by_owner_email_and_property_id(db, owner_email, property_id, event_model)


@api_router.post("/management/cleaning", response_model=CleaningWithId, status_code=status.HTTP_201_CREATED, 
                 summary="Create new cleaning event",
                 description="Creates a new cleaning event for the specified property and the given timeframe",
                 responses={
                    status.HTTP_404_NOT_FOUND: {
                        "description": "Specified property for creating event does not exist.",
                        "content": {"application/json": {"example": {"detail": "Specified property for creating event does not exist."}}}
                    },
                    status.HTTP_409_CONFLICT: {
                        "description": "There are overlapping events with the event to be created.",
                        "content": {"application/json": {"example": {"detail": "There are overlapping events with the event to be created."}}}
                    }
                },
                openapi_extra={
                    "requestBody": {
                        "required": "true",
                        "content": {
                            "application/json": {
                                "example": {
                                    "worker_name": "Great person",
                                    "property_id": "1",
                                    "owner_email": "owner@gmail.com",
                                    "begin_datetime": "2024-05-30T10:37:34",
                                    "end_datetime": "2024-05-31T10:37:34"
                                }
                            }
                        }
                    }
                },
            )
@api_router.post("/management/maintenance", response_model=MaintenanceWithId, status_code=status.HTTP_201_CREATED,
                 summary="Create new maintenance event",
                 description="Creates a new maintenance event for the specified property and the given timeframe",
                 responses={
                    status.HTTP_404_NOT_FOUND: {
                        "description": "Specified property for creating event does not exist.",
                        "content": {"application/json": {"example": {"detail": "Specified property for creating event does not exist."}}}
                    },
                    status.HTTP_409_CONFLICT: {
                        "description": "There are overlapping events with the event to be created.",
                        "content": {"application/json": {"example": {"detail": "There are overlapping events with the event to be created."}}}
                    }
                },
                openapi_extra={
                    "requestBody": {
                        "required": "true",
                        "content": {
                            "application/json": {
                                "example": {
                                    "company_name": "Maintenance Lda.",
                                    "property_id": "1",
                                    "owner_email": "owner@gmail.com",
                                    "begin_datetime": "2024-05-30T10:37:34",
                                    "end_datetime": "2024-05-31T10:37:34"
                                }
                            }
                        }
                    }
                },            )
async def create_management_event(
        event_data: Cleaning | Maintenance = Depends(InitializeEventWithOwnerEmail()),
        event_model: models.Cleaning | models.Maintenance = Depends(get_management_event_model),
        owner_email: str = Depends(get_user_email),
        db: Session = Depends(get_db)
):
    if event_data.property_id not in crud.get_property_ids_by_email(db, owner_email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"There are no registered properties for email {owner_email} which you can create events for."
        )

    if crud.there_are_overlapping_events(db, event_data):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"There are overlapping events with the event with begin_datetime {event_data.begin_datetime} "
                   f"and end_datetime {event_data.end_datetime}.")
    db_event = crud.create_management_event(db, event_data, event_model)
    await propagate_event_creation_to_wrappers(db_event)
    return db_event


@api_router.put("/management/cleaning/{event_id}", response_model=CleaningWithId, status_code=status.HTTP_200_OK,
                summary="Update cleaning event",
                description="Updates the cleaning event with the given id and the specified parameters. "
                            "If the begin_datetime or end_datetime parameters are updated, the system will check for overlapping events.",
                responses={
                    status.HTTP_404_NOT_FOUND: {
                        "description": "Specified event for updating does not exist.",
                        "content": {"application/json": {"example": {"detail": "Specified event for updating does not exist."}}}
                    },
                    status.HTTP_409_CONFLICT: {
                        "description": "There are overlapping events with the given interval for the event to be updated.",
                        "content": {"application/json": {"example": {"detail": "There are overlapping events with the given interval for the event to be updated."}}}
                    }
                })
@api_router.put("/management/maintenance/{event_id}", response_model=MaintenanceWithId, status_code=status.HTTP_200_OK,
                summary="Update maintenance event",
                description="Updates the maintenance event with the given id and the specified parameters. "
                            "If the begin_datetime or end_datetime parameters are updated, the system will check for overlapping events.",
                responses={
                    status.HTTP_404_NOT_FOUND: {
                        "description": "Specified event for updating does not exist.",
                        "content": {"application/json": {"example": {"detail": "Specified event for updating does not exist."}}}
                    },
                    status.HTTP_409_CONFLICT: {
                        "description": "There are overlapping events with the given time interval for the event to be updated.",
                        "content": {"application/json": {"example": {"detail": "There are overlapping events with the given time interval for the event to be updated."}}}
                    }
                })
async def update_event(
        event_id: int,
        update_event_data: UpdateCleaning | UpdateMaintenance = Depends(InitializeUpdateEventAccordingToEndpoint()),
        event_model: models.Cleaning | models.Maintenance = Depends(get_management_event_model),
        owner_email: EmailStr = Depends(get_user_email), db: Session = Depends(get_db)
):
    event_to_update = crud.get_management_event_by_id(db, event_model, event_id)
    if event_to_update is None or owner_email != event_to_update.owner_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event of type {event_model.__tablename__} with id {event_id} not found for email {owner_email}."
        )

    update_parameters = {field_name: field_value for field_name, field_value in update_event_data
                         if field_value is not None}

    if len(update_parameters) == 0:
        # The update is empty, but we should still return the matching record:
        return event_to_update

    begin_end_datetime_update_parameters = {key: value for key in ["begin_datetime", "end_datetime"]
                                            if (value := update_parameters.get(key)) is not None}

    if len(begin_end_datetime_update_parameters) > 0:
        updating_event = BaseEventWithId(
            id=event_to_update.id,
            property_id=event_to_update.property_id,
            owner_email=event_to_update.owner_email,
            begin_datetime=begin_end_datetime_update_parameters.get("begin_datetime", event_to_update.begin_datetime),
            end_datetime=begin_end_datetime_update_parameters.get("end_datetime", event_to_update.end_datetime),
            type=event_model.__tablename__
        )
        if crud.there_are_overlapping_events_excluding_updating_event(db, updating_event):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"There are overlapping events with the event "
                       f"with begin_datetime {updating_event.begin_datetime} "
                       f"and end_datetime {updating_event.end_datetime}.")

    db_event = crud.update_event(db, event_to_update, update_parameters)
    if len(begin_end_datetime_update_parameters) > 0:
        await propagate_event_update_to_wrappers(db_event)
    return db_event


@api_router.delete("/management/cleaning/{event_id}", status_code=status.HTTP_204_NO_CONTENT,
                   summary="Delete cleaning event",
                   description="Deletes the cleaning event with the given id.",
                   responses={
                       status.HTTP_404_NOT_FOUND: {
                            "description": "Specified event for deletion does not exist.",
                            "content": {"application/json": {"example": {"detail": "Specified event for deletion does not exist."}}}
                       }
                   })
@api_router.delete("/management/maintenance/{event_id}", status_code=status.HTTP_204_NO_CONTENT,
                   summary="Delete maintenance event",
                   description="Deletes the maintenance event with the given id.",
                   responses={
                       status.HTTP_404_NOT_FOUND: {
                            "description": "Specified event for deletion does not exist.",
                            "content": {"application/json": {"example": {"detail": "Specified event for deletion does not exist."}}}
                       }
                   })
async def delete_management_event_by_id(
        event_id: int,
        event_model: models.Cleaning | models.Maintenance = Depends(get_management_event_model),
        owner_email: EmailStr = Depends(get_user_email),
        db: Session = Depends(get_db)
):
    management_event = crud.get_management_event_by_owner_email_and_event_id(db, event_model, owner_email, event_id)
    if management_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Event of type {event_model.__tablename__} with id {event_id} for email {owner_email} not found")
    db_event = crud.delete_management_event(db, management_event)
    await propagate_event_deletion_to_wrappers(db_event)


@api_router.post("/reservation/{reservation_id}/email_key", status_code=204,
                 summary="Send email with key to reservation client",
                 description="Sends an email to the client of the reservation with the given id. \
                    The email contains the key to the property.",
                 responses={
                     status.HTTP_404_NOT_FOUND: {
                        "description": "Reservation with the given id for the email does not exist.",
                        "content": {"application/json": {"example": {"detail": "Reservation with the given id for the email does not exist."}}}
                     }
                 })
async def send_email_with_key(reservation_id: int, key_input: KeyInput, owner_email: EmailStr = Depends(get_user_email),
                              db: Session = Depends(get_db)):

    reservation: models.Reservation = crud.get_reservation_by_internal_id(db, reservation_id)

    if reservation is None or reservation.owner_email != owner_email:
        raise HTTPException(status_code=404, detail=f"Reservation with id {reservation_id} for email {owner_email} not found.")

    await crud.send_email_to_reservation_client(db, key_input.key, reservation)
