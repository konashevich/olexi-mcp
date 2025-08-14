# System Tuning: Current Behaviour (British English)

This document describes the current, implemented tuning of the Olexi legal research system. It reflects the live behaviour across planning, search, filtering, resilience, transparency, and summarisation. It is domain‑agnostic and uses British English.

## End‑to‑end flow
- Plan: Host-side AI plans a Boolean query and selects databases.
- Search: MCP tool executes the search (progress events available).
- Filter: Optional year range and lexical stoplist are applied host‑side.
- Fallback: If filtering empties results, broaden query and/or switch method.
- URL: A shareable AustLII URL is generated that mirrors the query, scope, and method (boolean/auto/title) used.
- Summarise: Host AI produces a neutral Markdown summary in British English.

## Search strategy
- Boolean grouping: The planner enforces precise Boolean syntax, always grouping OR alternatives with parentheses and keeping AND chains tight to core terms.
- Light lexical expansion: The planner prefers gentle stemming (e.g., stem*) alongside exact phrases and avoids broad wildcards or multi‑token stemming.
- Adaptive method: The host selects method automatically based on prompt specificity: auto for vague prompts; boolean for scoped prompts. The upstream scraper accepts method in {"boolean", "auto", "title"}.
- Titles‑only mode: A titles‑only variant is available via method="title" and is used as a fallback when appropriate.
- Date handling: Upstream date operators are not used. Any date cues are represented as plain year tokens in the query; year filtering is performed host‑side.

## Resilience and performance
- Soft‑fail health checks: Before searching, a lightweight health probe runs. On timeout or failure, the system continues with a progress warning rather than blocking.
- Configurable HTTP timeouts and retries: The scraper uses environment‑driven timeouts, capped retries, and a fixed back‑off between attempts.
	- AUSTLII_TIMEOUT (seconds), AUSTLII_RETRIES, AUSTLII_BACKOFF (seconds)
- Cached health state: A cached snapshot is used with a staleness threshold; the live probe timeout is configurable via AUSTLII_HEALTH_TIMEOUT.

## Post‑fetch processing
- Year filtering: Years are extracted from titles (e.g., "[2024]" or "(D Month 2024)") and an optional inclusive year range is applied via API parameters yearFrom/yearTo.
- Noise stoplist (lexical): An optional, configurable stoplist removes items whose titles contain obvious off‑topic indicators (environment variable PREVIEW_STOPLIST).

## Fallback strategy
- If results are empty after filters, the system emits a progress event and attempts a single broadened query:
	- Heuristics include replacing AND with OR and removing long‑phrase quotes.
	- The search method may switch once: boolean → auto, auto → title, title → boolean.

## Transparency and events
- Progress events: The server streams structured events for planning, adaptive method selection, search progress, preview counts, and fallback usage.
- Results preview: A preview event includes the planned query, selected databases, unfiltered/filtered counts, and a subset of items.
- Error events: Errors are surfaced with stable codes: PLANNING_FAILED, MCP_ERROR, SUMMARIZE_FAILED, and HOST_AI_UNAVAILABLE.
- Shareable URL: A direct upstream link is generated using the MCP tool, ensuring auditability and manual exploration.

## Localisation
- Summaries are produced in British English and the summariser prompt emphasises neutrality and scope adherence (no speculation; mark thin evidence clearly).

## Environment configuration
- AUSTLII_TIMEOUT, AUSTLII_RETRIES, AUSTLII_BACKOFF — scraper network behaviour
- AUSTLII_HEALTH_TIMEOUT — live probe timeout
- PREVIEW_STOPLIST — comma‑separated terms to filter from titles
- HOST_GOOGLE_API_KEY / GOOGLE_API_KEY — host‑side AI credentials
- HOST_MODEL — host‑side AI model name
- PORT, MCP_URL — Streamable HTTP transport settings

## Security and operational signals
- API key and origin checks for host endpoints with security event logging (e.g., invalid_api_key, too_many_ips, rate_limited) to a dedicated log.
- Health and uptime endpoints provide operational observability without exposing sensitive data.

## MCP tooling alignment
- Tools: List Databases, Search AustLII, Build Search URL, Search with Progress (emits MCP progress updates).
- Method parameter: The search tools support method values "boolean", "auto", and "title" to align with the adaptive and fallback strategy.

## Omissions by design
- No upstream date operators are used; temporal constraints are handled via plain year tokens and host‑side filters.
- No domain‑specific lexicons or hard‑coded exclusions; behaviour is general‑purpose across legal topics.
