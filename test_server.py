# test_server.py
import requests
import json

def test_server():
    """Test the Olexi server step by step"""
    
    # Test 1: Check if server is running
    print("🔍 Testing server connectivity...")
    try:
        response = requests.get("http://127.0.0.1:3000/status", timeout=5)
        print(f"✅ Server status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False
    
    # Test 2: Check API docs
    print("\n🔍 Testing API docs...")
    try:
        response = requests.get("http://127.0.0.1:3000/docs", timeout=5)
        print(f"✅ API docs: {response.status_code}")
    except Exception as e:
        print(f"❌ API docs not reachable: {e}")
    
    # Test 3: Test the main API endpoint
    print("\n🔍 Testing API endpoint...")
    try:
        test_payload = {
            "prompt": "test query",
            "context_url": "https://example.com"
        }
        response = requests.post(
            "http://127.0.0.1:3000/api/olexi-chat",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"✅ API endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"❌ API endpoint error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_server()