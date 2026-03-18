# Usage Guide

## Authentication

All `/tools/*` endpoints require the `x-api-key` header.

```
x-api-key: DEMO_KEY
```

Requests without a valid key return `401 Unauthorized`.

---

## MCP Tool Manifest

Discover all available tools:

```bash
curl -H "x-api-key: DEMO_KEY" http://localhost:8000/tools
```

---

## Tool Reference

### `search_flights`

**POST** `/tools/searchFlights`

Search available flights by route and date.

**Request body:**
```json
{
  "origin": "Paris",
  "destination": "Rome",
  "date": "2026-04-01"
}
```

**Response:**
```json
{
  "tool": "search_flights",
  "query": { "origin": "Paris", "destination": "Rome", "date": "2026-04-01" },
  "results": [
    {
      "id": "FL001",
      "origin": "Paris",
      "destination": "Rome",
      "date": "2026-04-01",
      "departure_time": "08:30",
      "arrival_time": "10:45",
      "airline": "AirEurope",
      "price": 189.99,
      "seats_available": 12,
      "duration_minutes": 135
    }
  ],
  "total_found": 3
}
```

**curl example:**
```bash
curl -s -X POST http://localhost:8000/tools/searchFlights \
  -H "x-api-key: DEMO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"origin":"Paris","destination":"Rome","date":"2026-04-01"}' | python3 -m json.tool
```

---

### `book_flight`

**POST** `/tools/bookFlight`

Book a specific flight for a passenger.

**Request body:**
```json
{
  "flight_id": "FL002",
  "passenger_name": "Alice Dupont"
}
```

**Response:**
```json
{
  "tool": "book_flight",
  "success": true,
  "booking": {
    "booking_id": "BK3F9A1C2D",
    "flight_id": "FL002",
    "passenger_name": "Alice Dupont",
    "status": "CONFIRMED",
    "booked_at": "2026-03-11T10:00:00Z",
    "flight_details": { ... }
  },
  "message": "Flight FL002 successfully booked for Alice Dupont."
}
```

**curl example:**
```bash
curl -s -X POST http://localhost:8000/tools/bookFlight \
  -H "x-api-key: DEMO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"flight_id":"FL002","passenger_name":"Alice Dupont"}' | python3 -m json.tool
```

---

### `list_bookings`

**GET** `/tools/listBookings`

Returns all confirmed bookings.

**Response:**
```json
{
  "tool": "list_bookings",
  "bookings": [
    {
      "booking_id": "BK3F9A1C2D",
      "flight_id": "FL002",
      "passenger_name": "Alice Dupont",
      "status": "CONFIRMED",
      "booked_at": "2026-03-11T10:00:00Z",
      "origin": "Paris",
      "destination": "Rome",
      "date": "2026-04-01",
      "airline": "MedFly",
      "price": 145.50
    }
  ],
  "total": 1
}
```

**curl example:**
```bash
curl -s http://localhost:8000/tools/listBookings \
  -H "x-api-key: DEMO_KEY" | python3 -m json.tool
```

---

## Running the Demo Client

Make sure the server is running first (locally or via Docker).

### Local run:
```bash
cd client

# Install dependencies (one-time)
uv venv && uv pip install httpx

# Run the demo
uv run python demo_client.py
```

### With custom server URL or API key:
```bash
uv run python demo_client.py --base-url http://localhost:8000 --api-key DEMO_KEY
```

### Expected output:
```
🛫  MCP Flight Booking — Demo Client
    Server : http://localhost:8000
    Key    : DEMO****

════════════════════════════════════════════════════════════
  STEP 0 — Fetch MCP Tool Manifest
════════════════════════════════════════════════════════════
  ✅  3 tools registered on this MCP server:

    • search_flights         [POST]  /tools/searchFlights
    • book_flight            [POST]  /tools/bookFlight
    • list_bookings          [GET]   /tools/listBookings

════════════════════════════════════════════════════════════
  STEP 1 — search_flights('Paris', 'Rome', '2026-04-01')
════════════════════════════════════════════════════════════
  ✅  3 flight(s) found:

    [FL001]  AirEurope    08:30 → 10:45  €189.99  (12 seats)
    [FL002]  MedFly       13:15 → 15:30  €145.50  (4 seats)
    [FL003]  AirEurope    18:00 → 20:20  €210.00  (23 seats)

  ℹ️   Selecting cheapest flight: [FL002] €145.50

...
✅  Demo completed successfully!
```

---

## Interactive API Docs

Swagger UI is available at: **http://localhost:8000/docs**

All endpoints can be tested directly from the browser.
