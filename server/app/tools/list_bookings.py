from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.config import get_settings, Settings
from app.tools.book_flight import load_bookings_from_file

router = APIRouter()


class BookingSummary(BaseModel):
    booking_id: str
    flight_id: str
    passenger_name: str
    status: str
    booked_at: str
    origin: str
    destination: str
    date: str
    airline: str
    price: float


class ListBookingsResponse(BaseModel):
    tool: str = "list_bookings"
    bookings: list[BookingSummary]
    total: int


@router.get("/listBookings", response_model=ListBookingsResponse)
def list_bookings(
    include_cancelled: bool = False,
    settings: Settings = Depends(get_settings)
):
    """
    MCP Tool: list_bookings
    Returns all confirmed flight bookings.
    """
    raw_bookings = load_bookings_from_file(settings.data_dir)

    # By default only return active (non-cancelled) bookings
    if not include_cancelled:
        raw_bookings = [b for b in raw_bookings if b.get("status") != "CANCELLED"]

    summaries = []
    for b in raw_bookings:
        fd = b.get("flight_details", {})
        summaries.append(
            BookingSummary(**{
                "booking_id": b["booking_id"],
                "flight_id": b["flight_id"],
                "passenger_name": b["passenger_name"],
                "status": b["status"],
                "booked_at": b["booked_at"],
                "origin": fd.get("origin", ""),
                "destination": fd.get("destination", ""),
                "date": fd.get("date", ""),
                "airline": fd.get("airline", ""),
                "price": fd.get("price", 0.0),
            })
        )

    return ListBookingsResponse(**{"bookings": summaries, "total": len(summaries)})
