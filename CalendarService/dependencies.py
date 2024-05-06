from fastapi import Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ProjectUtils.DecoderService.decode_token import decode_token
from CalendarService.database import SessionLocal
from CalendarService.schemas import UserBase, Cleaning
from pydantic import EmailStr
from CalendarService.schemas import Base
from pydantic_core._pydantic_core import ValidationError
from CalendarService import models
from CalendarService import schemas


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user(res: Response, cred: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    decoded_token = decode_token(res, cred)
    return UserBase(**decoded_token)


def get_user_email(user: UserBase = Depends(get_user)):
    return user.email


def get_request_url_path(request: Request):
    return request.url.path


def get_event_model(request_url_path: str = Depends(get_request_url_path)):
    print("running get_event_model")
    if request_url_path.split("/")[2] == "reservation":
        return models.Reservation
    return get_management_event_model(request_url_path)


def get_management_event_model(request_url_path: str = Depends(get_request_url_path)):
    print("running get_management_event_model")
    match request_url_path.split("/")[3]:
        case "cleaning":
            return models.Cleaning
        case "maintenance":
            return models.Maintenance


def get_management_event_schema(request_url_path: str = Depends(get_request_url_path)):
    print("running get_management_event_schema")
    match request_url_path.split("/")[3]:
        case "cleaning":
            return schemas.Cleaning
        case "maintenance":
            return schemas.Maintenance


def get_update_management_event_schema(request_url_path: str = Depends(get_request_url_path)):
    print("running get_update_management_event_schema")
    match request_url_path.split("/")[3]:
        case "cleaning":
            return schemas.UpdateCleaning
        case "maintenance":
            return schemas.UpdateMaintenance


class InitializeEventWithOwnerEmail:

    def __call__(self, base: Base, EventSchema=Depends(get_management_event_schema),
                 email: EmailStr = Depends(get_user_email)):
        print("EventSchema", EventSchema)
        try:
            event = EventSchema(owner_email=email, **base.model_dump(exclude={"owner_email"}))
            event.owner_email = email
            print("EventSchema", EventSchema)
            print("event", event)
        except ValidationError as e:
            raise HTTPException(422, detail=e.errors())
        return event


class InitializeUpdateEventAccordingToEndpoint:

    def __call__(self, base: Base, UpdateEventSchema=Depends(get_update_management_event_schema)):
        try:
            event = UpdateEventSchema(**base.model_dump())
            print("event", event)
        except ValidationError as e:
            raise HTTPException(422, detail=e.errors())
        return event
