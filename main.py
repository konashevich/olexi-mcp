# main.py (Final Production Version)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import ChatRequest, ChatResponse
from austlii_scraper import search_austlii
from mcp_handler import generate_search_plan, summarize_results
from database_map import DATABASE_TOOLS_LIST
import urllib.parse # To help build the final search URL
import os

# --- App Initialization ---
app = FastAPI(
    title="Olexi AI Server",
    description="Backend server for the Olexi AI browser extension.",
    version="1.0.0",
)

# --- Static Files Configuration ---
# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- CORS Configuration ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Favicon Endpoints ---
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve the main favicon.ico file."""
    favicon_path = "static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"message": "Favicon not found"}

@app.get("/favicon-16x16.png", include_in_schema=False)
async def favicon_16():
    """Serve the 16x16 PNG favicon."""
    favicon_path = "static/favicon-16x16.png"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"message": "Favicon not found"}

@app.get("/favicon-32x32.png", include_in_schema=False)
async def favicon_32():
    """Serve the 32x32 PNG favicon."""
    favicon_path = "static/favicon-32x32.png"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"message": "Favicon not found"}

@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon():
    """Serve the Apple touch icon."""
    icon_path = "static/apple-touch-icon.png"
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    return {"message": "Apple touch icon not found"}

@app.get("/site.webmanifest", include_in_schema=False)
async def web_manifest():
    """Serve the web app manifest."""
    manifest_path = "static/site.webmanifest"
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")
    return {"message": "Web manifest not found"}

# --- API Endpoints ---
@app.get("/", tags=["Health Check"], include_in_schema=False)
async def read_root():
    """Serve the main landing page with Olexi branding."""
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"status": "Olexi AI server is running", "port": 3000, "databases": len(DATABASE_TOOLS_LIST)}

@app.get("/status", tags=["Health Check"])
async def get_status():
    """JSON status endpoint for programmatic access."""
    return {"status": "Olexi AI server is running", "port": 3000, "databases": len(DATABASE_TOOLS_LIST)}

@app.post("/api/olexi-chat", response_model=ChatResponse, tags=["AI Chat"])
async def handle_chat_request(request: ChatRequest):
    """
    The main endpoint that orchestrates the full AI-driven search and summary process.
    """
    print(f"Received prompt: {request.prompt}")

    # --- Phase 2: Analyze & Strategize (MCP Call #1) ---
    try:
        search_plan = generate_search_plan(request.prompt, DATABASE_TOOLS_LIST)
        query_to_search = search_plan.get("query", request.prompt)
        databases_to_search = search_plan.get("databases", [])
    except Exception as e:
        print(f"Error generating search plan: {e}")
        # Fallback in case of AI error: search the prompt text in all cases.
        query_to_search = request.prompt
        databases_to_search = ["au/cases"]

    # --- Phase 3: Execute & Scrape ---
    scraped_results = search_austlii(query_to_search, databases_to_search)

    # Convert Pydantic models to simple dicts for the AI to process
    # Manually convert to ensure all URLs are strings
    scraped_results_dicts = []
    for item in scraped_results:
        scraped_results_dicts.append({
            "title": item.title,
            "url": str(item.url),  # Force conversion to string
            "metadata": item.metadata
        })

    # --- Phase 4: Synthesize & Formulate (MCP Call #2) ---
    try:
        ai_summary = summarize_results(request.prompt, scraped_results_dicts)
    except Exception as e:
        print(f"Error summarizing results: {e}")
        ai_summary = "I found some data but encountered an error while trying to summarize it."
    
    # --- Phase 5: Deliver (Construct the final search URL) ---
    # We can now dynamically build the real search URL for the user to click.
    params = [
        ("query", query_to_search),
        ("method", "boolean"),
        ("meta", "/au")
    ]
    for db_code in databases_to_search:
        params.append(("mask_path", db_code))
    
    final_search_url = f"https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?{urllib.parse.urlencode(params)}"

    return ChatResponse(
        ai_response=ai_summary,
        search_results_url=final_search_url
    )