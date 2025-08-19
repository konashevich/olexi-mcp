# TESTING: Olexi MCP Connector

Purpose: Provide deterministic manual steps for Microsoft validation.

Prerequisites
- Public endpoint live at https://<your-production-domain>/
- MCP path reachable at https://<your-production-domain>/mcp
- No auth required on MCP for certification testing

Steps
1) Health check
   - GET https://<domain>/status → JSON includes `mcp: true` and `austlii.ok` (true/false)
   - GET https://<domain>/mcp/health → {"status":"ok","name":"Olexi MCP Server", ...}

2) List databases
   - Create a Copilot Studio test agent and add the MCP connector pointing to https://<domain>/mcp
   - In a test chat, invoke tool `list_databases`.
   - Expected: an array of objects with fields `code`, `name`, `description`; length > 10.

3) Search (boolean)
   - Invoke tool `search_austlii` with:
     - query: "privacy AND metadata"
     - databases: ["au/cases/cth/HCA","au/cases/cth/FCA"]
     - method: "boolean"
   - Expected: a list (>= 3 items) with fields `title`, `url`, `metadata` (string or null). `url` hosts on `https://www.austlii.edu.au/`.

4) Build URL
   - Invoke tool `build_search_url` with the same parameters.
   - Expected: a single `https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?...` URL string.

5) Progress search (optional)
   - Invoke tool `search_with_progress` with the same parameters.
   - Expected: progress events (0-1.0) then a list of results like step 3.

Error handling
- If AustLII is down, `search_*` may fail or return 0 results; `build_search_url` still returns a URL.
- HTTP errors map to 4xx/5xx from the upstream where applicable; connector itself responds 200 with content per MCP protocol.
