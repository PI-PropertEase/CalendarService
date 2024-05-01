from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr
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


class InternalEvent(BaseEvent):
    pass


class ExternalEvent(BaseEvent):
    external_id: int  # generated with a certain id the on website wrappers


class Cleaning(InternalEvent):
    pass


class UpdateCleaning(BaseModel):
    property_id: Optional[int] = None
    begin_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None


class Maintenance(InternalEvent):
    pass


class UpdateMaintenance(BaseModel):
    property_id: Optional[int] = None
    begin_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None


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
