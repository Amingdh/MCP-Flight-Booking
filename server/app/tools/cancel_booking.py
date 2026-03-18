import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.config import get_settings, Settings

router = APIRouter()


class CancelBookingRequest(BaseModel):
    booking_id: str


class CancelBookingResponse(BaseModel):
    tool: str = "cancel_booking"
    success: bool
    message: str
    booking_id: str
    cancelled_at: str = ""


def load_and_cancel(booking_id: str, data_dir: str) -> dict:
    """
    Load bookings.json, mark the target booking as CANCELLED,
    write the file back, and return a result dict.
    """
    bookings_path = Path(data_dir) / "bookings.json"
    if not bookings_path.exists():
        return {"found": False}

    with open(bookings_path, "r", encoding="utf-8") as f:
        bookings: list[dict] = json.load(f)

    target = next((b for b in bookings if b["booking_id"] == booking_id), None)

    if target is None:
        return {"found": False}

    if target["status"] == "CANCELLED":
        return {"found": True, "already_cancelled": True, "booking": target}

    target["status"] = "CANCELLED"
    target["cancelled_at"] = datetime.utcnow().isoformat() + "Z"

    with open(bookings_path, "w", encoding="utf-8") as f:
        json.dump(bookings, f, indent=2)

    return {"found": True, "already_cancelled": False, "booking": target}


@router.post("/cancelBooking", response_model=CancelBookingResponse)
def cancel_booking(
    payload: CancelBookingRequest,
    settings: Settings = Depends(get_settings),
):
    """
    MCP Tool: cancel_booking
    Marks a booking as CANCELLED in the persistent store.
    Returns success/failure with the cancellation timestamp.
    """
    result = load_and_cancel(payload.booking_id, settings.data_dir)

    if not result["found"]:
        return CancelBookingResponse(**{
            "success": False,
            "message": f"Booking '{payload.booking_id}' not found.",
            "booking_id": payload.booking_id,
        })

    if result["already_cancelled"]:
        return CancelBookingResponse(**{
            "success": False,
            "message": f"Booking '{payload.booking_id}' is already cancelled.",
            "booking_id": payload.booking_id,
        })

    cancelled_at = result["booking"]["cancelled_at"]
    return CancelBookingResponse(**{
        "success": True,
        "message": f"Booking '{payload.booking_id}' has been successfully cancelled.",
        "booking_id": payload.booking_id,
        "cancelled_at": cancelled_at,
    })
