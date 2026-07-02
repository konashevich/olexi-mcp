# models.py

from pydantic import BaseModel, HttpUrl
from typing import Optional, Union

class SearchResultItem(BaseModel):
    """
    Defines the structure for a single search result item scraped from AustLII.
    """
    title: str
    url: Union[HttpUrl, str]  # Accept both HttpUrl and string
    metadata: Optional[str] = None # e.g., "Relevance: 100%"

## Legacy ChatResponse removed (non-MCP design). Use tools outputs instead.