# product.md — Vision, Personas, User Journeys (Priority 2)

## Vision

Bhrikuty Film Director turns a **brand + a topic** into a complete, brand-compliant, multi-platform content package — script, subtitles, infographic cards, voiceover, rendered video, and 8 platform-specific outputs — without requiring a camera, an editing suite, or a production team. The long-term direction (see `roadmap.md` Phase 7) is to move from a **pipeline-oriented** tool (the operator picks phases, providers, and steps) to an **outcome-oriented** one (the operator states a goal in one sentence; the system infers the rest and asks only what it genuinely can't).

Two product expansions are explicitly in scope, both **additive** to the existing card-slideshow output — never a replacement:
1. **Raw-footage & B-roll editing** — camera clips, talking-head video, AI-generated B-roll compositing.
2. **Viral-clips trimmer** — given a YouTube URL or existing MP4, automatically find and export branded short-form clips per platform.

## Personas

| Persona | Description | What they need from the system |
|---|---|---|
| **Solo operator (primary, real today)** | Runs 1–4 brands personally, no team. Currently the only real user — four live brands exist under this exact usage pattern. | Fast, reliable phase runs; brand consistency without re-entering config every time; a dashboard they can run every step from without touching a terminal. |
| **Future: multi-brand agency operator** | Manages content for several client brands at once. | Per-brand isolation (already exists via `brand_slug`), audit trail of runs (`pipeline_runs`/`pipeline_steps` — exists), eventually auth once used beyond one machine (CP7 in `architecture.md`). |
| **Future: non-technical creator** | Wants "make me a video" without knowing what a "phase" or "provider" is. | The Phase 7 `ProjectOrchestrator`/intake-flow vision in `roadmap.md` — not built yet. |

## Core user journeys (current, working)

### Journey A — New brand onboarding
1. Operator runs `tools/init_brand.py` (interactive wizard or `--from-json`) to produce `brand_profile.json` (colors, typography, tone, platforms, content pillars).
2. Brand appears in the dashboard (`brand.html`) and is usable by any phase.

### Journey B — Produce one phase of content
1. Operator supplies `--topic`/`--outline` (CLI) or fills the dashboard's run form.
2. `pipeline.py` runs: script generation → compliance check → card render → TTS voiceover → text-content generation → video assembly → platform cuts.
3. Output lands in `_output/phase_NN/{youtube,youtube_shorts,tiktok,instagram,twitter,linkedin,blog,github}/` plus a `PIPELINE_SUMMARY.md`.
4. Operator reviews via `phase_dashboard.html` (per-tab command bar, run/copy buttons, version history via `.versions/`).

### Journey C — Compliance and iteration
1. `compliance_checker.py` runs a 17-rule brand check automatically as part of the pipeline.
2. Operator can re-run any individual step (`/api/run-step`) and compare against `.versions/{step}/vN/` history without losing prior output.

## Future user journeys (scoped, not yet built — see `roadmap.md` for sequencing)

### Journey D — Raw-footage / B-roll video (Phase 1B)
Operator uploads a talking-head clip (`/api/upload-clip` already exists and is currently a dead end — nothing consumes the upload today). The system transcript-analyzes it, composites AI-generated or stock B-roll, and produces a seamless master render — same branding/compliance/platform-export pipeline as Journey B.

### Journey E — Viral clips from an existing video (Phase 1C)
Operator supplies a YouTube URL or existing MP4. The system finds the strongest 3–5 segments, brands them, and exports platform-shaped clips — reusing `platform_cutter.py` as-is.

### Journey F — Outcome-oriented "make me a video" (Phase 7)
Operator types one sentence ("make me a YouTube video about SpaceX"). A `ProjectOrchestrator` infers a `GoalTemplate`, asks 2–5 targeted questions only for what it can't infer from brand history, then runs the full hidden pipeline (research → script → storyboard → voice → music → B-roll → graphics → render → publish) unattended.

## Non-goals (explicitly out of scope for the current roadmap horizon)

- AI-generated fully synthetic talking-head/avatar video (HeyGen-style) — tracked as a future `AvatarEngine` interface, not part of Phase 1B.
- Live multi-camera or real-time/interactive editing.
- Multi-user collaboration or cloud rendering — blocked on the local-filesystem-as-truth model and no-auth API; both are explicit prerequisites, not afterthoughts (see `architecture.md` §4, CP7).
