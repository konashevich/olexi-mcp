from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest, ChatResponse

# --- App Initialization ---
app = FastAPI(
    title="Olexi AI Server",
    description="Backend server for the Olexi AI browser extension.",
    version="1.0.0",
)

# --- CORS Configuration ---
# This is crucial to allow the browser extension (on a different domain)
# to make requests to this API.
# In production, you should restrict origins to the specific domain of your extension.
origins = [
    "*" # For development, allow all origins.
    # "chrome-extension://<your-extension-id>", # Example for production
    # "https://www.austlii.edu.au", # If the extension injects scripts
]

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
    The main endpoint to handle chat requests from the Olexi AI extension.
    
    This endpoint will eventually contain the full 5-phase logic:
    1.  Analyze & Strategize (MCP Call #1)
    2.  Execute & Scrape (Call to AustLII)
    3.  Synthesize & Formulate (MCP Call #2)
    """
    print(f"Received prompt: {request.prompt}")
    
    # --- !! PLACEHOLDER LOGIC !! ---
    # This is where the real work will happen. For now, we return a mocked response.
    # This allows the front-end to be developed against a working API.
    
    mocked_ai_answer = (
        f"This is a placeholder response for your query: **'{request.prompt}'**. "
        "The real AI logic has not been implemented yet.\n\n"
        "However, this confirms that the connection between the browser extension "
        "and the FastAPI backend is working correctly."
    )
    
    mocked_search_url = "https://www.austlii.edu.au/search/"

    return ChatResponse(
        ai_response=mocked_ai_answer,
        search_results_url=mocked_search_url
    )