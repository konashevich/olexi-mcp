# Olexi AI — MCP Hybrid Server and Extension (AI-only)

Version: 3.2  
Date: 11 August 2025

Olexi AI is a browser extension and Python backend that orchestrate AI-driven legal research on AustLII. The system is strictly AI-only: when AI is not accessible, AI-dependent endpoints return 503 and the extension informs the user—no fabricated results and no legacy non-AI fallbacks.

## What’s in this repo
- FastAPI server exposing:
  - MCP Tools Bridge (REST): /api/tools/* (AI required for plan/summarize)
  - MCP server (Streamable HTTP) mounted at /mcp for MCP hosts (VS Code, etc.)
  - Static assets and status endpoints
- Browser extension (MV3) under `olexi-extension/`
- Scraper for AustLII’s CGI endpoint with proper headers and parsing
- AI handlers using google-genai (Gemini 2.5 Flash)

## AI-only behavior
- If GOOGLE_API_KEY is missing/invalid or AI fails:
  - /api/tools/plan_search → 503 Service Unavailable
  - /api/tools/summarize_results → 503 Service Unavailable
- The extension shows a clear message: “AI is not accessible.” No fallback to legacy. No fake results.

## Endpoints
- GET /status — JSON status, includes MCP availability flag
- MCP Tools Bridge (REST facade):
  - GET /api/tools/databases — Returns available AustLII databases
  - POST /api/tools/plan_search — AI plan (query, databases). AI required.
  - POST /api/tools/search_austlii — Scrape based on query/databases
  - POST /api/tools/summarize_results — AI summary from results. AI required.
  - POST /api/tools/build_search_url — Constructs AustLII results URL
- MCP server: mounted at /mcp (Streamable HTTP)
 - AustLII health and uptime:
   - GET /austlii/health — Current health snapshot (ok, status, error, checked_at, latency_ms, cached) plus uptime, counters, and current_downtime
   - POST /austlii/health/probe — Force a live probe; returns fresh snapshot (cached=false)
   - GET /austlii/uptime — Uptime summary and counters only

## Setup
Prerequisites: Python 3.12+

```bash
# Clone and create venv
git clone <repo-url>
cd austlii-mcp-server
python -m venv .venv
source .venv/bin/activate

# Install deps
pip install -r requirements.txt

# Configure AI
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env

# Run server
./.venv/bin/python -m uvicorn main:app --reload --port 3000

# Verify
curl -s http://127.0.0.1:3000/status | jq
```

### Optional monitoring config (env)

```bash
export AUSTLII_POLL_INTERVAL=60           # seconds (default 60)
export AUSTLII_MONITOR_LOG=austlii_monitoring.txt
export AUSTLII_LOG_MAX_BYTES=2097152      # 2 MB
export AUSTLII_LOG_BACKUPS=5              # rotate backups
```

## AustLII health monitoring and uptime

The server continuously probes AustLII and logs results to a rotating JSONL file.

- Log file: austlii_monitoring.txt (JSON Lines, rotated by size)
- Log schema per line:
  - { ts, ok, status, error, latency_ms, source, interval_s }
  - Example:

```json
{"ts":"2025-08-11T10:32:00Z","ok":true,"status":200,"error":"","latency_ms":142,"source":"poll","interval_s":60}
```

- In-memory metrics:
  - Rolling samples for up to 7 days
  - Counters: total_checks, ok_checks, fail_checks, first_checked_at, last_ok_at, last_fail_at, current_downtime
  - Uptime windows: last_5m, last_1h, last_24h, last_7d, since_start (0..1). Null until enough samples exist.

### Health endpoints

- GET /austlii/health
  - Returns current health snapshot with fields:
    - ok, status, error, checked_at, latency_ms, cached
    - uptime: { last_5m, last_1h, last_24h, last_7d, since_start }
    - counters and current_downtime
  - Query live=true to force an immediate probe

- POST /austlii/health/probe
  - Triggers an immediate probe; updates cache/metrics/logs and returns a fresh snapshot

- GET /austlii/uptime
  - Returns only uptime summary, counters, and current_downtime

Quick checks:

```bash
curl -s http://127.0.0.1:3000/austlii/health | jq
curl -s -X POST http://127.0.0.1:3000/austlii/health/probe | jq
curl -s http://127.0.0.1:3000/austlii/uptime | jq
```

## License
Copyright (c) 2025. All rights reserved.