from pydantic import BaseModel, HttpUrl
from typing import Optional

class ChatRequest(BaseModel):
    """
    Defines the structure of an incoming request from the browser extension.
    """
    prompt: str
    context_url: Optional[HttpUrl] = None # The URL the user is currently on

class ChatResponse(BaseModel):
    """
    Defines the structure of the response sent back to the extension.
    """
    ai_response: str
    search_results_url: Optional[HttpUrl] = None