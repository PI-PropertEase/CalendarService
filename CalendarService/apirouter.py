from fastapi import APIRouter, Depends, status, HTTPException, Request

from CalendarService.dependencies import get_user, get_db, get_user_email

from CalendarService.schemas import Reservation, Cleaning, Maintenance, UniformEvent, UserBase
from sqlalchemy.orm import Session
from CalendarService.crud import create_cleaning, create_maintenance, get_events_by_owner_email, get_management_event_by_owner_email_and_event_id, delete_management_event
from CalendarService import models
from CalendarService.crud import there_are_overlapping_events
from CalendarService.dependencies import Initialize_event_with_owner_email
from pydantic import EmailStr

# deny by default with dependency get_user
api_router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(get_user)])

@api_router.get("", response_model=list[UniformEvent], status_code=status.HTTP_200_OK)
async def read_events_by_owner_email(user: UserBase = Depends(get_user), db: Session = Depends(get_db)):
    for event in get_events_by_owner_email(db, user.email):
        print(event.__dict__)
    return get_events_by_owner_email(db, user.email)


@api_router.get("/management/types", response_model=list[str], status_code=status.HTTP_200_OK)
async def read_management_event_types():
    return models.management_event_types

@api_router.post("/management/cleaning", response_model=Cleaning, status_code=status.HTTP_201_CREATED)
async def create_cleaning_event(cleaning: Cleaning = Depends(Initialize_event_with_owner_email(Cleaning)),db: Session = Depends(get_db)):
    if there_are_overlapping_events(db, cleaning):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"There are overlapping events with the event with begin_datetime {cleaning.begin_datetime} "
                   f"and end_datetime {cleaning.end_datetime}.")
    return create_cleaning(db, cleaning)

@api_router.post("/management/maintenance", response_model=Cleaning, status_code=status.HTTP_201_CREATED)
async def create_maintenance_event(maintenance: Maintenance = Depends(Initialize_event_with_owner_email(Maintenance)), db: Session = Depends(get_db)):
    if there_are_overlapping_events(db, maintenance):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"There are overlapping events with the event with begin_datetime {maintenance.begin_datetime} "
                   f"and end_datetime {maintenance.end_datetime}.")
    return create_maintenance(db, maintenance)

@api_router.delete("/management/cleaning/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
@api_router.delete("/management/maintenance/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_management_event_by_id(event_id: int, request: Request, owner_email: EmailStr = Depends(get_user_email), db: Session = Depends(get_db)):
    match request.url.path.split("/")[-2]:
        case "cleaning":
            ManagementEventClass = models.Cleaning
        case "maintenance":
            ManagementEventClass = models.Maintenance

    management_event = get_management_event_by_owner_email_and_event_id(db, ManagementEventClass, owner_email, event_id)
    if management_event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event of type {ManagementEventClass.__tablename__} with id {event_id} for email {owner_email} not found")
    delete_management_event(db, management_event)
