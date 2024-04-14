from CalendarService.schemas import Reservation
from ProjectUtils.MessagingService.schemas import BaseMessage


def from_reservation_create(message: BaseMessage):
    body = message.body
    return Reservation(
        id=body["id"],
        property_id=body["property_id"],
        begin_datetime=body["begin_datetime"],
        end_datetime=body["end_datetime"],
        status=body["status"],
        service="zooking",
        client_name=body["client_name"],
        client_phone=body["client_phone"],
        cost=body["cost"]
    )
