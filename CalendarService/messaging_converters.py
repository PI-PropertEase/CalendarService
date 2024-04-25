from CalendarService.schemas import Reservation, Service
from ProjectUtils.MessagingService.schemas import BaseMessage


def from_reservation_create(service_value: str, reservation_dict: dict):
    return Reservation(
        id=reservation_dict["_id"],
        property_id=reservation_dict["property_id"],
        owner_email = reservation_dict["owner_email"],
        begin_datetime=reservation_dict["begin_datetime"],
        end_datetime=reservation_dict["end_datetime"],
        service=Service(service_value),
        client_email=reservation_dict["client_email"],
        client_name=reservation_dict["client_name"],
        client_phone=reservation_dict["client_phone"],
        cost=reservation_dict["cost"],
        confirmed=reservation_dict["confirmed"]
    )
