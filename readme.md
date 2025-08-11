# Olexi AI — MCP Hybrid Server and Extension (AI-only)

Version: 3.3  
Date: 11 August 2025

Olexi AI is a browser extension and Python backend that orchestrate AI-driven legal research on AustLII. The system is strictly AI-only: when AI is not accessible, AI-dependent endpoints return 503 and the extension informs the user—no fabricated results and no legacy non-AI fallbacks.

## What’s in this repo
- FastAPI server exposing:
  - MCP Tools Bridge (REST): `/api/tools/*` (AI required for plan/summarize; gated by auth)
  - MCP server (Streamable HTTP) mounted at `/mcp` (tool-only: no AI)
  - Health and uptime endpoints for AustLII
  - Static assets and `/status`
- Browser extension (MV3) under `olexi-extension/`
- Scraper for AustLII’s CGI endpoint
- AI handlers using Google Gemini

## Endpoints
- GET `/status` — JSON status (AI availability, AustLII health snapshot)
- MCP Tools Bridge (REST facade):
  - GET  `/api/tools/databases`
  - POST `/api/tools/plan_search`        (AI; 503 if AI unavailable)
  - POST `/api/tools/search_austlii`
  - POST `/api/tools/summarize_results`  (AI; 503 if AI unavailable)
  - POST `/api/tools/build_search_url`
- MCP server (Streamable HTTP): mounted at `/mcp`
  - GET `/mcp/health` — basic OK JSON
  - Use a host (e.g., VS Code Continue) to connect to `/mcp`
- AustLII health:
  - GET  `/austlii/health` — health + uptime summary (use `?live=true` to force probe)
  - POST `/austlii/health/probe` — immediate probe
  - GET  `/austlii/uptime` — uptime/counters only

## Authentication

Production (silent, no user prompts)
- The published extension auto-authorizes on first use (no copy/paste keys).
- Flow (server-side endpoints):
  - POST `/auth/provision` — extension sends its store ID, device_id, and a DPoP public key; server validates Origin (chrome-extension://<store-id>) and issues short-lived access_token (JWT, ~10 min) + refresh_token (~30 days) bound to that key.
  - POST `/auth/token` (grant_type=refresh_token) — refresh access tokens silently.
  - GET `/.well-known/jwks.json` — public signing keys (RS/ES).
- Tokens are bound to the device key (DPoP) and the store ID origin. Users do nothing.

Development (local)
- Keep simple API-key auth enabled for fast local runs.
- Requirements:
  - Header: `X-API-Key: <value from EXTENSION_API_KEYS or extension_api_keys.txt>`
  - Extension ID pinning:
    - Strict: set `EXTENSION_IDS="<your-dev-extension-id>"` (from chrome://extensions).
    - Easy: set `EXTENSION_IDS=""` to disable the ID check locally.
- Restart the server after .env changes:
  - `uvicorn main:app --reload --port 3000 --env-file .env`

Environment variables (auth & limits)
- `EXTENSION_API_KEYS` — comma-separated dev keys (local-only)
- `EXTENSION_IDS` — comma-separated allowed extension IDs (dev/prod)
- `OLEXI_DAILY_LIMIT` — default 50 requests/day per subject (device_id or API key)
- `OLEXI_MAX_DISTINCT_IPS` — anti-sharing heuristic (default 10/day)
- Optional (when provisioning is enabled):  
  `OLEXI_REQUIRE_DPOP=true`  
  `OLEXI_TOKEN_TTL=600`  
  `OLEXI_REFRESH_TTL=2592000`  
  `OLEXI_OAUTH_ISSUER=olexi-server`  
  `OLEXI_OAUTH_AUDIENCE=olexi-extension`

Rate limits & anti-cheat
- Hard daily cap: 50 requests/day per device_id (or API key in dev).
- Heuristics: block if too many distinct IPs per day; burst limits applied.
- Only your extension origin is accepted in production; others require manual admin-issued credentials.

Admin (manual non-extension clients)
- Manage client keys/tokens via admin endpoints (if enabled), protected by `ADMIN_API_KEY`.
- These clients are rate-limited and can be revoked independently.

## Setup

Prerequisites: Python 3.12+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo 'GOOGLE_API_KEY=your_gemini_api_key_here' >> .env
# Optional dev auth:
# echo 'EXTENSION_API_KEYS=your_dev_key' >> .env
# echo 'EXTENSION_IDS=' >> .env   # disable ID check locally
uvicorn main:app --reload --port 3000 --env-file .env
```

Quick checks
```bash
curl -s http://127.0.0.1:3000/status | jq
curl -s http://127.0.0.1:3000/austlii/health | jq
curl -s -H "X-API-Key: <dev_key>" http://127.0.0.1:3000/api/tools/databases | jq
```

## MCP usage (tool-only)
- Add to your VS Code MCP host (e.g., Continue):
```json
{
  "mcpServers": {
    "austlii": {
      "transport": { "type": "http", "url": "http://127.0.0.1:3000/mcp" }
    }
  }
}
```
- Tools available: `list_databases`, `search_austlii`, `build_search_url`. Planning/summarization must be done by the host’s AI (e.g., Copilot).

## AustLII health monitoring and uptime
- Rotating JSONL logs: `austlii_monitoring.txt`
- Log schema (per line): `{ ts, ok, status, error, latency_ms, source, interval_s }`
- In-memory uptime windows: `last_5m`, `last_1h`, `last_24h`, `last_7d`, `since_start`
- Endpoints:
  - GET `/austlii/health` (use `?live=true` to probe)
  - POST `/austlii/health/probe`
  - GET `/austlii/uptime`

## Security logs
- JSONL audit: `security_events.log` — records notable auth/abuse events (e.g., rate_limited, bad_origin, too_many_ips).

## Notes
- AI-only behavior: AI-dependent endpoints return 503 when AI is unavailable.
- No legacy chat endpoint; use `/api/tools/*` or `/mcp`.