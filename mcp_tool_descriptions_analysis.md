# Olexi MCP Tools: Current Design and Interface Specification

## Abstract
This document specifies the current Machine Context Protocol (MCP) interface of the Olexi legal research server. It formalizes the available resources and tools, their input and output contracts, selection guidance, and operational constraints. The intent is to enable reliable orchestration by AI agents and straightforward integration by host applications without exposing implementation internals.

## System Overview
The MCP server is implemented using `FastMCP` and exposes:
- One structured resource for database discovery (`olexi://databases`).
- Three primary tools for search workflow: `List Databases`, `Search AustLII`, and `Build Search URL`.
- One optional long-running variant: `Search with Progress` (emits progress updates via MCP context).

Transport
- Default: stdio (`mcp.run()`).
- Optional: streamable HTTP when mounted; diagnostic endpoints include `/mcp/health`, `/mcp/info`, and `/mcp/` root. These are auxiliary and not required for MCP use.

Data Model
- SearchResultItem: { title: string, url: string, metadata?: string }

## Resource Catalog

### olexi://databases
- Purpose: Provide the authoritative list of Australian legal databases (codes, names, descriptions) to inform search scope selection.
- Output: JSON array of objects: { code: string, name: string, description: string }.
- Typical usage: List first; select a subset of codes for subsequent tools.

## Tool Interface Specifications

Each tool is described by its functional purpose, inputs, outputs, selection criteria, and constraints. Inputs and outputs are stable contracts intended for AI routing and host integration.

### List Databases
- Purpose: Enumerate available Australian legal databases with codes and descriptions across courts, tribunals, and legislation.
- Inputs: none
- Outputs: Array<{ code: string, name: string, description: string }>
- Selection: Use to determine the search scope before calling search tools.

### Search AustLII
- Purpose: Execute searches across one or more selected databases and return structured items for analysis, citation, or follow-up scraping.
- Inputs:
	- query: string (supports boolean operators AND, OR, NOT)
	- databases: string[] (database codes from List Databases)
	- method: string = "boolean" (optional; search mode)
- Outputs: Array<SearchResultItem>
- Scale: Can return hundreds to thousands of items depending on scope.
- Constraints: Dependent on AustLII availability and response times; latency increases with scope and result set size.
- Use when: Retrieving machine-usable search results for research, precedent checks, and statutory references.

### Build Search URL
- Purpose: Produce a direct, shareable HTTPS link to the equivalent AustLII results for manual browsing or bookmarking.
- Inputs:
	- query: string
	- databases: string[]
	- method: "boolean" | "auto" | "title" (optional; default "boolean")
- Outputs: string (HTTPS URL)
- Notes: No network call is made; output mirrors the same query/scope and search method used.
- Use when: A user or system needs a navigable URL instead of parsed results.

### Search with Progress
- Purpose: Perform the same search as Search AustLII while emitting progress via MCP context for long-running queries.
- Inputs:
	- query: string
	- databases: string[]
	- ctx: MCP context (for progress messages)
	- method: string = "boolean" (optional)
- Outputs: Array<SearchResultItem>
- Constraints: Best suited for large scopes or high-latency scenarios where UI feedback is desirable.
- Use when: The host or user benefits from progress indicators during execution.

## Selection Guidance (Agent-Oriented)
- Need database options or codes? Use List Databases (or the resource `olexi://databases`).
- Need structured, programmatic results? Use Search AustLII.
- Need a shareable link for the same query/scope? Use Build Search URL.
- Expect a long-running search and want UI feedback? Use Search with Progress.

## Operational Considerations
- Performance: Result size scales with the number of databases and query breadth. Consider narrowing scope for faster turnaround.
- Reliability: The tools depend on external AustLII availability. Transient slowdowns are possible during peak times.
- Progress Semantics: Search with Progress reports a monotonic fraction [0,1] with brief status messages; final output matches Search AustLII.
- Stability: Inputs/outputs are stable contracts abstracted from implementation details to minimize breaking changes.

## Interface Quality Metrics
To enable robust AI routing and integration, the interface descriptions prioritize:
1. Decision clarity (when to use which tool or resource).
2. Explicit parameter contracts (names, types, optionality, defaults).
3. Output structure predictability (schemas that are easy to parse and display).
4. Comparative context (distinguishing structured results vs shareable link vs progress-enabled search).
5. Practical constraints (performance, dependency on upstream availability).

## Examples (Non-executing)
- Query across high courts: query = "unconscionable conduct", databases = ["au/cases/cth/HCA", "au/cases/cth/FCA"].
- Shareable link: Build Search URL with query = "duty of care", databases = ["au/cases/nsw/NSWSC"].
- Large-scope with feedback: Search with Progress for query = "misleading or deceptive conduct", databases = ["au/cases/vic/VSC", "au/cases/nsw/NSWCA"].

## Privacy and Security Notes
- The server exposes only functional tools and a database resource; no user data is persisted by these interfaces.
- Hosts should manage API keys and credentials separately (outside tool inputs) where applicable.

## Change Management
This specification reflects the current implementation in `mcp_server.py`. Future changes should update this document only when input/output contracts or selection semantics change.
