# mcp_server.py
# Hybrid MCP server exposing Olexi tools, mountable under FastAPI and runnable via stdio.

from typing import List, Dict, Optional
from pydantic import BaseModel, HttpUrl
from mcp.server.fastmcp import FastMCP, Context

from database_map import DATABASE_TOOLS_LIST
from austlii_scraper import search_austlii as scrape
from mcp_handler import generate_search_plan as plan, summarize_results as synth
import urllib.parse

# --- Pydantic models for structured output ---
class SearchPlan(BaseModel):
    query: str
    databases: List[str]

class SearchResultItem(BaseModel):
    title: str
    url: str
    metadata: Optional[str] = None

class Summary(BaseModel):
    markdown: str

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

@mcp.tool(title="Plan Search")
def plan_search(prompt: str) -> SearchPlan:
    """Generate a boolean query and database list for a prompt."""
    sp = plan(prompt, DATABASE_TOOLS_LIST)
    return SearchPlan(query=sp.get("query", prompt), databases=sp.get("databases", []))

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

@mcp.tool(title="Summarize Results")
def summarize_results(prompt: str, results: List[SearchResultItem]) -> Summary:
    """Summarize scraped results with citations using the LLM."""
    # Convert models to plain dicts for the LLM handler
    dicts = [{"title": r.title, "url": r.url, "metadata": r.metadata} for r in results]
    md = synth(prompt, dicts)
    return Summary(markdown=md)

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
    # We don't have stepwise scraping, so simulate coarse progress
    await ctx.report_progress(0.2, total=1.0, message="Planning")
    _ = plan(query, DATABASE_TOOLS_LIST)
    await ctx.report_progress(0.6, total=1.0, message="Scraping")
    results = scrape(query, databases)
    await ctx.report_progress(0.9, total=1.0, message="Packaging")
    out: List[SearchResultItem] = []
    for item in results:
        out.append(SearchResultItem(title=item.title, url=str(item.url), metadata=item.metadata))
    await ctx.report_progress(1.0, total=1.0, message="Done")
    return out

# --- Entry point for stdio/CLI ---
if __name__ == "__main__":
    # Default to stdio for compatibility with most hosts; override via env/args if needed.
    mcp.run()  # stdio by default; can pass transport="streamable-http" for HTTP
