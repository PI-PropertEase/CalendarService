from fastapi import Depends, HTTPException, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ProjectUtils.DecoderService.decode_token import decode_token
from CalendarService.database import SessionLocal
from CalendarService.schemas import UserBase, Cleaning
from pydantic import EmailStr

from CalendarService.schemas import Base
from pydantic_core._pydantic_core import ValidationError


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


class Initialize_event_with_owner_email:
    def __init__(self, Base_event):
        # Event is the class with which I shall initialize the object
        # It will be passed according to the endpoint which is called
        self.Base_event = Base_event

    def __call__(self, base: Base, email: EmailStr = Depends(get_user_email)):

        try:
            event = self.Base_event(owner_email=email, **base.model_dump(exclude={"owner_email"}))
            event.owner_email = email
            print("self.Base_event", self.Base_event)
            print("event", event)
        except ValidationError as e:
            raise HTTPException(422, detail=e.errors())
        return event

