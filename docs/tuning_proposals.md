# Generalised Tuning Proposals (British English)

This document outlines general, system-wide tuning options that don’t hard-code domain specifics (e.g., medical negligence). These are phrased and implemented in a technology-agnostic fashion and can be applied or toggled without binding to any single subject area.

| Proposal | Explanation | My comment |
|---|---|---|
| Prefer precise Boolean grouping | Always use parentheses around OR groups and keep AND chains tight to the core terms. Reduces ambiguity from operator precedence and improves recall without over-broad matches. | |
| Light lexical expansion only | Allow modest stem/wildcard expansion (e.g., term*), but avoid blanket wildcards or multi-token stemming. Keeps noise low while still catching natural variants. | |
| Adaptive search mode (auto vs tuned) | For broad/unclear/vague enquiries, start with method=auto (ranked full‑text) to maximise recall. When scope is explicit or implied (courts, years, statute, specific issues), switch to tuned search (Boolean with precise grouping and/or titles‑only) and apply filters/tools. Provide fallbacks: if tuned yields thin results, retry with auto; if auto is noisy, run a titles‑only or Boolean pass. | |
| Avoid date operators in upstream search | Do not use site-specific date operators; instead, add plain year tokens where helpful and apply any date filtering host-side after retrieval. This mitigates brittle CGI behaviour. | |
| Soft-fail health checks | If the upstream health probe times out, proceed with a warning instead of blocking the session. Improves reliability under transient slowness. | |
| Configurable HTTP timeouts and retries | Centralise timeouts in environment variables and add limited retries with back-off/jitter. Avoids hard failures on temporary network stalls. | |
| Titles-only secondary pass (optional) | Provide an optional titles-only follow-up search when the first pass is very broad. Improves precision at the cost of some recall; gated by a flag. | |
| Post-fetch noise filters (lexical) | Optionally drop preview items containing generic off-topic indicators (maintain a configurable stoplist). Apply only when not explicitly requested by the user. | |
| Year extraction from titles | Extract years from titles to enable optional host-side year filtering without relying on upstream query syntax. | |
| Result preview transparency | Stream planned query, selected databases, item counts, and fallback usage in progress events so the user can see what happened and why. | |
| Shareable URL generation | Always provide a direct link to the upstream results with the exact query and databases used, for auditability and manual exploration. | |
| Summariser neutrality and scoping | Instruct the summariser to stay within provided results, avoid speculation, and clearly mark when data is thin. Improves trust and reduces hallucination risk. | |
| Error event consistency | Emit structured error events with stable codes (e.g., PLANNING_FAILED, MCP_ERROR, SUMMARISE_FAILED) to simplify debugging and UX handling. | |
| Environment-gated behaviours | Gate optional behaviours (precision mode, recency bias, retries) behind environment variables to allow per-deployment tuning. | |
| Tool doc clarity | Make tool descriptions explicit about capabilities and trade-offs (boolean vs titles-only; performance expectations; limitations). Helps hosts choose the right tool. | |
| Logging hygiene | Log parameters at a high level (e.g., which databases, counts) but avoid logging sensitive content. Improve redaction and sampling for production. | |
| Progressive back-off for upstream | When upstream is slow, increase delay between retries slightly and cap total attempts; reflect this in progress events for transparency. | |
| Front-end SSE robustness | Use per-request aborts, reasonable global timeouts, and parser tolerance for partial chunks; surface a single consolidated error to the user. | |
| British English localisation | Ensure UI text, messages, and summaries use British English spelling and terminology (e.g., prioritise, behaviour, summarise). | |
| Minimal assumptions about domains | Keep prompts and filters domain-agnostic; avoid hard-coded vocab tied to a single legal area to preserve general applicability. | |

Notes
- All proposals are designed to be configurable and safe by default.
- No domain-specific lexicons or exclusions are included here.
- British English is applied throughout this document and should be used across UI and summaries.
