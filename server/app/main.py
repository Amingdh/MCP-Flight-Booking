"""
Flight Booking MCP Server
=========================
Uses the official MCP Python SDK (FastMCP).

Supports two transports:
  stdio  — default, used by MCP Inspector and Claude Desktop
  sse    — HTTP server, used for browser/HTTP clients

Run modes:
  python -m app.main            -> stdio (MCP Inspector)
  python -m app.main --sse      -> SSE HTTP server on :8000

MCP Inspector command:
  npx @modelcontextprotocol/inspector \
    uv run python -m app.main
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Fix python path when running via `python app/main.py` directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

PORT         = int(os.getenv("PORT", "8000"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "flight-mcp-server")
DATA_DIR     = Path(os.getenv("DATA_DIR", "data"))

# ── FastMCP server instance ──────────────────────────────────────────────────
mcp = FastMCP(
    name=SERVICE_NAME,
    instructions=(
        "You are a flight booking assistant. "
        "Use search_flights to find available flights, "
        "book_flight to reserve a seat, "
        "and list_bookings to review all reservations."
    ),
    host="0.0.0.0",
    port=PORT,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_flights() -> list[dict]:
    flights_path = DATA_DIR / "flights.json"
    with open(flights_path, "r") as f:
        return json.load(f)["flights"]


def _save_booking(booking: dict) -> None:
    bookings_path = DATA_DIR / "bookings.json"
    existing: list[dict] = []
    if bookings_path.exists():
        with open(bookings_path, "r") as f:
            existing = json.load(f)
    existing.append(booking)
    with open(bookings_path, "w") as f:
        json.dump(existing, f, indent=2)


def _load_bookings() -> list[dict]:
    bookings_path = DATA_DIR / "bookings.json"
    if not bookings_path.exists():
        return []
    with open(bookings_path, "r") as f:
        return json.load(f)


# ── MCP Tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> dict:
    """
    Search for available flights.

    Args:
        origin:      Departure city (e.g. "Paris")
        destination: Arrival city   (e.g. "Rome")
        date:        Travel date in YYYY-MM-DD format (e.g. "2026-04-01")

    Returns:
        A dict with matched flights and total count.
    """
    all_flights = _load_flights()
    matched = [
        f for f in all_flights
        if f["origin"].lower()       == origin.lower()
        and f["destination"].lower() == destination.lower()
        and f["date"]                == date
    ]
    return {
        "query":       {"origin": origin, "destination": destination, "date": date},
        "total_found": len(matched),
        "flights":     matched,
    }


@mcp.tool()
def book_flight(flight_id: str, passenger_name: str) -> dict:
    """
    Book a flight for a passenger.

    Args:
        flight_id:      The flight ID to book (e.g. "FL002")
        passenger_name: Full name of the passenger (e.g. "Alice Dupont")

    Returns:
        Booking confirmation with a unique booking ID and full flight details.
    """
    all_flights = _load_flights()
    flight = next((f for f in all_flights if f["id"] == flight_id), None)

    if not flight:
        return {"success": False, "error": f"Flight '{flight_id}' not found."}

    if flight["seats_available"] <= 0:
        return {"success": False, "error": f"No seats available on flight '{flight_id}'."}

    booking_id = f"BK{uuid.uuid4().hex[:8].upper()}"
    booking = {
        "booking_id":     booking_id,
        "flight_id":      flight_id,
        "passenger_name": passenger_name,
        "status":         "CONFIRMED",
        "booked_at":      datetime.utcnow().isoformat() + "Z",
        "flight_details": flight,
    }

    _save_booking(booking)

    return {
        "success": True,
        "message": f"Flight {flight_id} successfully booked for {passenger_name}.",
        "booking": booking,
    }


@mcp.tool()
def list_bookings() -> dict:
    """
    List all confirmed flight bookings.

    Returns:
        A dict with all bookings and total count.
    """
    bookings = _load_bookings()
    # Only return active (non-cancelled) bookings
    active_bookings = [b for b in bookings if b.get("status") != "CANCELLED"]
    summaries = [
        {
            "booking_id":     b["booking_id"],
            "flight_id":      b["flight_id"],
            "passenger_name": b["passenger_name"],
            "status":         b["status"],
            "booked_at":      b["booked_at"],
            "origin":         b["flight_details"].get("origin", ""),
            "destination":    b["flight_details"].get("destination", ""),
            "date":           b["flight_details"].get("date", ""),
            "airline":        b["flight_details"].get("airline", ""),
            "price":          b["flight_details"].get("price", 0.0),
        }
        for b in active_bookings
    ]
    return {"total": len(summaries), "bookings": summaries}


@mcp.tool()
def cancel_booking(booking_id: str) -> dict:
    """
    Cancel an existing flight booking.

    Args:
        booking_id: The booking ID to cancel (e.g. "BKA5FD8367")

    Returns:
        A dict with success status, message, and cancellation timestamp.
    """
    bookings_path = DATA_DIR / "bookings.json"
    if not bookings_path.exists():
        return {"success": False, "error": "No bookings found."}

    with open(bookings_path, "r", encoding="utf-8") as f:
        bookings: list[dict] = json.load(f)

    target = next((b for b in bookings if b["booking_id"] == booking_id), None)

    if target is None:
        return {"success": False, "error": f"Booking '{booking_id}' not found."}

    if target["status"] == "CANCELLED":
        return {"success": False, "error": f"Booking '{booking_id}' is already cancelled."}

    target["status"] = "CANCELLED"
    target["cancelled_at"] = datetime.utcnow().isoformat() + "Z"

    with open(bookings_path, "w", encoding="utf-8") as f:
        json.dump(bookings, f, indent=2)

    return {
        "success":      True,
        "booking_id":   booking_id,
        "message":      f"Booking '{booking_id}' has been successfully cancelled.",
        "cancelled_at": target["cancelled_at"],
    }



from mcp.types import PromptReference, Completion, CompletionArgument


# ── MCP Resources ────────────────────────────────────────────────────────────

@mcp.resource("flights://catalog")
def get_flights_catalog() -> str:
    """Read the complete raw flights catalog."""
    flights_path = DATA_DIR / "flights.json"
    if not flights_path.exists():
        return "{}"
    with open(flights_path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("bookings://current")
def get_current_bookings() -> str:
    """Read all current flight bookings as raw JSON."""
    bookings_path = DATA_DIR / "bookings.json"
    if not bookings_path.exists():
        return "[]"
    with open(bookings_path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("policies://company")
def get_company_policies() -> str:
    """Read the full markdown document containing airline luggage, cancellation, and pet policies."""
    policies_path = DATA_DIR / "company_policies.md"
    if not policies_path.exists():
        return "# Company Policies\nNot found."
    with open(policies_path, "r", encoding="utf-8") as f:
        return f.read()

@mcp.resource("airports://info")
def get_airports_info() -> str:
    """Read the JSON document containing detailed airport information, terminals, and transit options."""
    airports_path = DATA_DIR / "airports.json"
    if not airports_path.exists():
        return "{}"
    with open(airports_path, "r", encoding="utf-8") as f:
        return f.read()


# ── MCP Prompts ──────────────────────────────────────────────────────────────

@mcp.completion()
async def prompt_completions(ref: PromptReference, argument: CompletionArgument, context=None) -> Completion | None:
    """
    Handle argument auto-completion dynamically from the flights catalog.
    """
    all_flights = _load_flights()
    # Extract unique origins and destinations from the database
    cities = set([f["origin"] for f in all_flights] + [f["destination"] for f in all_flights])
    
    if isinstance(ref, PromptReference) and argument.name in ["origin", "destination", "start_city"]:
        matched = [c for c in cities if c.lower().startswith(argument.value.lower())]
        return Completion(values=matched)
    return None

@mcp.prompt()
def flight_search_prompt(origin: str = "Paris", destination: str = "Rome") -> str:
    """
    Create a prompt for searching flights between two cities.
    """
    return (
        f"I am looking for a flight from {origin} to {destination}. "
        "Please use the `search_flights` tool to find the best options. "
        "Summarize the results by price and departure time, and ask if I would like to book the cheapest option."
    )

@mcp.prompt()
def multi_city_itinerary_prompt(start_city: str = "Paris", duration_days: str = "7") -> str:
    """
    Plan a complex multi-city itinerary grounded in real catalog data.
    """
    return (
        f"I want to do a {duration_days}-day trip starting from {start_city}. "
        "Please read the `flights://catalog` resource to see EVERY flight we offer. "
        "Then, design a logical multi-city itinerary that uses ONLY the cities and flights that actually exist in our catalog starting from my start city. "
        "Provide a day-by-day breakdown of what I should do in each city, and list the exact flights I need to book to make the trip happen."
    )

@mcp.prompt()
def customer_support_cancellation_prompt(booking_id: str) -> str:
    """
    Customer support agent persona for handling refund policies.
    """
    return (
        f"A customer wants to cancel their booking with ID: '{booking_id}'. "
        "1. First, use `list_bookings` to find this booking and the flight date. "
        "2. Our airline policy states: Flights can only be cancelled for a full refund if the cancellation is requested more than 14 days before the flight date. Otherwise, there is a 50% penalty fee. "
        "Please calculate if they are eligible for a full refund based on today's date, and write a polite customer service response explaining their options."
    )

@mcp.prompt()
def flight_with_baggage_prompt(origin: str = "London", destination: str = "Barcelona") -> str:
    """
    Combined prompt: search for a flight AND retrieve the baggage policy for the airline in one shot.
    Demonstrates chaining a Tool (search_flights) with a Resource (policies://company).
    """
    return (
        f"I want to fly from {origin} to {destination}. "
        "Please do the following in order:\n"
        "1. Use the `search_flights` tool to find the available flights on the soonest available date.\n"
        "2. Pick the cheapest flight from the results and note the airline name.\n"
        "3. Use the `get_company_policies` tool to read the full baggage policy document.\n"
        "4. From that policy document, extract and show me ONLY the baggage rules for the airline you found in step 2.\n"
        "5. Give me a final summary: the flight details (price, times, seats) AND the baggage allowance for that airline side by side."
    )

@mcp.prompt()
def booking_confirmation_email_prompt(booking_id: str) -> str:
    """
    Generate a professional booking confirmation email for a completed flight reservation.
    """
    return (
        f"The user has just booked a flight and the booking ID is: '{booking_id}'.\n"
        "Please generate a complete, professional confirmation email to send to the passenger.\n\n"
        "Instructions:\n"
        "1. Use the `list_bookings` tool to retrieve the exact details of this booking ID (passenger name, flight date, times, origin, destination, etc.). Wait, `list_bookings` might not return a single booking easily, so carefully read the response to find the correct one.\n"
        "2. Look up the airline the passenger is flying with in the booking details.\n"
        "3. Use the `get_company_policies` resource to read the luggage and pet policy for that specific airline.\n"
        "4. Use the `get_airports_info` resource to find terminal and transit information for their destination city.\n"
        "5. Draft an HTML-styled or rich Markdown email that includes:\n"
        "   - A warm, professional greeting and a note of thanks.\n"
        "   - The flight itinerary (Origin, Destination, Date, Departure/Arrival times).\n"
        "   - A summary of the luggage policy they need to be aware of.\n"
        "   - Helpful transit instructions for when they land at their destination airport.\n"
        "   - A reminder of the cancellation policy.\n"
    )


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    use_sse = "--sse" in sys.argv

    if use_sse:
        print(f"Starting {SERVICE_NAME} in SSE mode on port {PORT}", file=sys.stderr)
        print(f"MCP Inspector SSE URL: http://localhost:{PORT}/sse", file=sys.stderr)
        mcp.run(transport="sse")
    else:
        # stdio transport — MCP Inspector spawns this process directly
        mcp.run(transport="stdio")
