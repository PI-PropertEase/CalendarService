from datetime import datetime
from enum import Enum
from typing import Optional
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr, model_validator
from pydantic_core import ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber

PhoneNumber.phone_format = 'E164'  # 'INTERNATIONAL'

"""
Receiving Schemas - in API endpoints or messaging
"""


class Base(BaseModel):
    class Config:
        extra = "allow"


class UserBase(BaseModel):
    email: EmailStr


class Service(str, Enum):
    ZOOKING = "zooking"
    EARTHSTAYIN = "earthstayin"
    CLICKANDGO = "clickandgo"


class BaseEvent(BaseModel):
    property_id: int
    owner_email: EmailStr
    begin_datetime: datetime
    end_datetime: datetime

    @model_validator(mode="after")
    def validate(self):
        if self.begin_datetime < datetime.now():
            raise RequestValidationError("begin_datetime cannot be in the past")
        if self.begin_datetime >= self.end_datetime:
            raise RequestValidationError("begin_datetime cannot be greater or equal to end_datetime")
        return self


class InternalEvent(BaseEvent):
    pass


class ExternalEvent(BaseEvent):
    external_id: int  # generated with a certain id the on website wrappers


class Cleaning(InternalEvent):
    pass


class UpdateCleaning(BaseModel):
    begin_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None

    @model_validator(mode="after")
    def validate(self):
        begin_end_datetime_none_size = [mydatetime for mydatetime in [self.begin_datetime, self.end_datetime] if mydatetime is None]
        if len(begin_end_datetime_none_size) != 2:
            if len(begin_end_datetime_none_size) != 0:
                raise RequestValidationError("begin_datetime and end_datetime have to both be specified or both not specified")
            else:
                if self.begin_datetime < datetime.now():
                    raise RequestValidationError("begin_datetime cannot be in the past")
                if self.begin_datetime >= self.end_datetime:
                    raise RequestValidationError("begin_datetime cannot be greater or equal to end_datetime")
        return self


class Maintenance(InternalEvent):
    pass


class UpdateMaintenance(BaseModel):
    begin_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None

    @model_validator(mode="after")
    def validate(self):
        begin_end_datetime_none_size = [mydatetime for mydatetime in [self.begin_datetime, self.end_datetime] if mydatetime is None]
        if len(begin_end_datetime_none_size) != 2:
            if len(begin_end_datetime_none_size) != 0:
                raise RequestValidationError("begin_datetime and end_datetime have to both be specified or both not specified")
            else:
                if self.begin_datetime < datetime.now():
                    raise RequestValidationError("begin_datetime cannot be in the past")
                if self.begin_datetime >= self.end_datetime:
                    raise RequestValidationError("begin_datetime cannot be greater or equal to end_datetime")
        return self


class ReservationStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELED = "canceled"


class Reservation(ExternalEvent):
    service: Service
    reservation_status: ReservationStatus
    client_email: EmailStr
    client_name: str
    client_phone: PhoneNumber
    cost: float


"""
Returning Schemas
id -> internal id
"""


class UniformEventWithId(BaseModel):
    # schema to return when asked for all events
    # particular fields of certain events have default value None
    id: int
    property_id: int
    owner_email: EmailStr
    begin_datetime: datetime
    end_datetime: datetime
    type: str
    service: Optional[Service] = None


class BaseEventWithId(BaseModel):
    id: int
    property_id: int
    owner_email: EmailStr
    begin_datetime: datetime
    end_datetime: datetime
    type: str


class ManagementEventWithId(BaseEventWithId):
    pass


class CleaningWithId(ManagementEventWithId):
    pass


class MaintenanceWithId(ManagementEventWithId):
    pass


class ReservationWithId(BaseEventWithId):
    service: Service
    reservation_status: ReservationStatus
    client_email: EmailStr
    client_name: str
    client_phone: PhoneNumber
    cost: float
