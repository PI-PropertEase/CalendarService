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



class Event(BaseModel):
    id: int
    property_id: int
    owner_email: EmailStr
    begin_datetime: datetime
    end_datetime: datetime


class Reservation(Event):
    service: Service
    confirmed: bool
    client_email: EmailStr
    client_name: str
    client_phone: PhoneNumber
    cost: float


class UniformEvent(BaseModel):
    id: int
    property_id: int
    owner_email: EmailStr
    begin_datetime: datetime
    end_datetime: datetime
    type: str
    service: Optional[Service] = None

