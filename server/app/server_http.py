"""
HTTP REST server entrypoint — used by Docker and the demo client.
Runs the FastAPI app that exposes /tools/* REST endpoints on port 8000.
"""
import uvicorn
import os
import sys

# Ensure the server root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from app.config import get_settings
from app.middleware.auth import APIKeyMiddleware
from app.tools.search_flights import router as search_flights_router
from app.tools.book_flight import router as book_flight_router
from app.tools.list_bookings import router as list_bookings_router
from app.tools.cancel_booking import router as cancel_booking_router

from app.main import mcp

settings = get_settings()

app = FastAPI(
    title=settings.service_name,
    description="MCP Flight Booking REST Server (for demo client & Docker)",
    version="1.0.0",
)

app.add_middleware(APIKeyMiddleware)

app.include_router(search_flights_router, prefix="/tools", tags=["MCP Tools"])
app.include_router(book_flight_router,    prefix="/tools", tags=["MCP Tools"])
app.include_router(list_bookings_router,  prefix="/tools", tags=["MCP Tools"])
app.include_router(cancel_booking_router, prefix="/tools", tags=["MCP Tools"])


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.get("/tools", tags=["MCP Discovery"])
def get_tools_manifest():
    """Returns the tool manifest listing available MCP capabilities."""
    return {
        "tools": [
            {
                "name": "search_flights",
                "method": "POST",
                "endpoint": "/tools/searchFlights",
                "description": "Search for available flights based on origin, destination and date.",
            },
            {
                "name": "book_flight",
                "method": "POST",
                "endpoint": "/tools/bookFlight",
                "description": "Book a ticket on a flight using its ID and passenger name.",
            },
            {
                "name": "list_bookings",
                "method": "GET",
                "endpoint": "/tools/listBookings",
                "description": "Retrieve a list of all existing bookings.",
            },
            {
                "name": "get_flights_catalog",
                "method": "GET",
                "endpoint": "/resources/flights",
                "description": "Retrieve the full raw catalog of all available flights and dates.",
            },
            {
                "name": "get_company_policies",
                "method": "GET",
                "endpoint": "/resources/policies",
                "description": "Read the full markdown document containing airline luggage, cancellation fees, and pet policies.",
            },
            {
                "name": "get_airports_info",
                "method": "GET",
                "endpoint": "/resources/airports",
                "description": "Read JSON document with detailed airport, terminal, lounge, and transit info for cities.",
            },
            {
                "name": "cancel_booking",
                "method": "POST",
                "endpoint": "/tools/cancelBooking",
                "description": "Cancel a confirmed flight booking by its booking ID. Sets status to CANCELLED.",
            }
        ]
    }


@app.get("/resources/flights", tags=["MCP Resources"])
def get_flights_resource():
    from app.main import _load_flights
    return {"flights": _load_flights()}


@app.get("/resources/bookings", tags=["MCP Resources"])
def get_bookings_resource():
    from app.main import _load_bookings
    return {"bookings": _load_bookings()}

@app.get("/resources/policies", tags=["MCP Resources"])
def get_policies_resource():
    from app.main import get_company_policies
    return {"policies_md": get_company_policies()}

@app.get("/resources/airports", tags=["MCP Resources"])
def get_airports_resource():
    from app.main import get_airports_info
    import json
    return {"airports": json.loads(get_airports_info())}


if __name__ == "__main__":
    uvicorn.run(
        "app.server_http:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
    )
