#!/usr/bin/env python3
"""
Test script to validate AustLII database codes
"""

import requests
from bs4 import BeautifulSoup
import sys

def test_database_code(db_code, query="contract"):
    """Test if a database code returns results"""
    url = "https://www.austlii.edu.au/cgi-bin/sinosrch.cgi"
    
    params = [
        ("query", query),
        ("method", "auto"),
        ("meta", "/au"),
        ("mask_path", db_code)
    ]
    
    headers = {
        "Referer": "https://www.austlii.edu.au/forms/search1.html",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"Testing database code: {db_code}")
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if "0 documents found" in response.text:
            print(f"  ❌ No results found for {db_code}")
            return False
        elif "documents found" in response.text:
            # Extract number of documents
            import re
            match = re.search(r'(\d+)\s+documents found', response.text)
            if match:
                count = match.group(1)
                print(f"  ✅ Found {count} documents for {db_code}")
                return True
        else:
            print(f"  ⚠️  Unclear result for {db_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing {db_code}: {e}")
        return False

if __name__ == "__main__":
    # Test different database codes
    test_codes = [
        "au/cases/cth/HCA",      # High Court
        "au/cases/cth/FCA",      # Federal Court  
        "au/cases/cth",          # All Cth cases
        "au/legis/cth/consol_act", # Cth legislation
        "AU_CTH_CASES",          # Old invalid code
        "",                      # No filter (all databases)
    ]
    
    print("Testing AustLII database codes with query 'contract':")
    print("=" * 50)
    
    for code in test_codes:
        test_database_code(code)
        print()
