# Independent Publisher Proposal (Summary)

Service: Olexi MCP Connector for AustLII

Problem & audience
- Problem: Efficient discovery of Australian primary law across AustLII without manual browsing.
- Audience: Legal researchers, practitioners, and students using Microsoft Copilot Studio.

Data source
- AustLII (austlii.edu.au) legacy CGI search. Primary law content is public domain; connector returns links and minimal metadata.

Auth
- None (for MCP endpoint) to simplify review.

Endpoints
- MCP Streamable HTTP at `https://<your-production-domain>/mcp`
- Health at `/mcp/health` and `/status`

Operations (tools)
- list_databases
- search_austlii
- build_search_url
- search_with_progress

Limitations
- Dependent on AustLII uptime. No full-text replication; links only.

Publisher
- Name: <Your Publisher Name>
- Website: https://<your-website>
- Support: support@example.com

Notes
- Attribution: "Results via AustLII (austlii.edu.au)".
