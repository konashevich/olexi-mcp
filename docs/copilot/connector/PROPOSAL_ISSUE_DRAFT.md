# Proposal: Olexi MCP (AustLII) — Independent Publisher Connector

## Summary
An MCP server that enables MCP-capable hosts (e.g., Copilot Studio, ChatGPT Connectors, Claude, VS Code + Copilot) to search AustLII for Australian laws and cases, returning titles/URLs/light metadata and a shareable results URL. Full text is hosted by AustLII; the connector provides discovery and citation links.

## Audience
Legal researchers, practitioners, academics, students, and policy teams working with Australian law.

## Public MCP URL (production)
- Base: https://olexi-mcp-root-au-691931843514.australia-southeast1.run.app/
- Transport: Streamable HTTP at service root (`/`).

## Authentication
- None. Public read-only discovery; no PII processed. Logs exclude content.

## Tools
- list_databases() — available legal databases
- search_austlii(query, databases, method) — titles, URLs, metadata
- build_search_url(query, databases, method) — shareable results URL
- search_with_progress(...) — search + progress events

## Data source and rights
- Source: AustLII (austlii.edu.au). We cite and link, returning light metadata only.
- Attribution included in docs/site. Rights details in `RIGHTS.md`. Permission letter can be provided if required.

## Publisher
- Name: Olexi — https://olexi.legal — ai@olexi.legal

## Testing
- Steps documented in `docs/copilot/connector/TESTING.md`.

## Risks/Notes
- Primary risk is data rights acceptability for scraping-like discovery. Our approach is respectful (titles/links only, no bulk content); we will adjust if policy requires.
