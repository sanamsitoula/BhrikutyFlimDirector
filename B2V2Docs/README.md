# B2V2Docs — Bhrikuty 2.0 Documentation Set

This folder is the **single source of truth** for architecture, product, and engineering decisions on this project. Before any non-trivial change — new module, new plugin, new API route, new table, new UI pattern — consult these documents in priority order:

| # | File | Purpose |
|---|---|---|
| 1 | [architecture.md](architecture.md) | Overall system architecture — current (as-is) and target (Bhrikuty 2.0) module boundaries |
| 2 | [product.md](product.md) | Vision, personas, user journeys |
| 3 | [requirements.md](requirements.md) | Functional and non-functional requirements |
| 4 | [design-system.md](design-system.md) | UI/UX components, tokens, interaction rules |
| 5 | [database.md](database.md) | Schema, relationships, indexing strategy |
| 6 | [api.md](api.md) | API contracts, routes, error responses |
| 7 | [coding-rules.md](coding-rules.md) | Code style, naming, testing, linting |
| 8 | [roadmap.md](roadmap.md) | Phase-wise plan, milestones, gating rules |

Two supporting documents, consulted alongside the above wherever relevant:

| File | Purpose |
|---|---|
| [ai-agents.md](ai-agents.md) | Responsibilities and interaction rules for each AI/plugin role |
| [security.md](security.md) | Authentication, authorization, secrets, privacy |
| [deployment.md](deployment.md) | Infrastructure, CI/CD, monitoring, backups |

## Ground rules

1. **Never introduce new architecture without first checking whether it already exists** in `architecture.md`. Extend existing modules/interfaces before creating new ones.
2. **If two documents conflict, stop and surface the conflict** — do not silently pick one interpretation.
3. **`roadmap.md` is executed phase by phase.** Do not start work on Phase *N+1* until Phase *N*'s measurable output has been produced **and verified** against its stated pass criteria. "The code was written" is not verification — running the stated check is.
4. Every completed unit of work is reported as: **Summary, Files changed, Architecture impact, Risks, Future improvements.**
5. These documents describe a **working, in-production system** (four live brands under `youtube_scripts/setup/projects/`). Nothing here proposes deleting or breaking an existing working path — see `architecture.md`'s "Nothing is deleted" rule.
6. **Never silently replace a tool/provider named in the roadmap or by the user because it "doesn't fit."** Verify the concrete blocker, add an alternative alongside the original (never remove the original's slot), and ask the user before proceeding. See `coding-rules.md` RULE 0 for the incident that made this a standing rule, and why "extend, don't swap" is non-negotiable here.

## Source of this document set

This set was derived from a full audit of the codebase as it existed on 2026-07-16 (`ARCHITECTURE_AUDIT.md`, repo root — kept as historical record, superseded operationally by this folder) plus direct inspection of `server.py`, `pipeline.py`, `db/schema.sql`, `db/migrate.py`, `.env.example`, and `requirements.txt`. Where a capability is described as "planned" or "not yet built," that reflects the real state at time of writing, not a stand-in for unverified assumptions.
