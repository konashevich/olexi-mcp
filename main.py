# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest, ChatResponse
from austlii_scraper import search_austlii # <-- IMPORT OUR NEW FUNCTION

app = FastAPI(
    title="Olexi AI Server",
    description="Backend server for the Olexi AI browser extension.",
    version="1.0.0",
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "Olexi AI server is running"}

@app.post("/api/olexi-chat", response_model=ChatResponse, tags=["AI Chat"])
async def handle_chat_request(request: ChatRequest):
    print(f"Received prompt: {request.prompt}")

    # --- !! PHASE 2 & 3 INTEGRATION (PLACEHOLDER STRATEGY) !! ---
    # In the future, an LLM call will generate these parameters.
    # For now, we hardcode them to test the scraper.
    query_to_search = request.prompt
    databases_to_search = ["AU_CTH_CASES", "AU_NSW_LEGIS"]

    # Call our new scraper function
    scraped_results = search_austlii(query_to_search, databases_to_search)

    # --- !! PHASE 4 & 5 (PLACEHOLDER SYNTHESIS) !! ---
    # For now, we will just format the scraped results directly into the response.
    # Later, this data will be sent to the LLM for a proper summary.
    
    ai_summary = ""
    if not scraped_results:
        ai_summary = f"I couldn't find any documents on AustLII for '{query_to_search}'. Please try a different query."
    else:
        ai_summary = f"I found {len(scraped_results)} documents related to '{query_to_search}'. Here are the top 3:\n\n"
        for i, result in enumerate(scraped_results[:3]): # Show top 3
            ai_summary += f"{i+1}. **{result.title}**\n   - Metadata: *{result.metadata}*\n   - [Read More]({result.url})\n"

    # The final search URL is not easily available, so we'll mock it for now.
    mocked_search_url = "https://www.austlii.edu.au/search/"

    return ChatResponse(
        ai_response=ai_summary,
        search_results_url=mocked_search_url
    )