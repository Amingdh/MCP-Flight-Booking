#!/usr/bin/env python3
"""
MCP Flight Booking — Demo Client
=================================
Demonstrates end-to-end MCP host/client interaction:
  1. Fetch the tool manifest from the MCP server
  2. Call search_flights("Paris", "Rome", "2026-04-01")
  3. Select the cheapest flight
  4. Call book_flight for that flight
  5. Call list_bookings to confirm the reservation
  6. Print all results with pretty formatting

Usage:
    python demo_client.py [--base-url http://localhost:8000] [--api-key DEMO_KEY]
"""

import argparse
import json
import sys
import httpx

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_KEY = "DEMO_KEY"


def make_headers(api_key: str) -> dict:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


def banner(title: str) -> None:
    width = 60
    print("\n" + "═" * width)
    print(f"  {title}")
    print("═" * width)


def pretty(data: dict) -> None:
    print(json.dumps(data, indent=2))


# ── Step helpers ─────────────────────────────────────────────────────────────

def fetch_tool_manifest(client: httpx.Client, base_url: str) -> dict:
    banner("STEP 0 — Fetch MCP Tool Manifest")
    resp = client.get(f"{base_url}/tools")
    resp.raise_for_status()
    manifest = resp.json()
    print(f"  ✅  {len(manifest['tools'])} tools registered on this MCP server:\n")
    for tool in manifest["tools"]:
        print(f"    • {tool['name']:20s}  [{tool['method']}]  {tool['endpoint']}")
    return manifest


def search_flights(
    client: httpx.Client, base_url: str, origin: str, destination: str, date: str
) -> list[dict]:
    banner(f"STEP 1 — search_flights({origin!r}, {destination!r}, {date!r})")
    payload = {"origin": origin, "destination": destination, "date": date}
    resp = client.post(f"{base_url}/tools/searchFlights", json=payload)
    resp.raise_for_status()
    data = resp.json()
    print(f"  ✅  {data['total_found']} flight(s) found:\n")
    for f in data["results"]:
        print(
            f"    [{f['id']}]  {f['airline']:12s}  "
            f"{f['departure_time']} → {f['arrival_time']}  "
            f"€{f['price']:.2f}  ({f['seats_available']} seats)"
        )
    return data["results"]


def book_flight(
    client: httpx.Client, base_url: str, flight_id: str, passenger_name: str
) -> dict:
    banner(f"STEP 2 — book_flight({flight_id!r}, {passenger_name!r})")
    payload = {"flight_id": flight_id, "passenger_name": passenger_name}
    resp = client.post(f"{base_url}/tools/bookFlight", json=payload)
    resp.raise_for_status()
    data = resp.json()
    booking = data["booking"]
    print(f"  ✅  {data['message']}")
    print(f"\n  Booking ID  : {booking['booking_id']}")
    print(f"  Passenger   : {booking['passenger_name']}")
    print(f"  Flight      : {booking['flight_id']}")
    print(f"  Status      : {booking['status']}")
    print(f"  Booked at   : {booking['booked_at']}")
    return booking


def list_bookings(client: httpx.Client, base_url: str) -> list[dict]:
    banner("STEP 3 — list_bookings()")
    resp = client.get(f"{base_url}/tools/listBookings")
    resp.raise_for_status()
    data = resp.json()
    print(f"  ✅  {data['total']} booking(s) on record:\n")
    for b in data["bookings"]:
        print(
            f"    [{b['booking_id']}]  {b['passenger_name']:20s}  "
            f"{b['origin']} → {b['destination']}  {b['date']}  "
            f"{b['airline']:12s}  €{b['price']:.2f}  [{b['status']}]"
        )
    return data["bookings"]


# ── Main flow ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MCP Flight Booking Demo Client")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="MCP server base URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key for authentication")
    args = parser.parse_args()

    headers = make_headers(args.api_key)

    print("\n🛫  MCP Flight Booking — Demo Client")
    print(f"    Server : {args.base_url}")
    print(f"    Key    : {args.api_key[:4]}{'*' * (len(args.api_key) - 4)}")

    with httpx.Client(headers=headers, timeout=10.0) as client:
        # 0. Discover tools
        fetch_tool_manifest(client, args.base_url)

        # 1. Search flights
        flights = search_flights(client, args.base_url, "Paris", "Rome", "2026-04-01")

        if not flights:
            print("\n  ❌  No flights found. Exiting.")
            sys.exit(1)

        # 2. Pick the cheapest flight
        cheapest = min(flights, key=lambda f: f["price"])
        print(f"\n  ℹ️   Selecting cheapest flight: [{cheapest['id']}] €{cheapest['price']:.2f}")

        # 3. Book it
        booking = book_flight(client, args.base_url, cheapest["id"], "Alice Dupont")

        # 4. Confirm by listing all bookings
        list_bookings(client, args.base_url)

    print("\n✅  Demo completed successfully!\n")


if __name__ == "__main__":
    main()
