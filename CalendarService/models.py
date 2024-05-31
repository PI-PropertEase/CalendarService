from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Boolean
from enum import Enum as EnumType
from .database import Base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList

class Service(EnumType):
    ZOOKING = "zooking"
    EARTHSTAYIN = "earthstayin"
    CLICKANDGO = "clickandgo"


class EmailPropertyIdMapping(Base):
    __tablename__ = "email_property_id_mapping"
    email = Column(String, primary_key=True)
    properties_ids = Column(MutableList.as_mutable(ARRAY(Integer)))


class BaseEvent(Base):
    __tablename__ = "base_event"
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "base_event",
    }
    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, index=True)
    owner_email = Column(String)
    begin_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    type = Column(String)


class InternalEvent(BaseEvent):
    __tablename__ = "internal_event"
    __mapper_args__ = {
        "polymorphic_identity": "internal_event",
        # polymorphic_identity will be overwritten by the subclasses
    }
    id = Column(Integer, ForeignKey("base_event.id"), primary_key=True)


class ExternalEvent(BaseEvent):
    __tablename__ = "external_event"
    __mapper_args__ = {
        "polymorphic_identity": "external_event",
        # polymorphic_identity will be overwritten by the subclasses
    }
    id = Column(Integer, ForeignKey("base_event.id"), primary_key=True)
    external_id = Column(Integer, index=True)


class ManagementEvent(InternalEvent):
    __tablename__ = "management_event"
    __mapper_args__ = {
        "polymorphic_identity": "management_event",
        # polymorphic_identity will be overwritten by the subclasses
    }
    id = Column(Integer, ForeignKey("internal_event.id"), primary_key=True)


class Maintenance(ManagementEvent):
    __tablename__ = "maintenance"
    __mapper_args__ = {
        "polymorphic_identity": "maintenance",
    }
    id = Column(Integer, ForeignKey("management_event.id"), primary_key=True)
    company_name = Column(String)


class Cleaning(ManagementEvent):
    __tablename__ = "cleaning"
    __mapper_args__ = {
        "polymorphic_identity": "cleaning",
    }
    id = Column(Integer, ForeignKey("management_event.id"), primary_key=True)
    worker_name = Column(String)


class ReservationStatus(EnumType):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELED = "canceled"


class Reservation(ExternalEvent):
    __tablename__ = "reservation"
    __mapper_args__ = {
        "polymorphic_identity": "reservation",
    }

    id = Column(Integer, ForeignKey("external_event.id"), primary_key=True)
    reservation_status = Column(Enum(ReservationStatus))
    client_email = Column(String)
    client_name = Column(String)
    client_phone = Column(String)
    cost = Column(Float)
    service = Column(Enum(Service))


management_event_types = [management_event.__tablename__ for management_event in ManagementEvent.__subclasses__()]
