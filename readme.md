# OLEXI Australian Laws MCP Server (OLEXI-MCP)

Version: 3.4
Date: 13 August 2025

OLEXI-MCP is a research project by Dr Oleksii Konashevych at the intersection of law and technology. It’s a Model Context Protocol (MCP) server that searches AustLII (www.austlii.edu.au) — the free, online database of Australian legal information (legislation and case law).

OLEXI-MCP is a free tool that lets your AI chat agent search across Australian laws. It works with any MCP-capable host, including:

- ChatGPT (via Connectors) — quick overview: https://youtu.be/WLWbtkJqq8I?si=MR8_HskYOuhUEEY0
- Claude by Anthropic
- VS Code + GitHub Copilot
- Any other MCP-supporting app
- OLEXI Chrome extension for AustLII (coming soon)

Once connected, you can ask legal questions and your AI won’t just guess — it’ll search AustLII and cite real legislation and case law, with links. In general-purpose chats (e.g., ChatGPT), you can nudge tool use by mentioning “Australian laws” or explicitly asking it to use the “OLEXI MCP” tool.

For developers and researchers:

Add manually to your own MCP host:

```json
{
  "mcpServers": {
    "austlii": {
      "transport": {
        "type": "http",
        "url": "https://olexi-mcp-root-au-691931843514.australia-southeast1.run.app/"
      }
    }
  }
}
```

- The MCP tool is open source — git clone and enjoy
- Docker image is available — no hassle
- Or use the hosted endpoint: https://olexi-mcp-root-au-691931843514.australia-southeast1.run.app/



Fun’s over — boring technical stuff:

Why MCP and host-led reasoning
- Separation of concerns: the MCP server provides tools (search, URL builder) only; the host agent plans queries and writes the summary. This prevents “black-box” scraping and keeps logic inspectable.
- Portability: any MCP-capable host (VS Code, browsers, services) can orchestrate the same tools.
- Safety and least-privilege: the tool-only server holds no AI keys; the host owns AI usage and policy.

What makes AustLII different (methodology and findings)
The AustLII search stack is a legacy CGI system with subtle constraints. We validated the following through careful experimentation:
- The true endpoint is the CGI script: https://www.austlii.edu.au/cgi-bin/sinosrch.cgi. “Modern” paths like /search/ return 410 and are unsuitable for programmatic queries.
- Requests must look like a real browser. At minimum include:
  - User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36
  - Referer: https://www.austlii.edu.au/forms/search1.html
- Multiple database filters require repeating the key: use mask_path=… once per database; don’t comma-join.
- Parsing needs precision. Results live under div.card and each item is li.multi; naïve list scraping grabs UI tabs instead of cases.
- Database codes follow a stable taxonomy: au/[type]/[jurisdiction]/[court_code] (for example au/cases/cth/HCA, au/cases/nsw/NSWSC). See database_map.py for coverage.

Research framing: disciplined legal search, not fuzzy browsing
- Query planning enforces grouped ORs, avoids brittle date operators, and sanitises unsafe patterns before execution.
- Adaptive search modes: use method=auto for broad or vague prompts; prefer boolean (and sometimes titles-only) when scope is clear; switch modes automatically on empty previews.
- Host-side filters: optional year-from/to extraction from titles (e.g., [2024] …) and a configurable stop-list to reduce preview noise.
- Resilience: timeouts, retries, and back-off are environment-configurable; health probes are soft-gated to keep research flowing.

## System architecture (high level)

MCP host → MCP tool calls → AustLII → Preview in host

- MCP server (tool-only): search_austlii, search_with_progress, build_search_url.
  - Production (Cloud Run): MCP Streamable HTTP is served at the service root path "/" (no /mcp).
  - Local: identical — serve MCP at the root path "/".
- Scraper: performs the CGI request with required headers and parses div.card > li.multi.

## Endpoints
- MCP server (Streamable HTTP):
  - Production: served at the root path `/` (POST handshake at `/`).
  - Local: served at the root path `/`.
  - Connect a compatible host to use the tools (list_databases, search_austlii, build_search_url)

Environment variables (selected)
- AUSTLII_POLL_INTERVAL, AUSTLII_HEALTH_TIMEOUT
- AUSTLII_TIMEOUT, AUSTLII_RETRIES, AUSTLII_BACKOFF
- AUSTLII_CONNECT_TIMEOUT, AUSTLII_READ_TIMEOUT (optional, override AUSTLII_TIMEOUT for connect/read respectively)
- AUSTLII_JITTER (optional jitter proportion for retry backoff, e.g., 0.3 => ±30%)

## Setup (local)

Prerequisites: Python 3.12+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn mcp_http:app --host 127.0.0.1 --port 3000 --reload
```

See `docs/how_to_start_locally.md` for local start and handshake test.

## MCP usage (tool-only)
- Production (recommended): point your MCP host at the Cloud Run service base URL; the MCP transport is at `/` (no path).
  - AU endpoint: https://olexi-mcp-root-au-691931843514.australia-southeast1.run.app/
- Local (legacy combined app): connect to `/mcp` if you run the host+MCP server together.
- Planning and summarisation remain in the host; this server never embeds an AI model.

## AustLII mechanics (implementation notes)
- CGI endpoint: `https://www.austlii.edu.au/cgi-bin/sinosrch.cgi`
- Headers: strict User-Agent and Referer to mimic genuine browser traffic
- Query parameters: `query`, `method` (boolean/auto/title), `meta` (`/au`); repeat `mask_path` per database
- Parser: find `div.card`, then `li.multi` items; ignore sorting/navigation chrome
- URL builder: repeat `mask_path` keys and percent-encode parameters

## Deployment
- Dockerfile and Cloud Run ready (container exposes `$PORT`, default 8080 in Cloud Run).
- Production region: deployed in Australia (australia-southeast1) for lower latency to Australian users and data locality.
  - Service URL (MCP at root): https://olexi-mcp-root-au-691931843514.australia-southeast1.run.app/
- See `docs/deploy_cloud_run.md` for build, push, and deploy steps, and suggested environment configuration.

## Ethics and respectful use
- Respect AustLII’s infrastructure: moderate timeouts and retries; avoid aggressive scraping; include a real User-Agent.
- Provide clear citations and a direct results URL for verification.
- Maintain an audit trail of health checks and security events for accountability.

## Acknowledgements
This project builds upon AustLII’s open access to legal materials and the MCP ecosystem for structured tool orchestration. We aim to advance practical research methods in Law & Technology while respecting the systems and communities that make such research possible.

## License
MIT — see the LICENSE file for details. If you prefer a permissive license with an explicit patent grant, consider Apache-2.0.