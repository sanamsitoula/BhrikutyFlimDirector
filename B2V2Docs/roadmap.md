# roadmap.md — Phase-Wise Plan (Priority 8, but the execution contract for everything above)

## Execution protocol — read this before starting any phase

1. **One phase is worked at a time.** Phase *N+1* does not start — no code, no docs, no scaffolding for it — until Phase *N*'s measurable output has been produced **and verified** against its stated pass criteria below.
2. **"Verified" means the stated check was actually run and passed**, not that the corresponding code was written. Re-run the check yourself; do not accept "should be fixed" as done.
3. **Every phase declares explicit Inputs and Outputs**, not just a task list — see the template in Phase 1 below. Inputs = what must already exist/be true before the phase can start. Outputs = the concrete, checkable artifacts/state the phase must produce. This is what makes "did we actually achieve this phase" answerable by inspection instead of judgment call.
4. **For every phase, report**: Summary · Files changed · Architecture impact · Risks · Future improvements — before moving on.
5. **Any "future improvement" or deferred item surfaced during a phase is immediately added to the Carried-Forward TODO Checklist below** (not just mentioned in prose and forgotten). **The LAST step of every phase, without exception, is reviewing that checklist**: check off anything the current phase happened to resolve, confirm anything still open is still correctly assigned to a future phase (or flag it as newly blocking if it turns out to be), and add anything newly discovered. This is the loop that keeps deferred work from silently disappearing.
6. **If a phase's work reveals that an earlier document (`architecture.md`, `requirements.md`, etc.) needs updating, update it in the same change** — documentation drift is exactly the failure mode this folder exists to prevent.
7. **Nothing in any phase deletes a currently-working path.** The four live brands (`chain_clarity`, `ecoWorld`, `loksewawithmanoj`, `manojsir`) must keep working, unmodified, throughout every phase.
8. Every phase is scoped from `architecture.md`'s choke points (CP1–CP12), `requirements.md`'s FR/NFR list, and the historical Error Checklist in `ARCHITECTURE_AUDIT.md` (repo root, kept as the historical record this roadmap operationalizes).
9. **Never silently replace a tool/provider named in a phase's Task list** — see `coding-rules.md` RULE 0. Extend with an alternative and ask; never swap and ship.

---

## Carried-Forward TODO Checklist (persistent — reviewed as the LAST step of every phase)

This is the loop mechanism: nothing raised as a "future improvement" lives only in a chat response. It lands here, gets assigned to the phase that will actually close it (or flagged as unassigned if none of the existing phases cover it), and gets checked off — with the verification that was actually run, not just "should be done" — only when that phase reaches it.

| # | Item | Raised during | Assigned to | Status |
|---|---|---|---|---|
| T1 | Wire `server.py` and `tools/generate_phase.py` through `core/config.py` (currently only `pipeline.py` is wired; the other two still have their own copy of the `.env` loader) | Phase 1 | Phase 2 (`core/` extraction) | ☐ Open |
| T2 | Register a real `JAMENDO_CLIENT_ID` and run one live end-to-end smoke test of Tier B (automated) in `tools/audio/music_provider.py` | Phase 1 | **Unassigned — operational, not a coding task.** Whoever has a Jamendo account does this; re-check this row at the start of any phase that depends on Tier B being proven live | ☐ Open |
| T3 | Mix `phase_N/music/background_music.mp3` into `create_video.py`'s final render (ducked under narration) — today the file is produced but never consumed by the render step, so it has **zero effect on any rendered video's actual audio** until this lands | Phase 1 | Phase 5 (already explicitly scoped — "Advanced AI Workflows + Raw-Footage/Music Core" / Phase 1D audio-mixing) | ☐ Open |

---

## Phase 0 — Documentation (this deliverable)

**Inputs** (what had to exist before this phase could start):
- The codebase as it stood at the start of this work — `server.py`, `pipeline.py`, `db/*`, `tools/*`, `.env.example`, `requirements.txt` — readable and inspectable.
- `ARCHITECTURE_AUDIT.md` (repo root) as the raw research material to ground the docs in, cross-checked against the live code rather than trusted at face value.

**Task**: Establish `B2V2Docs/` as the single source of truth (this folder), grounded in direct inspection of the current codebase, not invention.

**Outputs** (what this phase had to produce):
- 12 files under `B2V2Docs/` (11 docs + README index), each citing at least one verified fact from the real codebase.
- A phase-gate execution protocol (this section) governing every phase after it.

**Output checklist (measurable)**:
- [ ] All 11 files listed in `README.md` exist and each cites at least one verified, concrete fact from the actual codebase (file path, line number, or grep result) rather than a generic statement.
- [ ] `README.md`'s priority order and phase-gate rule are in place.

**Verification**: read each file back and confirm every factual claim (file names, line counts, table names, route names) matches a `grep`/`Read` of the real file — this was done during authoring (see citations throughout each doc) and should be spot-re-checked before Phase 1 begins if significant time has passed.

**Status: COMPLETE as of this writing.** → Phase 1 may begin.

---

## Phase 1 — Quick Wins (de-duplicate, close config gaps)

**Depends on**: Phase 0.

**Inputs** (what had to exist before this phase could start):
- Phase 0's completed `B2V2Docs/` set (this roadmap, `architecture.md`'s choke-point table, the historical Error Checklist in `ARCHITECTURE_AUDIT.md`) — Phase 1's task list is derived directly from these, not from a fresh read of the codebase.
- The specific pre-existing defects these tasks target, each independently confirmed present before starting: `pipeline.py:339`'s `ANTHROPIC_API_KEY`-only gate; the three-way `DB_NAME` default mismatch; `schema.sql` missing `asset_versions`/`content_views`; `.env.example` vs. actual `os.environ` reads drift; `tools/social_apis` as a nested gitlink; the duplicated `.env` loader in 3 files; `music_brief.md` being generated with nothing consuming it.
- No new external service is *required* to start (Tier A of item 7 needs no API at all); `JAMENDO_CLIENT_ID` and Postgres access are optional and only needed to fully close two specific checklist rows (see Risks in the Phase 1 report).

**Task**:
1. Fix `pipeline.py` Step 5's hardcoded `"ANTHROPIC_API_KEY" in os.environ` gate → check "is any provider configured" instead (closes CP10/E10).
2. Reconcile `DB_NAME` default across `db/db.py`, `db/migrate.py`, `install.py` to one value (closes part of E1).
3. Fold `asset_versions`/`content_views` into `schema.sql` (or otherwise make a fresh `psql -f schema.sql` create every table `db.py` queries) (closes E2).
4. Reconcile `.env.example` against actual `os.environ` reads — add missing vars (`GEMINI_API_KEY`, all `DB_*`), label unimplemented ones (Runway/Kling/BFL/Ideogram/Creatomate) as "reserved, not yet implemented" (closes CP9/E3).
5. Resolve `tools/social_apis`'s nested `.git` — either declare it as a proper submodule or replace with a static snapshot (closes E5).
6. Create a single `core/config.py` `.env` loader as the first extraction — used by at least one of `server.py`/`pipeline.py`/`generate_phase.py` going forward (closes part of CP1). Do not require all three to migrate in this phase; wiring one caller through it and leaving the others as a tracked follow-up is acceptable.
7. Ship the `MusicProvider` free tier consuming the already-generated `music_brief.md` — the single lowest-effort, zero-new-infrastructure fix available; closes the "generated brief with no consumer" gap. **Status: DONE** — implemented as `tools/audio/music_provider.py` with **both** tiers available side by side (per `coding-rules.md` RULE 0 — an earlier version of this work incorrectly swapped Pixabay for Jamendo instead of keeping both; corrected):
   - **Tier A — Manual**: Pixabay's public API (verified against pixabay.com/api/docs/) has no Music/Audio search endpoint, so this is a manual-drop tier, not an API call — download a track yourself from pixabay.com/music/ (or any source), drop it in `phase_N/music/manual/`. Checked first; no key needed.
   - **Tier B — Jamendo**: automated free API (developer.jamendo.com), used only when no manual file is present. Requires `JAMENDO_CLIENT_ID`.
   Wired into `pipeline.py` as Step 4b (`--skip-music` to opt out); skips gracefully if neither tier has anything usable.
8. **(Last step, every phase)** Review the Carried-Forward TODO Checklist above: add T1/T2/T3 (all newly surfaced during this phase), confirm their phase assignments are correct, check off nothing yet (none are closeable from within Phase 1 itself).

**Outputs** (what this phase had to produce):
- Modified: `pipeline.py`, `db/db.py`, `install.py`, `db/schema.sql`, `.env.example`.
- New: `core/__init__.py`, `core/config.py`, `tools/audio/music_provider.py`.
- Git-level fix: `tools/social_apis` converted from gitlink to regular tracked files.
- 3 items added to the Carried-Forward TODO Checklist (T1–T3), each pre-assigned to the phase that will close it (or flagged unassigned/operational).
- Docs corrected in the same change they were invalidated by: `architecture.md`, `roadmap.md` (Pixabay→two-tier correction).

**Output checklist (measurable)**:
- [x] `grep -n "ANTHROPIC_API_KEY" pipeline.py` no longer shows a step-gating check tied to that specific key; running a phase with only `GEMINI_API_KEY` set still executes Step 5. Verified: `any_llm_provider_configured()` (now in `core/config.py`) tested directly with only `GEMINI_API_KEY` set → returns `True`.
- [x] `grep -n "DB_NAME" db/db.py db/migrate.py install.py` shows one consistent default (or all three require the env var with no default). Verified: all three now default to `"bhrikutyflimdirector"`.
- [x] Fresh `psql -f db/schema.sql` against an empty DB, then a code path calling `record_asset_version`/`log_content_view`, does **not** error on a missing table. `asset_versions`/`content_views` (with their indexes) are now defined directly in `schema.sql`. **Not independently re-run**: no local `psql`/Postgres instance was available in this session — verify with an actual fresh-DB run before relying on this in production.
- [x] `grep -oE "os\.environ(\.get)?\(['\"][A-Z_]+" -r .` produces a variable set that exactly matches `.env.example`'s documented keys. Verified by running the actual diff both directions (excluding vendored/.venv paths): zero vars read by code are undocumented; every documented-but-unused var is explicitly labeled RESERVED/planned or IMPLEMENTED in `.env.example`.
- [x] `git status` from repo root no longer shows nested-repo confusion for `tools/social_apis`. Verified: nested `.git` removed, `git ls-files -s` now shows mode `100644` (regular files) instead of `160000` (gitlink) for every file under that path.
- [x] Running a phase with `music_brief.md` present produces an actual audio file, not silence/no music track. Verified both tiers: **Tier A (manual)** confirmed fully end-to-end against a disposable test project (synthetic source track looped/faded to target duration via ffmpeg, real output file produced, ~60s duration confirmed via ffprobe). **Tier B (Jamendo)**: search-term extraction against a real brief and the graceful skip-path (no manual file, no `JAMENDO_CLIENT_ID`, no writes to the live brand) confirmed. **Not yet verified**: a live network call against the real Jamendo API (no test `client_id` was available in this session) — do one real smoke-test run before relying on Tier B in production. Tier A has no such gap since it doesn't call any external API.
- [x] **Carried-Forward TODO Checklist reviewed** (this phase's last step, per Execution Protocol rule 5): T1/T2/T3 added above with phase assignments; nothing was closeable from within Phase 1 itself, so nothing is checked off yet.

**Phase 1 status: substantially complete.** Two items above are implemented and locally verified but carry an explicit "not independently re-run against the real external system" caveat (Postgres schema apply; live Jamendo API call) — both require credentials/services not available in this session. Run those two specific checks before treating Phase 1 as fully closed and starting Phase 2.

**Difficulty**: Low. **Risk**: Low. **Time est.**: 3–5 days.

---

## Phase 2 — Architecture Cleanup (extract `core/`, define `Renderer`)

**Depends on**: Phase 1 verified complete.

**Inputs** (what must be true before this phase starts):
- Phase 1's output checklist fully checked, including the two currently-caveated rows (Postgres schema apply, live Jamendo call) re-run against the real systems.
- `core/config.py` existing and already wired into `pipeline.py` (Phase 1 output) as the pattern the remaining extractions in this phase follow.
- Carried-Forward TODO Checklist reviewed at Phase 1 close (T1 assigned here — see below).

**Task**:
1. Extract `Brand`, `Phase`, `PipelineRun` as real dataclasses/models in `core/`.
2. Move `server.py`'s business-logic methods (regex parsing, compliance-status computation) into `core/`, leaving `server.py` as routing only.
3. Define the `Renderer` interface itself (even before HyperFrames/footage implementations exist) so `remotion_renderer.py`/`ffmpeg_assembler.py` become its first two implementations — not two more disconnected scripts (partially closes CP5; full closure completes in Phase 6).
4. Centralize the path-traversal guard into one shared function used by every file-accepting endpoint (closes E6).
5. **(Carried forward — T1)** Wire `server.py` and `tools/generate_phase.py` through `core/config.py`, closing out the last two of the three original duplicated `.env` loaders (fully closes CP1).
6. **(Last step, every phase)** Review the Carried-Forward TODO Checklist: check off T1 once step 5 above is verified; confirm T2/T3 are still correctly assigned (T2 to whoever holds Jamendo credentials, T3 to Phase 5); add anything newly discovered during this phase's work.

**Outputs** (what this phase must produce):
- `core/brand.py`, `core/phase.py` (or equivalent) with real model classes, imported by `server.py`/`pipeline.py` in place of ad hoc JSON-blob handling.
- The `Renderer` interface (even with only its two existing-path wrappers as implementations).
- One centralized path-traversal guard function, used by every file-accepting endpoint.
- `server.py` and `generate_phase.py` no longer carrying their own `.env`-loader copy (T1 closed).
- Carried-Forward TODO Checklist updated (T1 checked off with its verification; T2/T3 status re-confirmed).

**Output checklist (measurable)**:
- [ ] Every existing dashboard route returns byte-identical (or documented-intentional-diff) responses before/after the move — verified by manually exercising each route pre- and post-change.
- [ ] `Renderer` interface exists with `RemotionRenderer` and `FfmpegAssembler` as concrete implementations; `pipeline.py`'s existing render step calls through the interface.
- [ ] A test asserting a `../` payload is rejected passes identically on every file-accepting endpoint (`_api_file`, `/api/upload-audio`, `/api/upload-clip`).
- [ ] All four live brands can still run a full phase end-to-end with no regression.
- [ ] `grep -rn "_env_path\|_env = BASE_DIR" server.py tools/generate_phase.py` finds no remaining independent `.env`-loader copy — both import from `core/config.py` instead (closes T1).
- [ ] Carried-Forward TODO Checklist reviewed and updated as this phase's last step.

**Difficulty**: Medium. **Risk**: Medium (must not change route responses). **Time est.**: 1.5–2.5 weeks.

---

**Standing note for every phase from here on (3–7)**: each phase below follows the same contract established in Phases 1–2 even where not re-typed in full — (a) an explicit **Inputs** section (what the prior phase's verified output must include before this one starts), (b) an explicit **Outputs** section (the concrete artifacts/state produced, not just tasks performed), and (c) a mandatory **last task step**: review the Carried-Forward TODO Checklist, check off anything this phase closed, re-confirm anything still open is correctly assigned, and add anything newly discovered. When actually executing a later phase, write out its Inputs/Outputs explicitly at that time (mirroring Phase 1/2's format above) rather than skipping straight to the task list — this is not optional, it's what makes "did we actually achieve this phase" answerable by inspection instead of judgment call.

---

## Phase 3 — Core Improvements (testing + CI + job queue + Demo harness)

**Depends on**: Phase 2 verified complete.

**Task**:
1. Add a pytest suite for `core/` (now unit-testable in isolation from HTTP) — at least one test per E1/E2/E3/E5/E6/E10/E11.
2. Add a GitHub Actions workflow running lint + this test suite.
3. Replace ad hoc `threading.Thread` jobs with a durable, cost-aware queue table (closes CP2/CP3's durability requirement — required groundwork before any paid API is wired up in Phase 5).
4. Add minimal auth to the API (closes CP7 — at minimum, gate any endpoint that could trigger a paid external call or accept a file upload).
5. Build the Demo & Validation harness covering output formats #1–#3 only (slideshow / Shorts / platform-cuts) — formats #4–#6 are added in Phases 5–6 as those capabilities are built.

**Output (measurable)**:
- [ ] CI runs on every push/PR and fails on a lint or test regression.
- [ ] A server restart no longer silently drops in-flight job state — a job's status survives restart (durable queue verified by killing the process mid-job and confirming state is recoverable).
- [ ] At least one auth mechanism gates `/api/upload-clip` and `/api/run` — an unauthenticated request is rejected.
- [ ] `debug_report.md`-style pass/fail report exists with one row each for output formats #1–#3, runnable as a single command with no manual per-directory checking.

**Difficulty**: Medium-High. **Risk**: Low (additive). **Time est.**: 4–5 weeks.

---

## Phase 4 — Plugin System

**Depends on**: Phase 3 verified complete.

**Task**:
1. Wrap existing Remotion/ffmpeg path as the default `Renderer`; wrap existing TTS scripts behind `TTSEngine`.
2. Implement the generalized `LLMProvider` interface (Claude/Codex/Qwen/MiniMax/Gemini/DashScope) — this is where flawless new-LLM-provider support actually gets delivered (fully closes CP10).
3. Define (interfaces only — implementations land in Phase 5–6) `BRollProvider`/`FootageEditor`/`ClipSourcer`/`HighlightDetector`.
4. Add taste-skill-style design-dial instructions to the existing card-generation system prompt (`build_system_prompt()`).

**Output (measurable)**:
- [ ] A phase run with only a non-Anthropic, non-Gemini, non-Qwen provider configured (e.g. a stubbed MiniMax/Codex implementation) completes script generation successfully.
- [ ] Every existing TTS engine still produces correct output when invoked through the new `TTSEngine` interface — no behavior change versus pre-Phase-4.
- [ ] New interfaces (`BRollProvider` etc.) exist as importable, documented contracts with zero concrete implementations yet — this phase is about the seam, not the plugins.

**Difficulty**: Medium. **Risk**: Low (existing paths become the default plugin, unchanged behavior). **Time est.**: 3–4 weeks.

---

## Phase 5 — Advanced AI Workflows + Raw-Footage/Music Core (Phase 1B/1D groundwork)

**Depends on**: Phase 4 verified complete.

**Task**:
1. Build `ai/eval.py`'s bounded self-check loop, extended with a visual-check pass (closes CP6).
2. Implement `ResearchProvider`/`DeepResearchProvider` (optional, additive — manual `--topic`/`--outline` remains default).
3. Implement free-tier-first `BRollProvider` (Pexels/Pixabay before Kling/Runway) and remaining `MusicProvider` tiers, with a render cache (closes CP4) and cost-capped retry (closes E7) from day one — non-negotiable given CP3/CP4 dependency.
4. Implement `FootageEditor` (video-use pattern) operating on already-uploaded `/api/upload-clip` content.
5. Extend the Demo harness with format #4 (raw-footage + B-roll) and #5 (overlay infographics), run against stubbed/free-tier providers by default.

**Output (measurable)**:
- [ ] Running the same phase twice with unchanged inputs against a stubbed B-roll/voice provider does **not** re-invoke the paid API on the second run (cache hit verified).
- [ ] A simulated provider timeout/error triggers a bounded retry (<3 attempts), never an unbounded one.
- [ ] Demo harness formats #4–#5 pass, each producing a real output artifact meeting the pass criteria in `ARCHITECTURE_AUDIT.md`'s Demo & Validation table.
- [ ] A deliberately corrupt/truncated clip fed to the footage path produces a reported failure (non-zero exit or failed job status), never a silent success (closes E8).

**Difficulty**: Medium-High. **Risk**: Medium (first paid-API integration — CP3/CP4 must be genuinely done, not just planned). **Time est.**: 6–7 weeks.

---

## Phase 6 — Production Optimization + Viral Clips (Phase 1C)

**Depends on**: Phase 5 verified complete.

**Task**:
1. Extend the content-hash render cache to all renderers.
2. Ship `FootageRenderer` as a first-class `Renderer` implementation (camera clips + B-roll + talking-head, including `BackgroundMatteProvider` free tier) — fully closes CP5.
3. Ship the full Phase 1C viral-clips pipeline: `ClipSourcer` (YouTube/mp4 ingestion) + `HighlightDetector` (heuristic pass first, LLM re-rank second) + branding pass, reusing `platform_cutter.py` as-is — closes CP11.
4. Resolve the external `LearnRemotion` dependency one way or the other (fully closes E4) — either vendor/declare it or remove the `remotion_composer.py` path.
5. Extend the Demo harness with formats #5–#6 — all six output formats now covered end to end.
6. Add the new visual-compliance check (closes CP8).

**Output (measurable)**:
- [ ] Demo harness runs all 6 output-format rows and reports pass on every one, from one disposable demo brand, touching zero live-brand data.
- [ ] `read tools/video/remotion_composer.py`'s `REMOTION_OUT_DIR` default either points inside this repo (vendored) or the path no longer exists in the codebase (removed) — no more silent external dependency.
- [ ] A YouTube URL or local MP4 fed to `ClipSourcer` → `HighlightDetector` → branding → `platform_cutter.py` produces at least one trimmed, branded, platform-shaped clip.
- [ ] A B-roll clip or talking-head clip that doesn't match brand guidelines is flagged by the new visual-compliance check, not silently passed.

**Difficulty**: High. **Risk**: Medium-High — consider splitting into 6a (Footage) / 6b (Viral Clips) if timeline pressure requires shipping incrementally. **Time est.**: 8–10 weeks.

---

## Phase 7 — Product Experience Layer (outcome-oriented intake)

**Depends on**: Phase 6 verified complete. Deliberately last — a `ProjectOrchestrator` has nothing coherent to orchestrate until the plugin interfaces above are real, stable, and stop needing to be explained to the user.

**Task**:
1. Build `ProjectOrchestrator`/`IntakeAgent` — goal parsing via `LLMProvider`, capped clarifying questions (2–5), `GoalTemplate` registry.
2. Build `ai/director.py` — `plan(script) -> Storyboard` (the one AI module with no existing mapping anywhere in Phases 1–6).
3. Build `ThumbnailGenerator` (genuinely new — no thumbnail capability exists today).
4. Surface podcast-audio and transcript as standalone downloadable outputs (already exist internally as the voiceover track and `subtitles.srt`).
5. Build `ProjectMemory` — new DB tables (`audience_profiles`, `templates`, `learned_preferences`) + `get_context(brand_slug)`, sequenced after real usage history exists from Phases 1–6's own operation.

**Output (measurable)**:
- [ ] A single free-text goal ("make me a YouTube video about SpaceX") produces a finished multi-platform output after answering at most 5 clarifying questions, verified on at least the demo brand.
- [ ] The existing phase-by-phase dashboard/CLI still works unchanged for an operator who wants manual control — this phase is additive in front of, not a replacement for, Phases 1–6.
- [ ] A second run for the same brand asks strictly fewer (or equal) clarifying questions than the first, evidencing `ProjectMemory` actually reducing the question count over time.

**Difficulty**: High. **Risk**: Medium (additive in front of a stable existing system — low regression risk to what already works, but a large new product surface). **Time est.**: 6–8 weeks.

---

## Rough total estimate

~8–9.5 months at solo-operator pace, front-loaded on Phase 3 (testing/CI) because every later phase — especially Phase 5's first paid-API integration and Phase 6's user-facing capabilities — depends on being able to verify "nothing broke" automatically.

**If the timeline needs to compress**, in priority order: (1) ship Phase 1's `MusicProvider` free tier alone first — lowest effort, zero new infrastructure; (2) split Phase 6 and ship footage/B-roll before viral clips as two separate releases.
