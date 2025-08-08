# austlii_scraper.py (Final Version)

import requests
from bs4 import BeautifulSoup
from typing import List
from models import SearchResultItem

# The one true endpoint, as confirmed by network inspection.
BASE_URL = "https://www.austlii.edu.au/cgi-bin/sinosrch.cgi"

def search_austlii(query: str, databases: List[str]) -> List[SearchResultItem]:
    """
    Performs a search on AustLII by sending a GET request with the necessary
    browser headers to mimic a legitimate form submission.
    """
    
    # --- Correct URL Parameters ---
    params = [
        ("query", query),
        ("method", "boolean"), # Using boolean is more predictable than auto
        ("meta", "/au")
    ]
    for db_code in databases:
        params.append(("mask_path", db_code))

    # --- THE CRITICAL FIX: MIMIC BROWSER HEADERS ---
    # These headers make our request look like it's coming from a real browser.
    headers = {
        "Referer": "https://www.austlii.edu.au/forms/search1.html", # Say we came from the search form
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }

    print(f"Constructing request to AustLII with params: {params}")
    print(f"Sending with headers: {headers}")

    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        print(f"AustLII response status code: {response.status_code}")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from AustLII: {e}")
        return []

    # Save the HTML for debugging
    with open("debug_austlii_page.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    results: List[SearchResultItem] = []
    
    # --- HTML PARSING LOGIC ---
    # This might still need adjustment based on the contents of 'debug_austlii_page.html'
    # The 'multi' class was observed on older result pages and is a good starting point.
    list_items = soup.find_all('li', class_='multi')
    if not list_items:
        # Fallback if 'multi' class is not found. Let's try to find any list item in the main content.
        page_main = soup.find('div', id='page-main')
        if page_main:
            list_items = page_main.find_all('li')
    
    if not list_items:
        print("Could not find any list items ('li') in the page's main content. Please inspect 'debug_austlii_page.html' to find the correct result selectors.")
        return []

    for item in list_items:
        title_tag = item.find('a')
        
        if title_tag and title_tag.has_attr('href'):
            title = title_tag.get_text(strip=True)
            # Ensure the URL is absolute
            full_url = requests.compat.urljoin("https://www.austlii.edu.au", title_tag['href'])
            
            meta_tag = item.find('p', class_='meta') # The <p> tag containing metadata
            metadata = meta_tag.get_text(strip=True, separator=' | ') if meta_tag else "No metadata found"
            
            # The relevance score is often in a span with class 'right'
            relevance_tag = item.find('span', class_='right')
            if relevance_tag:
                 metadata += f" | {relevance_tag.get_text(strip=True)}"

            results.append(SearchResultItem(
                title=title,
                url=full_url,
                metadata=metadata
            ))

    return results