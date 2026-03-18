import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.config import get_settings, Settings

router = APIRouter()

# In-memory bookings store (persisted to JSON on each write)
_bookings: dict[str, dict] = {}


class BookFlightRequest(BaseModel):
    flight_id: str
    passenger_name: str


class BookingResult(BaseModel):
    booking_id: str
    flight_id: str
    passenger_name: str
    status: str
    booked_at: str
    flight_details: dict


class BookFlightResponse(BaseModel):
    tool: str = "book_flight"
    success: bool
    booking: BookingResult
    message: str


def load_flights(data_dir: str) -> list[dict]:
    flights_path = Path(data_dir) / "flights.json"
    with open(flights_path, "r") as f:
        data = json.load(f)
    return data["flights"]


def save_booking(booking: dict, data_dir: str) -> None:
    """Persist booking to JSON file."""
    bookings_path = Path(data_dir) / "bookings.json"
    existing = []
    if bookings_path.exists():
        with open(bookings_path, "r") as f:
            existing = json.load(f)
    existing.append(booking)
    with open(bookings_path, "w") as f:
        json.dump(existing, f, indent=2)


@router.post("/bookFlight", response_model=BookFlightResponse)
def book_flight(
    payload: BookFlightRequest,
    settings: Settings = Depends(get_settings),
):
    """
    MCP Tool: book_flight
    Books a flight for a passenger by flight ID.
    """
    all_flights = load_flights(settings.data_dir)

    flight = next((f for f in all_flights if f["id"] == payload.flight_id), None)

    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight '{payload.flight_id}' not found.",
        )

    if flight["seats_available"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No seats available on flight '{payload.flight_id}'.",
        )

    booking_id = f"BK{uuid.uuid4().hex[:8].upper()}"
    booked_at = datetime.utcnow().isoformat() + "Z"

    booking = {
        "booking_id": booking_id,
        "flight_id": payload.flight_id,
        "passenger_name": payload.passenger_name,
        "status": "CONFIRMED",
        "booked_at": booked_at,
        "flight_details": flight,
    }

    # Store in memory
    _bookings[booking_id] = booking

    # Persist to file
    save_booking(booking, settings.data_dir)

    return BookFlightResponse(**{
        "success": True,
        "booking": BookingResult(**booking),
        "message": f"Flight {payload.flight_id} successfully booked for {payload.passenger_name}.",
    })


def get_all_bookings() -> list[dict]:
    """Return all in-memory bookings."""
    return list(_bookings.values())


def load_bookings_from_file(data_dir: str) -> list[dict]:
    """Load bookings from JSON file."""
    bookings_path = Path(data_dir) / "bookings.json"
    if not bookings_path.exists():
        return []
    with open(bookings_path, "r") as f:
        return json.load(f)
