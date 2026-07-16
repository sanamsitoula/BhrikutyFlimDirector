# coding-rules.md — Code Style, Naming, Testing, Linting (Priority 7)

## RULE 0 — Never silently replace a planned tool/provider. Extend, don't remove.

**This is the single highest-priority rule in this file — it exists because it was violated once already (see incident below) and the user explicitly requires it going forward.**

- If `roadmap.md`, `architecture.md`, or the user names a specific tool/provider/library for a task, and that tool turns out not to fit (missing capability, no public API, wrong license, etc.) — **do not silently substitute a different tool and ship it as if it were the same task.**
- The correct sequence is: (1) verify the concrete blocker (e.g. "this API doesn't have the endpoint we need" — cite the actual documentation checked), (2) **add an alternative/extension alongside the originally-named tool** so both are available as options, never delete or replace the original's slot, (3) **surface the conflict to the user and ask** before proceeding, unless the user has already pre-authorized this kind of substitution in writing.
- "The named tool can't do X" is a reason to *extend* the design (add a second tier, a manual/fallback path, a second implementation of the same interface) — it is never sufficient justification to unilaterally decide and auto-deploy a replacement.
- This applies to tools, libraries, APIs, providers, UI frameworks, database engines — anything the user or the docs named specifically.

**Incident this rule codifies**: during Phase 1 of `roadmap.md`, the `MusicProvider` free tier was specified as "Pixabay Music API." Pixabay's public API (verified at pixabay.com/api/docs/) turned out to document Images/Videos search only, with no Music/Audio endpoint. Instead of surfacing that and asking, Jamendo was silently substituted and shipped as if it fulfilled the same task. The user's own workflow — manually downloading tracks from Pixabay's website and supplying them to the pipeline — was never asked about and was excluded entirely. **Fix applied**: `tools/audio/music_provider.py` now supports BOTH tiers side by side — Tier A (manual: operator drops a self-downloaded file, e.g. from Pixabay, into `phase_N/music/manual/`, checked first) and Tier B (automated: Jamendo API, used only if no manual file is present). Neither tier was removed to make room for the other.

## Current state (honesty note)

No linter, formatter, or style config exists today (no `.flake8`, `pyproject.toml`, `ruff.toml`, `.prettierrc`). This has been invisible because the project has had one author; it will surface immediately with any second contributor or AI agent working across sessions. This document is the interim style contract until an enforced linter config lands (`roadmap.md` Stage 1).

## Language/runtime conventions already in use — follow these

- **Python**: 3.11+, standard library `http.server` for the API (no framework), `psycopg2` raw SQL for DB access (no ORM), `subprocess` for orchestration.
- **File naming**: `snake_case.py`, one script per CLI tool under `tools/`, module-level constants in `UPPER_SNAKE_CASE` (e.g. `PROJECT_ROOT`, `BASE_DIR`).
- **Node/TS**: only inside `remotion/` (Root/Composition/ShortsComposition `.tsx`), otherwise the project is pure Python + static HTML.
- **No build step for HTML pages** (`dashboard.html`, `phase_dashboard.html`, etc.) — inline/embedded JS, no bundler. Keep it this way unless `design-system.md` is updated to authorize a framework migration first.

## Rules for new/changed code

1. **Never duplicate the `.env` loader or the provider-fallback chain.** These are already reimplemented 3× (`server.py`, `pipeline.py`, `generate_phase.py`) — this is a known defect (`architecture.md` §2), not a pattern to extend. Once `core/config.py` and `ai/providers.py` exist (`roadmap.md` Stage 1–4), new code imports from them; it does not add a 4th copy.
2. **Never gate a step on a specific provider's env var** (e.g. `"ANTHROPIC_API_KEY" in os.environ`). Use "is any `LLMProvider` configured" — the exact bug this rule prevents is documented as CP10/E10 in `architecture.md`.
3. **New file-accepting endpoints must reuse the shared path-traversal guard** once it exists (`api.md` Known Gaps #2) — never re-implement the `../`/`..\\` inline check a 4th time.
4. **New CLI tools go under `tools/` as thin wrappers** that import from `core/`/`ai/`/`render/` once those modules exist — not as another disconnected top-level script duplicating logic already in `core/`.
5. **New rendering logic implements the `Renderer` interface** (`architecture.md` §3) — it does not become a 4th disconnected video-assembly path alongside `create_video.py`/`remotion_composer.py`/`remotion/`.
6. **Prefer extending an existing module over creating a new one.** Before adding a new file, check `architecture.md` §2/§3 for whether the responsibility already has a home.
7. **No comments explaining what code does** — names should carry that. A comment is justified only for a non-obvious constraint, workaround, or invariant (matches the general project-wide instruction already in effect for this assistant).
8. **Don't add error handling/fallbacks for scenarios that can't happen.** Validate at system boundaries (user input via the dashboard, uploaded files, external API responses) — trust internal function contracts once a shared `core/` module exists.
9. **Keep `pipeline.py`'s CLI flags and every `tools/*.py` script's standalone invocation working unchanged** through any refactor (backward compatibility — `requirements.md` NFR-8).

## Testing

- **Current state**: one test file (`projects/test_hello.py`) tests an unrelated hello-world function — effectively zero coverage of `server.py`, `pipeline.py`, `tools/*`, or `db/*`. An informal manual smoke-test harness exists (`tools/debug_pipeline.py`, `tools/debug_ffmpeg.py`, `tools/run_debug.sh`/`.bat`) but is developer-invoked, not CI-gating.
- **Going forward**: every bug fix or new module lands with at least one automated test exercising it. Every item in the historical Error Checklist (`ARCHITECTURE_AUDIT.md`) gets one test as `core/` becomes unit-testable in isolation from HTTP (`roadmap.md` Stage 3).
- Prefer testing `core/` functions directly once extracted, rather than only through `server.py`'s HTTP layer — the whole point of extraction is to make this possible.
- The Demo & Validation harness (one row per output format, pass/fail) becomes the integration-test suite once built (`roadmap.md` Stage 3) — new output formats are not considered done until they have a row there.

## Linting/formatting (target — not yet configured)

- Python: add `ruff` (lint + format) config as part of Stage 1 of `roadmap.md`. Until then, match the prevailing style in the file being edited rather than introducing a new one.
- No linting config change is itself a justification for a large reformatting diff — land it as its own isolated change, never bundled with a feature/bug-fix commit.

## Scope discipline (applies to every task, not just this file)

- A bug fix does not need surrounding cleanup. A one-shot script does not need a reusable abstraction it will never be called from twice.
- Don't design for hypothetical future requirements beyond what's explicitly scoped in the current `roadmap.md` phase.
- Three similar lines are better than a premature abstraction — this applies especially to the plugin interfaces in `architecture.md` §3: implement the interface when there is a second real implementation to justify it, not preemptively for a hypothetical third.
