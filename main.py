# main.py (Final Production Version)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest, ChatResponse
from austlii_scraper import search_austlii
from mcp_handler import generate_search_plan, summarize_results
from database_map import DATABASE_TOOLS_LIST
import urllib.parse # To help build the final search URL

# --- App Initialization ---
app = FastAPI(
    title="Olexi AI Server",
    description="Backend server for the Olexi AI browser extension.",
    version="1.0.0",
)

# --- CORS Configuration ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.get("/", tags=["Health Check"])
async def read_root():
    """A simple health check endpoint to confirm the server is running."""
    return {"status": "Olexi AI server is running"}

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
    scraped_results_dicts = [item.model_dump() for item in scraped_results]

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