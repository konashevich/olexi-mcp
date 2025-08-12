# MCP Tool Descriptions Analysis for AI Agents

## Purpose
This document analyzes what information AI agents actually need in tool descriptions to make effective decisions, avoiding unnecessary implementation details while providing sufficient context for intelligent tool selection and usage.

## Analysis Framework

**AI Agent Needs:**
1. **Purpose**: What does this tool accomplish?
2. **Context**: When should this tool be used?
3. **Inputs**: What parameters are expected and in what format?
4. **Outputs**: What kind of results will be returned?
5. **Scale/Scope**: How much data or what coverage to expect?
6. **Limitations**: Any constraints or boundaries?

**AI Agent Does NOT Need:**
- Implementation details (parsing strategies, HTTP headers, etc.)
- Technical architecture decisions
- Internal error handling mechanisms
- Specific technology choices (BeautifulSoup, requests, etc.)

---

## Tool Design (current)

The following table reflects the current, AI-focused design of tool descriptions. It expresses purpose, inputs/outputs, when to choose a tool, and why this level of detail is sufficient for agents.

| Tool | AI-focused description | Inputs | Outputs | When to use | Why this is sufficient |
|------|------------------------|--------|---------|-------------|------------------------|
| list_databases | Get available Australian legal databases and their codes; use first to decide where to search. | none | { code, name, description }[] | Before searching, to select scope | Agents need options and codes; internals are irrelevant. |
| search_austlii | Search Australian legal databases for cases, legislation, and related documents; returns structured results. | query: string (AND/OR/NOT), databases: string[] | { title, url, metadata? }[] | Case law research, precedent checks, statutory references | Enables correct tool selection and parameterization without exposing implementation. |
| build_search_url | Generate a direct, shareable URL to the equivalent AustLII results. | query: string, databases: string[] | string (HTTPS URL) | Bookmark/share results or manual browsing | Clarifies alternative output (URL) and that it mirrors search inputs. |
| search_with_progress | Same as search_austlii but emits progress updates for long-running queries. | query: string, databases: string[] | { title, url, metadata? }[] | Large scope searches or when UI needs progress | Distinguishes selection vs base search; no implementation detail required. |

---

## Design rationale (why we describe tools this way)

1. Functional, not technical: Agents need to decide which tool to call and how—not how it’s implemented.
2. Clear selection cues: Each tool states when to use it, improving routing and reducing trial-and-error.
3. IO contracts: Minimal, explicit inputs/outputs prevent malformed calls and clarify expectations.
4. Stable across refactors: Hiding internals avoids description churn when implementations change.
5. UI clarity: Human users in IDEs see concise, meaningful summaries without noise.

---

## Recommended Description Principles

### DO Include:
- ✅ **Functional purpose** (what it accomplishes)
- ✅ **Use case scenarios** (when to choose this tool)
- ✅ **Input requirements** (parameter types and formats)
- ✅ **Output expectations** (result structure and scale)
- ✅ **Selection criteria** (vs alternative tools)
- ✅ **Practical constraints** (limitations relevant to usage decisions)

### DON'T Include:
- ❌ **Implementation details** (parsing strategies, HTTP methods)
- ❌ **Technical architecture** (CGI endpoints, header requirements)
- ❌ **Internal error handling** (fallback mechanisms, retry logic)
- ❌ **Technology choices** (specific libraries, frameworks)
- ❌ **Historical context** (why certain approaches were chosen)

---

## Quality Metrics for AI-Focused Descriptions

1. **Decision Clarity**: Can an AI agent determine when to use this tool?
2. **Parameter Understanding**: Are input requirements clear and actionable?
3. **Output Expectations**: Will the AI know what kind of results to expect?
4. **Comparative Context**: Can the AI choose between similar tools?
5. **Practical Constraints**: Are usage limitations relevant to decision-making clearly stated?

---

## Next Steps

1. Validate descriptions render clearly in client UIs (e.g., VS Code MCP panel).
2. Observe agent tool selection; refine phrasing if consistent mis-selections occur.
3. Keep descriptions stable; only adjust when behavior or IO contracts change.

---

## Final AI-focused Descriptions (IO Contracts)

These are the succinct descriptions an AI agent should rely on, including inputs/outputs and selection cues.

### list_databases
- Purpose: Get available Australian legal databases and their codes for research across courts, tribunals, and legislation. Use first to decide where to search.
- Inputs: none
- Outputs: Array of { code: string, name: string, description: string }
- Selection: Pass selected codes into search_austlii/build_search_url

Example: N/A (no inputs)

### search_austlii
- Purpose: Search Australian legal databases for cases, legislation, and related documents; returns structured results for analysis.
- Inputs: query: string (supports AND/OR/NOT), databases: string[] (codes from list_databases)
- Outputs: Array of { title: string, url: string, metadata?: string }
- Scale: Can return hundreds to thousands of items
- Limitations: Dependent on AustLII availability; large queries take longer
- Use when: Case law research, precedent checks, statutory references

Example: query="unconscionable conduct", databases=["au/cases/cth/HCA","au/cases/cth/FCA"]

### build_search_url
- Purpose: Generate a direct, shareable URL to the AustLII results for the same query and databases.
- Inputs: query: string, databases: string[]
- Outputs: string (HTTPS URL)
- Notes: No network call performed; link suitable for bookmarking/sharing/manual browsing

Example: query="duty of care", databases=["au/cases/nsw/NSWSC"] → "https://www.austlii.edu.au/cgi-bin/sinosrch.cgi?..."

### search_with_progress
- Purpose: Same search as search_austlii but emits progress updates for long-running queries.
- Inputs: query: string, databases: string[]
- Outputs: Array of { title: string, url: string, metadata?: string }
- Limitations: Dependent on AustLII availability; duration scales with scope
- Use when: Many databases, large result sets, or UI needs progress feedback

Example: query="misleading or deceptive conduct", databases=["au/cases/vic/VSC","au/cases/nsw/NSWCA"]
