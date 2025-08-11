#!/usr/bin/env python3
# test_api.py - Quick API test script

import requests
import json
import time

TOOLS_BASE = "http://127.0.0.1:3000/api/tools"

def test_tools_flow():
    print("Testing Olexi Tools Bridge...")

    try:
        # databases
        r = requests.get(f"{TOOLS_BASE}/databases", timeout=10)
        print("databases:", r.status_code, len(r.json()) if r.ok else r.text)

        # plan (may 503 if AI unavailable)
        payload = {"prompt": "test question about contracts"}
        rp = requests.post(f"{TOOLS_BASE}/plan_search", json=payload, timeout=30)
        print("plan_search:", rp.status_code, rp.text[:120])

        if rp.ok:
            plan = rp.json()
            rs = requests.post(f"{TOOLS_BASE}/search_austlii", json={"query": plan["query"], "databases": plan["databases"]}, timeout=30)
            print("search_austlii:", rs.status_code, (len(rs.json()) if rs.ok else rs.text))
        else:
            print("plan failed (likely AI unavailable); skipping search")
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    test_tools_flow()
