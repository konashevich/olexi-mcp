# MCP/Extension Architecture Improvement Plan

## 1. Summary of VS Code Agent Workflow (from chat.json)
- The agent receives a user request (e.g., "Find recent HCA cases on unconscionable conduct and summarise.").
- It plans the search: identifies relevant databases (HCA) and constructs a Boolean query ("unconscionab*").
- It invokes MCP tools in sequence:
  1. `mcp_austlii_list_databases` to get available DBs
  2. `mcp_austlii_search_with_progress` to search for cases
  3. Fetches and summarizes results (using agent-side AI, not MCP server AI)
  4. `mcp_austlii_build_search_url` to generate a shareable link
- The agent orchestrates the workflow, using MCP only for legal data access and search, not for AI summarization.

## 2. Analysis: Correctness and Suitability
- **Correct Use of MCP:**
  - The agent uses MCP as a capability bus: it plans, queries, and builds URLs, but does not offload AI summarization to MCP.
  - All AI/LLM work (summarization, synthesis) is performed by the agent on the host side, respecting resource isolation.
- **Orchestration Model:**
  - The agent is free to plan and sequence MCP tool calls as needed, not locked into a pre-orchestrated flow.
  - This matches the intended MCP design: tools are atomic, stateless, and composable.
- **Extension Suitability:**
  - The Chrome Extension should adopt this agent-led orchestration model, not hardcode a fixed workflow.
  - The extension and its server act as the MCP host, using MCP for legal data and keeping AI/LLM work isolated.

## 3. Reasoning and Recommendations
- **Isolation Principle:**
  - MCP server must not expose or use host-side AI resources (e.g., paid LLMs, REST summarizer).
  - Extension/server must use MCP only for legal data, not for AI computation.
- **Agent Freedom:**
  - The agent (in VS Code or Extension) should have full freedom to plan, sequence, and synthesize using MCP tools.
  - Pre-orchestration in the extension is limiting and conceptually wrong; redesign for agent-led planning.
- **Hybrid System:**
  - MCP server and Extension server run on the same platform but must remain strictly isolated in resource usage and responsibility.
  - Extension/server is the MCP host, responsible for agent orchestration and AI work.

## 4. Improvement Plan
1. **Redesign Chrome Extension Workflow:**
   - Remove hardcoded multi-step orchestration.
   - Implement agent-led planning: allow the agent to choose and sequence MCP tool calls.
   - Provide UI/UX for agent input, feedback, and result synthesis.
2. **Enforce Resource Isolation:**
   - MCP server exposes only legal data/search tools, not AI/LLM endpoints.
   - Extension/server uses MCP for data, host-side AI for summarization/synthesis.
3. **Document Architecture:**
   - Update README and developer docs to clarify separation of concerns, agent orchestration, and resource boundaries.
   - Provide examples of agent-led workflows in both VS Code and Extension contexts.
4. **Test and Validate:**
   - Ensure agent workflows in Extension match VS Code agent behavior (as seen in chat.json).
   - Validate that no AI/LLM calls are routed through MCP server.

## 5. Next Steps
- Refactor Extension to support agent-led orchestration.
- Audit MCP server endpoints to confirm no AI/LLM exposure.
- Update documentation and provide sample agent workflows.
- Review and test for strict resource isolation and correct agent behavior.

## 6. Status Update (implemented)
- Chrome Extension redesigned: agent-led, MCP-only tool usage (databases, search, build URL). No server-side AI calls.
- Legacy orchestration removed from the extension; no commented-out code left. Test page deprecated and emptied.
- Basic database selector UI added and heuristic auto-selection when none chosen.
- Isolation preserved: extension acts as MCP host; MCP server remains data/tools only.
