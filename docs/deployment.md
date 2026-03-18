# Deployment Guide

## Docker Deployment (recommended)

### 1. Build and start

From the project root (`mcp-flight-booking-poc/`):

```bash
docker-compose -f docker/docker-compose.yml up --build
```

To run in the background:
```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

### 2. Verify health

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### 3. Stop

```bash
docker-compose -f docker/docker-compose.yml down
```

---

## Environment variable overrides

You can override environment variables at runtime without rebuilding:

```bash
API_KEY=MY_SECRET_KEY docker-compose -f docker/docker-compose.yml up
```

Or edit the `environment:` block in `docker/docker-compose.yml` directly.

---

## Volume / Persistence

The `flight_data` Docker volume persists `bookings.json` between container restarts.

```bash
# Inspect the volume
docker volume inspect mcp-flight-booking-poc_flight_data

# Remove all data (reset bookings)
docker-compose -f docker/docker-compose.yml down -v
```

---

## Production considerations

| Concern | Recommendation |
|---------|----------------|
| TLS | Put Nginx/Traefik in front; terminate SSL there |
| Auth | Replace the static API key with JWT or OAuth2 |
| Persistence | Swap `bookings.json` for PostgreSQL or Redis |
| Scaling | Run multiple replicas behind a load balancer; share a DB |
| Secrets | Use Docker secrets or a vault (never commit `.env`) |

---

## Manual Docker build (without Compose)

```bash
# Build the image
docker build -f docker/Dockerfile -t flight-mcp-server .

# Run the container
docker run -p 8000:8000 \
  -e API_KEY=DEMO_KEY \
  -e PORT=8000 \
  flight-mcp-server
```
