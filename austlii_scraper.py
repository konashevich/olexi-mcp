# austlii_scraper.py (Final Production Version)

import time
import random
import os
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import List, Tuple, Optional
from urllib.parse import urljoin
from models import SearchResultItem

BASE_URL = "https://www.austlii.edu.au/cgi-bin/sinosrch.cgi"
HOME_URL = "https://www.austlii.edu.au/"


class AustliiUnavailableError(Exception):
    """Raised when AustLII is unreachable or returns an error consistently."""
    pass


def check_austlii_health(timeout: int = 5) -> Tuple[bool, int, str]:
    """
    Lightweight health check against AustLII homepage.
    Returns (ok, status_code, error_message)
    """
    headers = {
        "Referer": "https://www.austlii.edu.au/forms/search1.html",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    }
    try:
        resp = requests.get(HOME_URL, headers=headers, timeout=timeout)
        return (200 <= resp.status_code < 400, resp.status_code, "")
    except requests.RequestException as e:
        return (False, 0, str(e))

def search_austlii(query: str, databases: List[str], method: str = "boolean") -> List[SearchResultItem]:
    """
    Performs a search on AustLII by sending a GET request with the necessary
    browser headers and parses the results based on the confirmed HTML structure.
    """
    
    method = method if method in {"boolean", "auto", "title"} else "boolean"
    params = [
        ("query", query),
        ("method", method),
        ("meta", "/au")
    ]
    for db_code in databases:
        params.append(("mask_path", db_code))

    headers = {
        "Referer": "https://www.austlii.edu.au/forms/search1.html",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }

    print(f"Constructing request to AustLII with params: {params}")

    # Simple retry with small backoff for transient blips (configurable)
    last_err: Optional[Exception] = None
    response: Optional[requests.Response] = None
    retries = int(os.getenv("AUSTLII_RETRIES", "3"))
    # Allow separate connect/read timeouts; fall back to a single AUSTLII_TIMEOUT if provided
    connect_timeout = float(os.getenv("AUSTLII_CONNECT_TIMEOUT", os.getenv("AUSTLII_TIMEOUT", "20")))
    read_timeout = float(os.getenv("AUSTLII_READ_TIMEOUT", os.getenv("AUSTLII_TIMEOUT", "20")))
    backoff = float(os.getenv("AUSTLII_BACKOFF", "1.5"))
    jitter = float(os.getenv("AUSTLII_JITTER", "0.3"))  # proportion, e.g., 0.3 => ±30%
    for attempt in range(max(1, retries)):
        try:
            # Separate connect/read timeouts to better handle connect stalls
            response = requests.get(BASE_URL, params=params, headers=headers, timeout=(connect_timeout, read_timeout))
            print(f"AustLII response status code: {response.status_code}")
            response.raise_for_status()
            break
        except requests.RequestException as e:
            last_err = e
            print(f"Error fetching data from AustLII (attempt {attempt+1}): {e}")
            if attempt < max(1, retries) - 1:
                # brief backoff with jitter to avoid thundering herd
                factor = 1.0 + random.uniform(-jitter, jitter) if jitter > 0 else 1.0
                time.sleep(max(0.1, backoff * factor))
            else:
                raise AustliiUnavailableError(str(e))

    if response is None:
        # Should not happen due to raise above, but keep guard
        raise AustliiUnavailableError(str(last_err) if last_err else "Unknown AustLII error")

    # Debug output disabled
    # To re-enable debug output, uncomment the following lines:
    # with open("debug_austlii_page.html", "w", encoding="utf-8") as f:
    #     f.write(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    results: List[SearchResultItem] = []
    
    # --- FINAL CORRECTED PARSING LOGIC BASED ON YOUR SCREENSHOT ---
    # 1. Find the specific container for the search results.
    results_container: Optional[Tag] = soup.find('div', attrs={'class': 'card'})  # type: ignore[assignment]
    
    if not results_container:
        print("Could not find results container (<div class='card'>). Scraper needs update.")
        return []

    # 2. Now, find all the result list items *within* that container.
    list_items = results_container.find_all('li', attrs={'class': 'multi'})

    if not list_items:
        print("Could not find any list items (<li class='multi'>) within the card container.")
        return []

    for item in list_items:
        title_tag: Optional[Tag] = item.find('a')  # type: ignore[assignment]
        
        href_val = title_tag.get('href') if title_tag else None
        if title_tag and isinstance(href_val, str):
            title = title_tag.get_text(strip=True)
            full_url = urljoin("https://www.austlii.edu.au", href_val)
            
            # Extract relevance from the span with class 'right'
            relevance_tag: Optional[Tag] = item.find('span', attrs={'class': 'right'})  # type: ignore[assignment]
            metadata = relevance_tag.get_text(strip=True) if isinstance(relevance_tag, Tag) else "Relevance not found"

            results.append(SearchResultItem(
                title=title,
                url=full_url,
                metadata=metadata
            ))

    return results