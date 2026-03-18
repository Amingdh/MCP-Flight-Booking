# Setup Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.11 | [python.org](https://python.org) |
| uv | latest | see below |
| Docker | ≥ 24 | [docker.com](https://docker.com) |
| docker-compose | ≥ 2 | bundled with Docker Desktop |

---

## 1. Install `uv`

`uv` is a fast Python package manager written in Rust.

### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Via pip (fallback)
```bash
pip install uv
```

Verify installation:
```bash
uv --version
```

---

## 2. Clone / unzip the project

```bash
# If cloned from git:
git clone <repo-url> mcp-flight-booking-poc
cd mcp-flight-booking-poc
```

---

## 3. Configure environment

```bash
cd server
cp .env.example .env
# Edit .env if you want to change PORT or API_KEY
```

Default values:
```
PORT=8000
API_KEY=DEMO_KEY
SERVICE_NAME=flight-mcp-server
DATA_DIR=data
```

---

## 4. Install server dependencies

```bash
cd server
uv venv          # creates .venv/
uv pip install -e .
```

---

## 5. Install client dependencies

```bash
cd client
uv venv
uv pip install httpx
```

---

## 6. Run the server locally

```bash
cd server
uv run uvicorn app.main:app --reload --port 8000
```

The server will start at **http://localhost:8000**.

Open the Swagger UI at: http://localhost:8000/docs

---

## Project Structure

```
mcp-flight-booking-poc/
├── server/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point + tool manifest
│   │   ├── config.py            # pydantic-settings config loader
│   │   ├── middleware/
│   │   │   └── auth.py          # API key middleware
│   │   └── tools/
│   │       ├── search_flights.py
│   │       ├── book_flight.py
│   │       └── list_bookings.py
│   ├── data/
│   │   └── flights.json         # Mock flight data
│   ├── pyproject.toml
│   └── .env.example
├── client/
│   └── demo_client.py           # End-to-end demo script
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── docs/
    ├── setup.md
    ├── deployment.md
    └── usage.md
```
