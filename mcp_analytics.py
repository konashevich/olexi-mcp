"""
Structured HTTP analytics for the MCP Streamable HTTP app.

Logs JSON lines to stdout (Cloud Logging on Cloud Run). Filter in GCP with:
  jsonPayload.event="mcp_http_end"
  jsonPayload.mcp_session_id!=""
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MCP_SESSION_ID_HEADER = "mcp-session-id"
MCP_PROTOCOL_VERSION_HEADER = "mcp-protocol-version"

logger = logging.getLogger("olexi.mcp.analytics")


def _truthy_env(name: str, default: str = "true") -> bool:
    import os

    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def analytics_enabled() -> bool:
    return _truthy_env("MCP_ANALYTICS_ENABLED", "true")


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _request_fields(request: Request) -> dict[str, Any]:
    accept = request.headers.get("accept", "")
    return {
        "method": request.method,
        "path": request.url.path,
        "mcp_session_id": request.headers.get(MCP_SESSION_ID_HEADER),
        "mcp_protocol_version": request.headers.get(MCP_PROTOCOL_VERSION_HEADER),
        "client_ip": _client_ip(request),
        "user_agent": request.headers.get("user-agent"),
        "accept": accept[:120] if accept else None,
        "is_sse_accept": "text/event-stream" in accept,
    }


def log_request_event(
    phase: str,
    request: Request,
    *,
    status: Optional[int] = None,
    duration_ms: Optional[float] = None,
) -> None:
    if not analytics_enabled():
        return

    payload: dict[str, Any] = {
        "event": f"mcp_http_{phase}",
        "service": "olexi-mcp",
        **_request_fields(request),
    }
    if status is not None:
        payload["status"] = status
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 2)
        payload["is_keepalive"] = request.method == "GET" and duration_ms >= 300_000

    logger.info(json.dumps(payload, ensure_ascii=False))


class McpAnalyticsMiddleware:
    """ASGI middleware: log request start/end with MCP session id and timing."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not analytics_enabled():
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        start = time.perf_counter()
        status_code: Optional[int] = None

        log_request_event("start", request)

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            log_request_event("end", request, status=status_code, duration_ms=duration_ms)


def wrap_with_analytics(app: ASGIApp) -> ASGIApp:
    return McpAnalyticsMiddleware(app)
