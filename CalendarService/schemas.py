from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

PhoneNumber.phone_format = 'E164'  # 'INTERNATIONAL'


class UserBase(BaseModel):
    email: EmailStr


class EventStatusEnum(str, Enum):
    ONGOING = "OnGoing"
    PENDING = "Pending"


class Service(str, Enum):
    ZOOKING = "zooking"
    EARTHSTAYIN = "earthstayin"
    CLICKANDGO = "clickandgo"



class Event(BaseModel):
    id: int
    property_id: int
    begin_datetime: datetime
    end_datetime: datetime


class Reservation(Event):
    status: EventStatusEnum
    service: Service
    client_email: EmailStr
    client_name: str
    client_phone: PhoneNumber
    cost: float
