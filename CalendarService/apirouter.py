from fastapi import APIRouter, Depends, status, HTTPException

from CalendarService.dependencies import get_user, get_db

from CalendarService.schemas import Reservation, Cleaning, Maintenance, UniformEvent, UserBase
from sqlalchemy.orm import Session
from CalendarService.crud import create_cleaning, create_maintenance, get_events_by_owner_email
from CalendarService.models import management_event_types
from CalendarService.crud import there_are_overlapping_events
from CalendarService.dependencies import Initialize_event_with_owner_email

# deny by default with dependency get_user
api_router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(get_user)])

@api_router.get("", response_model=list[UniformEvent], status_code=status.HTTP_200_OK)
async def read_events_by_owner_email(user: UserBase = Depends(get_user), db: Session = Depends(get_db)):
    return get_events_by_owner_email(db, user.email)


@api_router.get("/management/types", response_model=list[str], status_code=status.HTTP_200_OK)
async def read_management_event_types():
    return management_event_types

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