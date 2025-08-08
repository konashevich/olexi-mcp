# austlii_scraper.py

import requests
from bs4 import BeautifulSoup
from typing import List
from models import SearchResultItem

BASE_URL = "https://www.austlii.edu.au/search/"

def search_austlii(query: str, databases: List[str]) -> List[SearchResultItem]:
    """
    Performs a search on AustLII and scrapes the results.

    Args:
        query: The search term (e.g., 'negligence AND "civil liability"').
        databases: A list of AustLII database codes (e.g., ['AU_CTH_CASES']).

    Returns:
        A list of structured search result items.
    """
    params = {
        "search-term": query,
        "databases": databases
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
    except requests.RequestException as e:
        print(f"Error fetching data from AustLII: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    results: List[SearchResultItem] = []

    # Find the list that contains all the search results.
    # From inspecting the AustLII page, results are in a <ul> with class 'search-results-list'
    result_list = soup.find('ul', class_='search-results-list')
    if not result_list:
        print("Could not find search results list in the page.")
        return []

    # Each result is an <li> within this list
    for item in result_list.find_all('li', class_='search-result'):
        title_tag = item.find('a', class_='search-result-title')
        
        if title_tag and title_tag.has_attr('href'):
            title = title_tag.get_text(strip=True)
            # AustLII uses relative URLs, so we need to join them with the base domain
            full_url = requests.compat.urljoin("https://www.austlii.edu.au", title_tag['href'])
            
            # Find the metadata, e.g., relevance score
            meta_tag = item.find('div', class_='search-result-meta')
            metadata = meta_tag.get_text(strip=True) if meta_tag else "No metadata found"
            
            results.append(SearchResultItem(
                title=title,
                url=full_url,
                metadata=metadata
            ))

    return results