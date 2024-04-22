from sqlalchemy import Column, Integer, String, DateTime, Enum, Float
from enum import Enum as EnumType
from .database import Base


class Service(EnumType):
    ZOOKING = "zooking"
    EARTHSTAYIN = "earthstayin"
    CLICKANDGO = "clickandgo"


class EventStatus(EnumType):
    ONGOING = "OnGoing"
    PENDING = "Pending"


class Event(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, index=True)
    status = Column(Enum(EventStatus))
    begin_datetime = Column(DateTime)
    end_datetime = Column(DateTime)


class Reservation(Event):
    __tablename__ = "reservations"

    client_email = Column(String) # TODO VER SE NÃO É EMAIL
    client_name = Column(String)
    client_phone = Column(String) #TODO change to phone number type if possible
    cost = Column(Float)
    service = Column(Enum(Service))



