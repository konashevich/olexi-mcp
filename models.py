# models.py

from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Union

class ChatRequest(BaseModel):
    prompt: str
    context_url: Optional[HttpUrl] = None

class SearchResultItem(BaseModel):
    """
    Defines the structure for a single search result item scraped from AustLII.
    """
    title: str
    url: Union[HttpUrl, str]  # Accept both HttpUrl and string
    metadata: Optional[str] = None # e.g., "Relevance: 100%"

class ChatResponse(BaseModel):
    ai_response: str
    search_results_url: Optional[Union[HttpUrl, str]] = None  # Accept both types
    # We will add the scraped data to our response later for debugging
    # scraped_data: List[SearchResultItem] = []