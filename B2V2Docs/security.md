# security.md — Authentication, Authorization, Secrets, Privacy

## Current state (verified against `server.py`)

- **No authentication or authorization on any route.** Every `/api/*` route in `api.md` is open. This is acceptable **only** because the server is currently run localhost-only, single-operator.
- **No centralized path-traversal guard.** `_api_file`, `/api/upload-audio`, `/api/upload-clip` each inline their own check (`if any(c in filename for c in ("../", "..\\", "/", "\\"))`). Functionally present, but not centralized or independently tested.
- **No CORS policy documented or restricted** — flagged in the historical audit as wide-open; verify current behavior before exposing beyond localhost.
- **Secrets**: `.env` is gitignored; `.env.example` contains no live keys. ~20 flat, ungrouped API keys (Anthropic, Gemini, ElevenLabs, DashScope, Runway, Kling, BFL, Ideogram, OpenAI, Creatomate, TikTok, Meta, Twitter, LinkedIn, Apify, DB credentials). No secrets manager, no per-environment separation (dev/staging/prod).
- **No SQL-injection risk found** in a partial review (`db.py` uses `psycopg2` parameterized queries) — **not confirmed line-by-line for every query**; a full pass is still owed before treating this as fully verified.
- **Uploaded content is unusually sensitive once Phase 1B ships**: `/api/upload-clip` already accepts arbitrary MP4 uploads with zero auth. Once this is real camera footage — potentially a real person's face and voice — the exposure is materially more consequential than an unauthenticated dashboard showing AI-generated cards.

## Hard gates (do not cross without closing the prerequisite)

| Gate | Condition | Prerequisite |
|---|---|---|
| **CP7** | Exposing the dashboard/API beyond `localhost` (LAN or public) | Authentication + centralized path-traversal guard must exist first — this is a hard blocker, not a recommendation |
| — | Accepting real camera/talking-head footage from an operator who isn't the sole trusted local user | Same as above — treat CP7 as strictly more urgent once Phase 1B (raw footage) ships to any real brand |
| — | Any paid API key (Runway, Kling, ElevenLabs, etc.) being reachable from an endpoint an untrusted caller can invoke | Auth must gate any endpoint that triggers a paid external call, to prevent cost-abuse via an open API |

## Rules for new work

1. **Every new file-accepting endpoint must use the shared path-traversal guard** once it's centralized (`coding-rules.md` rule 3) — never re-implement the inline check.
2. **Never log or persist a secret value.** `.env` values are read at process start; do not echo them into `PIPELINE_SUMMARY.md`, debug reports, or job status output.
3. **New API keys added to `.env.example` must be immediately either wired to real code, or explicitly labeled "reserved, not yet implemented"** — the current file blurs this distinction (Runway/Kling/BFL/Ideogram/Creatomate keys are cataloged with no code calling them), which is itself a security-adjacent risk: an operator can't tell what's actually active.
4. **No route may skip the (future) auth layer "just for internal use"** — internal-only exceptions are exactly how auth gaps regress; if a route is meant to be internal-only, it should not exist on the public route table at all.
5. **Compliance-adjacent visual checks** (CP8 in `architecture.md`) belong to the AI Reviewer role, not to this document — but any new visual-compliance check that inspects uploaded footage must not persist or transmit that footage anywhere beyond the local pipeline's own storage without an explicit, separate privacy review.

## Privacy considerations specific to Phase 1B/1C

- Raw footage/talking-head uploads may contain a real, identifiable person's likeness and voice. Before this data flows through any third-party API (B-roll generation, background matting, voice cloning), confirm that provider's data-retention/training-use terms — this is a per-provider check, not a one-time blanket approval.
- The viral-clips pipeline (Phase 1C) operates on an operator's **own** existing video (their upload rights are assumed, per `product.md` Journey E's scoping) — do not extend `ClipSourcer` to fetch arbitrary third-party YouTube content without a separate rights/ToS review.

## Deferred / not yet decided

- Choice of auth mechanism (API key, session, OAuth) for the dashboard — to be decided when CP7 is actually scheduled (`roadmap.md`), not speculatively now.
- Secrets-manager migration (away from flat `.env`) — only warranted once this becomes a multi-machine/hosted deployment; premature for the current single-operator local-first model.
