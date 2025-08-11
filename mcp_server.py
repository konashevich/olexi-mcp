# mcp_server.py
# Hybrid MCP server exposing Olexi tools, mountable under FastAPI and runnable via stdio.

from typing import List, Dict, Optional
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP, Context

from database_map import DATABASE_TOOLS_LIST
from austlii_scraper import search_austlii as scrape
import urllib.parse
from starlette.responses import JSONResponse
from starlette.requests import Request

# --- Pydantic models for structured output ---
class SearchResultItem(BaseModel):
    title: str
    url: str
    metadata: Optional[str] = None

# --- Create FastMCP server instance ---
mcp = FastMCP("Olexi MCP Server")

# --- Resources ---
@mcp.resource("olexi://databases")
def list_databases_resource() -> str:
    """JSON of available AustLII database tools."""
    import json
    return json.dumps(DATABASE_TOOLS_LIST, indent=2)

# --- Tools ---
@mcp.tool(title="List Databases")
def list_databases() -> List[Dict]:
    """Return all available AustLII databases with codes and descriptions."""
    return DATABASE_TOOLS_LIST

@mcp.tool(title="Search AustLII")
def search_austlii(query: str, databases: List[str]) -> List[SearchResultItem]:
    """Execute AustLII search and return structured results."""
    results = scrape(query, databases)
    # Convert to primitive dicts then model to ensure str URLs
    output: List[SearchResultItem] = []
    for item in results:
        output.append(
            SearchResultItem(title=item.title, url=str(item.url), metadata=item.metadata)
        )
    return output

@mcp.tool(title="Build Search URL")
def build_search_url(query: str, databases: List[str]) -> str:
    """Return the final AustLII search URL for UX handoff."""
    params = [("query", query), ("method", "boolean"), ("meta", "/au")]
    for db_code in databases:
        params.append(("mask_path", db_code))
    return f"https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?{urllib.parse.urlencode(params)}"

# --- Optional: progress example for long scrapes ---
@mcp.tool(title="Search with Progress")
async def search_with_progress(query: str, databases: List[str], ctx: Context) -> List[SearchResultItem]:
    await ctx.info("Starting AustLII search...")
    await ctx.report_progress(0.3, total=1.0, message="Scraping")
    results = scrape(query, databases)
    await ctx.report_progress(0.9, total=1.0, message="Packaging")
    out: List[SearchResultItem] = []
    for item in results:
        out.append(SearchResultItem(title=item.title, url=str(item.url), metadata=item.metadata))
    await ctx.report_progress(1.0, total=1.0, message="Done")
    return out

# --- Minimal HTTP diagnostics for mounted /mcp ---
@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def mcp_health(request: Request):  # type: ignore[override]
    return JSONResponse({"status": "ok", "name": mcp.name, "transport": "streamable-http"})

@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def mcp_index(request: Request):  # type: ignore[override]
    return JSONResponse({
        "message": "Olexi MCP Streamable HTTP endpoint",
        "health": "/mcp/health",
        "note": "Use an MCP host (e.g., Continue) to connect to /mcp."
    })

# --- Entry point for stdio/CLI ---
if __name__ == "__main__":
    # Default to stdio for compatibility with most hosts; override via env/args if needed.
    mcp.run()  # stdio by default; can pass transport="streamable-http" for HTTP
