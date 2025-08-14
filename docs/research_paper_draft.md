# OLEXI MCP for Australian Legal Research: Server-Centred Design, Interfaces, and Agent-Oriented Evaluation

## Abstract
Reliable, interpretable legal research on legacy web systems requires interfaces that align with agentic workflows rather than brittle scraping. We present the OLEXI Machine Context Protocol (MCP) server for Australian legal research, exposing stable tools for database discovery and search over AustLII. The server formalises agent-oriented input/output contracts, supports progress semantics for long-running operations, and implements resilience measures (timeouts, capped retries, soft-fail health checks). A companion MCP host is used only for planning and summarisation to evaluate interoperability, compare against generic MCP hosts (e.g., VS Code MCP agents), and isolate the server’s contribution. We report on design decisions that improve tool selection, traceability, and robustness, and outline an evaluation plan measuring reliability, latency, and agent decision quality.

## 1. Introduction
Legal research frequently depends on institutional repositories with legacy interfaces. Direct scraping is fragile and opaque; agentic systems require clear tools with predictable contracts. The OLEXI MCP server prioritises stable, agent-friendly tools and minimal assumptions about hosts or models. Our contributions are: (i) a tool suite focusing on database discovery and search with progress; (ii) agent-focused descriptions that improve routing; (iii) resilience for legacy endpoints; and (iv) a host-agnostic evaluation setup.

## 2. Background and related work
- Machine Context Protocol (MCP): standardising tool/resource exposure over stdio or HTTP.
- Agentic tool use: the role of functional tool contracts in improving selection and grounding.
- AustLII specifics: SINO search quirks and the need to avoid upstream date operators.
- Related systems: VS Code MCP host workflows; tool ecosystems in LangChain and similar frameworks.

## 3. System overview (MCP server)
- Transport: FastMCP server; stdio by default; optional streamable HTTP with `/mcp/health` and `/mcp/info` diagnostics.
- Data model: SearchResultItem { title: string, url: string, metadata?: string }.
- Resource: `olexi://databases` returns JSON array of { code, name, description } for scope selection.
- Tools:
  - List Databases: enumerate available databases.
  - Search AustLII: structured results for given query and database codes; supports method in {boolean, auto, title}.
  - Build Search URL: method-aware deterministic link for the same query/scope (boolean/auto/title).
  - Search with Progress: same as Search AustLII but emits progress updates via MCP context.

## 4. Design principles
- Agent-first IO contracts: functional purpose, clear inputs/outputs, selection cues, and realistic limitations.
- Progress semantics: explicit progress messages during long-running search paths.
- Tunable resilience: environment-driven timeouts (AUSTLII_TIMEOUT), capped retries (AUSTLII_RETRIES), back-off (AUSTLII_BACKOFF), soft-fail health probe (AUSTLII_HEALTH_TIMEOUT).
- Separation of concerns: the host plans queries and summarises results; the server provides data tools only.
- Privacy by minimisation: no user content persistence; operational logs only.

## 5. Implementation specifics
- Search modes and adaptivity: method in {boolean, auto, title}. Hosts choose adaptively (auto for vague prompts; boolean for scoped); `Search with Progress` surfaces execution state.
- Year handling: no upstream date operators; optional host-side year range via title parsing (e.g., "[2024]" or "(D Month 2024)").
- Noise control: optional lexical stoplist via PREVIEW_STOPLIST.
- URL generation: deterministic shareable link for the executed query/scope.
- Error and progress events: stable error codes (PLANNING_FAILED, MCP_ERROR, SUMMARIZE_FAILED, HOST_AI_UNAVAILABLE) and progress messages at key stages.

## 6. MCP host context (for evaluation)
- Role: planning database scope and Boolean query; summarising results into British English Markdown; streaming SSE to the client.
- Interoperability: identical tool contracts operate under generic MCP hosts (e.g., VS Code MCP agents); our host serves as a controlled testbed.

## 7. Evaluation methodology
- Research questions: tool routing accuracy; reliability/latency under load; transparency benefits of progress.
- Datasets: stratified queries by specificity and jurisdiction; temporal slices.
- Metrics: error/timeout rates; retry success; median and P95 latency; preview precision proxy; method selection accuracy; progress completeness.
- Baselines/ablations: no-progress; single-method (boolean); scraper without retries/back-off; alternative host (VS Code MCP) for interop.
- Protocol: fixed seeds; rate limits respected; toggled env settings to measure contribution of each resilience feature.

## 8. Security, privacy, and ethics
- No user content persistence; redacted/limited operational logging; API key handling at host only.
- Ethical upstream use: soft-fail health gating; bounded retries; conservative timeouts.

## 9. Limitations and threats to validity
- Upstream HTML changes and availability.
- Planner variance across models/runs.
- Generalisability beyond AustLII and SINO.

## 10. Reproducibility
- Artefacts: server code, tool spec, environment configuration, and sample datasets.
- How to run: stdio mode and HTTP mounting; environment variables documented; small scripts for evaluation.

## 11. Conclusion
OLEXI MCP demonstrates a server-centric approach to legal research tooling: stable IO contracts, progress semantics, and resilience tuned for a legacy repository. The design is portable across MCP hosts and amenable to quantitative evaluation. Future work includes method-aware URL generation, richer metadata extraction, caching, and rate-aware planning.

## Appendix A: Condensed MCP interface
- Resource olexi://databases → [{ code, name, description }]
- Tool List Databases → same as resource.
- Tool Search AustLII(query: string, databases: string[], method: "boolean"|"auto"|"title") → SearchResultItem[]
- Tool Build Search URL(query: string, databases: string[], method: "boolean"|"auto"|"title") → string (HTTPS URL)
- Tool Search with Progress(query: string, databases: string[], method: ...; ctx) → SearchResultItem[] + progress

## Appendix B: Configuration
- AUSTLII_TIMEOUT, AUSTLII_RETRIES, AUSTLII_BACKOFF, AUSTLII_HEALTH_TIMEOUT, PREVIEW_STOPLIST, MCP_URL, PORT
