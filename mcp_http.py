"""
MCP-only ASGI app: serves the MCP Streamable HTTP endpoint at the service root ("/").

Use this when you want a dedicated Cloud Run service whose base URL is your MCP endpoint
without a "/mcp" prefix. The main combined app remains in main.py.

Run with uvicorn, e.g.:
  uvicorn mcp_http:app --host 0.0.0.0 --port ${PORT:-8080}
"""

from mcp_server import mcp
from starlette.responses import FileResponse, JSONResponse
import os

# Ensure the HTTP transport expects the handshake at "/" (trailing slash supported).
try:
    mcp.settings.streamable_http_path = "/"
except Exception:
    pass

# Build the ASGI sub-application that implements the MCP Streamable HTTP transport.
app = mcp.streamable_http_app()

# Lightweight /privacy route when this app is deployed standalone
async def privacy(request):  # type: ignore[override]
  path = "static/privacy-mcp.html"
  if os.path.exists(path):
    return FileResponse(path, media_type="text/html")
  return JSONResponse({"title": "Privacy Policy", "detail": "See docs/PRIVACY_MCP.md"})

try:
  app.add_route("/privacy", privacy, methods=["GET"])  # type: ignore[attr-defined]
except Exception:
  # If add_route isn't available, ignore; privacy page is optional
  pass
