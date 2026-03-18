import json
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings

# Paths that do NOT require authentication
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc", "/mcp/sse", "/mcp/messages"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Allow public paths through without auth
        if path in PUBLIC_PATHS or path.startswith("/mcp/"):
            return await call_next(request)

        settings = get_settings()
        api_key = request.headers.get("x-api-key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key. Provide 'x-api-key' header."},
            )

        if api_key != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key."},
            )

        return await call_next(request)
