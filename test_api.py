#!/usr/bin/env python3
# test_api.py - Quick API test script

import requests
import json
import time

API_URL = "http://127.0.0.1:3000/api/olexi-chat"

def test_api():
    print("Testing Olexi API...")
    
    # Test data
    test_payload = {
        "prompt": "test question about contracts",
        "context_url": "https://example.com"
    }
    
    try:
        print(f"Sending request to: {API_URL}")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(
            API_URL, 
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 second timeout
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS!")
            print(f"AI Response: {result.get('ai_response', 'No ai_response field')}")
            print(f"Search URL: {result.get('search_results_url', 'No search_results_url field')}")
        else:
            print("ERROR!")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 60 seconds")
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Could not connect to server: {e}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_api()
