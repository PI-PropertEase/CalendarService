from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

PhoneNumber.phone_format = 'E164'  # 'INTERNATIONAL'


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
    # generated with a certain id the on website wrappers
    external_id: int


class Cleaning(InternalEvent):
    pass

class Maintenance(BaseModel):
    pass


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


class UniformEvent(BaseModel):
    # schema to return when asked for all events
    # particular fields of certain events have default value None
    id: int                                 # internal_id
    property_id: int
    owner_email: EmailStr
    begin_datetime: datetime
    end_datetime: datetime
    type: str
    service: Optional[Service] = None

