from sqlalchemy import Column, Integer, String, DateTime, Enum, Float
from enum import Enum as EnumType
from .database import Base


class Service(EnumType):
    ZOOKING = "zooking"


class EventStatus(EnumType):
    ONGOING = "OnGoing"
    PENDING = "Pending"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, index=True)
    status = Column(Enum(EventStatus))
    begin_datetime = Column(DateTime)
    end_datetime = Column(DateTime)


class Reservation(Event):
    service = Column(Enum(Service))
    client_name = Column(String)
    client_phone = Column(String) #TODO change to phone number if possible
    cost = Column(Float)

