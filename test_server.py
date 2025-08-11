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
    
    # Test 3: Test Tools Bridge endpoints
    print("\n🔍 Testing Tools Bridge endpoints...")
    try:
        r = requests.get("http://127.0.0.1:3000/api/tools/databases", timeout=5)
        print(f"✅ tools/databases: {r.status_code}")
        rp = requests.post("http://127.0.0.1:3000/api/tools/plan_search", json={"prompt": "test query"}, timeout=10)
        print(f"✅ tools/plan_search: {rp.status_code}")
        if rp.ok:
            plan = rp.json()
            rs = requests.post("http://127.0.0.1:3000/api/tools/search_austlii", json={"query": plan["query"], "databases": plan["databases"]}, timeout=15)
            print(f"✅ tools/search_austlii: {rs.status_code}")
        else:
            print("   plan_search unavailable (likely AI not configured)")
    except Exception as e:
        print(f"❌ Tools Bridge error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_server()