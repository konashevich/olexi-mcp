## Olexi MCP Connector for AustLII (Independent Publisher)

Overview
- Purpose: Provide a lightweight MCP (Model Context Protocol) server that enables Copilot Studio agents to search AustLII and generate shareable result links for legal research.
- Scope: Discovery/search only. Returns titles, links, and limited metadata; users open the primary source on AustLII.
- Transport: MCP Streamable HTTP mounted at `/mcp` within the existing FastAPI app.

Public endpoint
- Base URL: https://api.olexi.legal/
- MCP endpoint: https://api.olexi.legal/mcp
- Health: https://api.olexi.legal/mcp/health and https://api.olexi.legal/status

Authentication
- Default for certification: No auth on the MCP endpoint. The server supports API keys for some non-MCP flows, but MCP path is open for certification to simplify validation.
- If you later enable API key for MCP, document the header and provide test credentials.

Capabilities (tools)
- list_databases(): Returns an array of database descriptors (code, name, description).
- search_austlii(query, databases, method="boolean"): Returns a list of search results with title, url, metadata.
- build_search_url(query, databases, method="boolean"): Returns a single HTTPS URL to AustLII results (no network call).
- search_with_progress(query, databases, method="boolean"): Same as search but provides progress updates via MCP progress callbacks.

Configuration in Copilot Studio
1) Choose to add an MCP connector and provide the MCP URL: `https://api.olexi.legal/mcp`
2) No authentication required for the MCP path during certification.
3) Provide the icon (32x32 and 128x128 PNG). Suggested: reuse `static/favicon-32x32.png` and create a 128x128 if needed.

Sample queries
- "privacy act AND metadata retention" across HCA/FCA
- "misleading or deceptive conduct AND [2020 TO 2024]"
- "torts negligence NSW Court of Appeal"

Limitations and notes
- Dependent on AustLII availability and response time; results may vary.
- The connector returns links and metadata only; open sources on AustLII for the full text.
- Designed for a legacy HTML endpoint (no official API). The connector follows normal web requests and avoids invasive techniques.

Data rights and attribution
- The connector surfaces links to primary law and lightweight metadata. The underlying primary legal texts are public domain; access is via AustLII.
- Include attribution in user-facing experiences where appropriate: "Results via AustLII (austlii.edu.au)."
- See RIGHTS.md for details.

Support and privacy
- Privacy Policy: see `PRIVACY_MCP.md` and `static/privacy-mcp.html`.
- Support: see SUPPORT.md.
- Security posture: see SECURITY.md.
