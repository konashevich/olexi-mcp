# Olexi MCP (AustLII) — Independent Publisher Submission Package

This document bundles all artifacts and a PR-ready body for Microsoft Copilot Studio Independent Publisher certification.

## Public MCP URL
- https://olexi-mcp-root-au-691931843514.australia-southeast1.run.app/
  - Transport: Streamable HTTP at service root (`/`).

## Publisher
- Name: Olexi
- Website: https://olexi.legal
- Support: ai@olexi.legal

## Product site
- https://mcp.olexi.legal
  - Terms: https://mcp.olexi.legal/terms.html
  - Privacy: https://mcp.olexi.legal/privacy.html

## Connector manifest
- File: `docs/copilot/connector/mcp-manifest.json`
- Icons (absolute):
  - 32x32: https://mcp.olexi.legal/icons/icon32.png
  - 128x128: https://mcp.olexi.legal/icons/icon128.png

## Documentation
- Overview/Usage: `docs/copilot/connector/README.md`
- Testing steps: `docs/copilot/connector/TESTING.md`
- Support: `docs/copilot/connector/SUPPORT.md`
- Security: `docs/copilot/connector/SECURITY.md`
- Changelog: `docs/copilot/connector/CHANGELOG.md`
- Rights & attribution: `docs/copilot/connector/RIGHTS.md`

## Data source and rights
- Primary source: AustLII (austlii.edu.au). We return links and light metadata; full text remains on AustLII.
- Attribution: Included in site and docs.
- Terms/permissions: Attribution-only justification based on AustLII Web Developers materials. See `RIGHTS.md` and PDFs under `docs/austlii/`. If a permission letter is obtained later, attach it.

## PR-ready description (template)

Title: Olexi MCP (AustLII) — Independent Publisher connector submission

Summary:
- Adds an MCP connector that lets Copilot Studio and other MCP hosts search AustLII and return titles/URLs/metadata for Australian law. Full text remains on AustLII; we provide a shareable results URL.

Key details:
- Public MCP URL (root): https://olexi-mcp-root-au-691931843514.australia-southeast1.run.app/
- Auth: none (no keys required). No PII processed. Logs exclude content.
- Tools: list_databases, search_austlii, build_search_url, search_with_progress.
- Publisher: Olexi — https://olexi.legal — ai@olexi.legal
- Product site: https://mcp.olexi.legal
- Privacy: https://mcp.olexi.legal/privacy.html — Terms: https://mcp.olexi.legal/terms.html

Testing notes:
- Follow `docs/copilot/connector/TESTING.md` for steps and expected outcomes. Production MCP transport is at the service root.

Data rights:
- We cite and link to AustLII resources and return light metadata. See `RIGHTS.md` for justification and attribution. If requested, we can provide additional confirmation from AustLII.

Attachments:
- `mcp-manifest.json`, README, TESTING, SUPPORT, SECURITY, CHANGELOG, RIGHTS (paths above).
