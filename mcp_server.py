# mcp_server.py
# Hybrid MCP server exposing Olexi AI legal research tools.
# Mountable under FastAPI for HTTP transport and runnable via stdio for development.
# 
# Part of the Olexi AI project: significantly lowering barriers to legal research
# on Australia's primary legal database (AustLII) through intelligent conversational
# interfaces and sophisticated web scraping of legacy CGI endpoints.

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
mcp = FastMCP("Olexi MCP Server")  # AI-powered legal research assistant for AustLII

# --- Resources ---
@mcp.resource("olexi://databases")
def list_databases_resource() -> str:
    """JSON of available AustLII database tools.
    
    Provides structured access to Australian legal database system for 
    programmatic database selection and intelligent query routing.
    """
    import json
    return json.dumps(DATABASE_TOOLS_LIST, indent=2)

# --- Tools ---
@mcp.tool(title="List Databases")
def list_databases() -> List[Dict]:
    """Get available Australian legal databases with their codes and descriptions.
    
    Returns database options for legal research across federal courts, state courts, 
    specialized tribunals, and legislation. Use this first to understand what 
    databases are available before searching.
    
    Returns:
        List of database objects with code, name, and description for each available
        legal database. Essential for determining search scope and database selection.
    """
    return DATABASE_TOOLS_LIST

@mcp.tool(title="Search AustLII")
def search_austlii(query: str, databases: List[str], method: str = "boolean") -> List[SearchResultItem]:
    """Search Australian legal databases for cases, legislation, and legal documents.
    
    Performs comprehensive legal research across selected database codes. Returns 
    detailed results with titles, URLs, and metadata for further research.
    
    Args:
        query: Legal search terms (supports boolean operators like AND, OR, NOT)
        databases: List of database codes from list_databases (e.g., ['au/cases/cth/HCA'])
    
    Returns:
        List of legal documents with title, URL, and metadata. Typically returns 
        hundreds to thousands of results for comprehensive legal research.
    
    Limitations:
        Dependent on external AustLII availability; large result sets may take time to retrieve.
    
    Best for: Case law research, statutory interpretation, legal precedent analysis,
    citation verification, and comprehensive legal document discovery.
    """
    results = scrape(query, databases, method=method)
    # Convert to primitive dicts then model to ensure str URLs
    output: List[SearchResultItem] = []
    for item in results:
        output.append(
            SearchResultItem(title=item.title, url=str(item.url), metadata=item.metadata)
        )
    return output

@mcp.tool(title="Build Search URL")
def build_search_url(query: str, databases: List[str]) -> str:
    """Generate a direct URL to AustLII search results.
    
    Takes the same query and databases as search_austlii but returns a web link 
    instead of parsed results. Use when users want to bookmark, share, or manually 
    browse the search results page. No network call is made by this tool.
    
    Args:
        query: Legal search terms (same format as search_austlii)
        databases: List of database codes to include in search scope
    
    Returns:
        Complete HTTPS URL to AustLII search results page for immediate browser access.
        
    Use when: Users need a shareable link, want to browse results manually, or 
    require direct access to the original search interface.
    """
    params = [("query", query), ("method", "boolean"), ("meta", "/au")]
    for db_code in databases:
        params.append(("mask_path", db_code))
    return f"https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?{urllib.parse.urlencode(params)}"

# --- Optional: progress example for long scrapes ---
@mcp.tool(title="Search with Progress")
async def search_with_progress(query: str, databases: List[str], ctx: Context, method: str = "boolean") -> List[SearchResultItem]:
    """Search Australian legal databases with real-time progress updates.
    
    Identical functionality to search_austlii but provides status updates during 
    execution. Use for large searches that may take significant time, when user 
    interface needs progress feedback.

    Args:
        query: Legal search terms (supports boolean operators like AND, OR, NOT)
        databases: List of database codes from list_databases
        ctx: MCP execution context for progress reporting

    Returns:
        List of legal documents with title, URL, and metadata. Same results as 
        search_austlii but with progress updates sent during processing.
    
    Limitations:
        Dependent on external AustLII availability; duration scales with result size and databases selected.
        
    Use when: Searching across many databases, expecting large result sets, or 
    when user interface requires progress indication for better user experience.
    """
    await ctx.info("Starting AustLII search...")
    await ctx.report_progress(0.3, total=1.0, message="Scraping")
    results = scrape(query, databases, method=method)
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

@mcp.custom_route("/info", methods=["GET"], include_in_schema=False)
async def mcp_info(request: Request):  # type: ignore[override]
    return JSONResponse({
        "message": "Olexi MCP Streamable HTTP endpoint",
        "health": "/mcp/health",
        "transport": "streamable-http",
        "hint": "Your MCP host should POST to /mcp for the protocol handshake."
    })

# Some MCP hosts may probe the base path with GET before starting the POST handshake.
# Provide a friendly JSON response on GET "/" to avoid 400s from the transport layer.
@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def mcp_root_get(request: Request):  # type: ignore[override]
    return JSONResponse({
        "status": "ok",
        "name": mcp.name,
        "transport": "streamable-http",
        "health": "/mcp/health",
        "info": "/mcp/info",
        "hint": "Use POST to /mcp/ for MCP session handshake; avoid redirects by including the trailing slash."
    })

# --- Entry point for stdio/CLI ---
if __name__ == "__main__":
    # Default to stdio for compatibility with most hosts; override via env/args if needed.
    mcp.run()  # stdio by default; can pass transport="streamable-http" for HTTP
