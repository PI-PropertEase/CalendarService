from CalendarService.schemas import Reservation, Service


def from_reservation_create(service_value: str, reservation_dict: dict):
    return Reservation(
        external_id=reservation_dict["_id"],
        property_id=reservation_dict["property_id"],
        owner_email = reservation_dict["owner_email"],
        begin_datetime=reservation_dict["begin_datetime"],
        end_datetime=reservation_dict["end_datetime"],
        service=Service(service_value),
        client_email=reservation_dict["client_email"],
        client_name=reservation_dict["client_name"],
        client_phone=reservation_dict["client_phone"],
        cost=reservation_dict["cost"],
        reservation_status=reservation_dict["reservation_status"]
    )
