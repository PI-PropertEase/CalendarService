from fastapi import APIRouter, Depends, status

from CalendarService.dependencies import get_user, get_db

from CalendarService.schemas import Reservation, Cleaning
from sqlalchemy.orm import Session
from CalendarService.crud import create_cleaning, get_cleaning_by_id

# deny by default with dependency get_user
api_router = APIRouter(prefix="/events", tags=["events"], dependencies=[])


@api_router.get("/types", response_model=list[str], status_code=status.HTTP_200_OK)
async def get_event_types():
    return ["reservation", "booking"]

@api_router.post("/cleaning", response_model=Reservation, status_code=status.HTTP_201_CREATED)
async def create_cleaning_event(cleaning: Cleaning, db: Session = Depends(get_db)):
    return create_cleaning(db, cleaning)