import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.config import get_settings, Settings

router = APIRouter()


class SearchFlightsRequest(BaseModel):
    origin: str
    destination: str
    date: str


class FlightResult(BaseModel):
    id: str
    origin: str
    destination: str
    date: str
    departure_time: str
    arrival_time: str
    airline: str
    price: float
    seats_available: int
    duration_minutes: int


class SearchFlightsResponse(BaseModel):
    tool: str = "search_flights"
    query: dict
    results: list[FlightResult]
    total_found: int


def load_flights(data_dir: str) -> list[dict]:
    flights_path = Path(data_dir) / "flights.json"
    with open(flights_path, "r") as f:
        data = json.load(f)
    return data["flights"]


@router.post("/searchFlights", response_model=SearchFlightsResponse)
def search_flights(
    payload: SearchFlightsRequest,
    settings: Settings = Depends(get_settings),
):
    """
    MCP Tool: search_flights
    Searches available flights by origin, destination, and date.
    """
    all_flights = load_flights(settings.data_dir)

    matched = [
        f
        for f in all_flights
        if f["origin"].lower() == payload.origin.lower()
        and f["destination"].lower() == payload.destination.lower()
        and f["date"] == payload.date
    ]

    return SearchFlightsResponse(
        query={
            "origin": payload.origin,
            "destination": payload.destination,
            "date": payload.date,
        },
        results=matched,
        total_found=len(matched),
    )
