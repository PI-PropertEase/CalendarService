from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Boolean
from enum import Enum as EnumType
from .database import Base


class Service(EnumType):
    ZOOKING = "zooking"
    EARTHSTAYIN = "earthstayin"
    CLICKANDGO = "clickandgo"


class Event(Base):
    __tablename__ = "event"
    __mapper_args__ = {
        "polymorphic_identity": "event",
        "polymorphic_on": "type",
    }

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, index=True)
    owner_email = Column(String)
    begin_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    type = Column(String)


class ReservationStatus(EnumType):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELED = "canceled"


class Reservation(Event):
    __tablename__ = "reservation"
    __mapper_args__ = {
        "polymorphic_identity": "reservation",
    }

    id = Column(Integer, ForeignKey("event.id"), primary_key=True)
    reservation_status = Column(Enum(ReservationStatus))
    client_email = Column(String) # TODO VER SE NÃO É EMAIL
    client_name = Column(String)
    client_phone = Column(String) #TODO change to phone number type if possible
    cost = Column(Float)
    service = Column(Enum(Service))




