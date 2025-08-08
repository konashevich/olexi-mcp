# austlii_scraper.py (Final Production Version)

import requests
from bs4 import BeautifulSoup
from typing import List
from models import SearchResultItem

BASE_URL = "https://www.austlii.edu.au/cgi-bin/sinosrch.cgi"

def search_austlii(query: str, databases: List[str]) -> List[SearchResultItem]:
    """
    Performs a search on AustLII by sending a GET request with the necessary
    browser headers and parses the results based on the confirmed HTML structure.
    """
    
    params = [
        ("query", query),
        ("method", "boolean"),
        ("meta", "/au")
    ]
    for db_code in databases:
        params.append(("mask_path", db_code))

    headers = {
        "Referer": "https://www.austlii.edu.au/forms/search1.html",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }

    print(f"Constructing request to AustLII with params: {params}")

    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        print(f"AustLII response status code: {response.status_code}")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from AustLII: {e}")
        return []

    with open("debug_austlii_page.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    results: List[SearchResultItem] = []
    
    # --- FINAL CORRECTED PARSING LOGIC BASED ON YOUR SCREENSHOT ---
    # 1. Find the specific container for the search results.
    results_container = soup.find('div', class_='card')
    
    if not results_container:
        print("Could not find results container (<div class='card'>). Scraper needs update.")
        return []

    # 2. Now, find all the result list items *within* that container.
    list_items = results_container.find_all('li', class_='multi')

    if not list_items:
        print("Could not find any list items (<li class='multi'>) within the card container.")
        return []

    for item in list_items:
        title_tag = item.find('a')
        
        if title_tag and title_tag.has_attr('href'):
            title = title_tag.get_text(strip=True)
            full_url = requests.compat.urljoin("https://www.austlii.edu.au", title_tag['href'])
            
            # Extract relevance from the span with class 'right'
            relevance_tag = item.find('span', class_='right')
            metadata = relevance_tag.get_text(strip=True) if relevance_tag else "Relevance not found"

            results.append(SearchResultItem(
                title=title,
                url=full_url,
                metadata=metadata
            ))

    return results