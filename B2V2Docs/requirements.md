# requirements.md — Functional & Non-Functional Requirements (Priority 3)

## Functional requirements

### FR-1 — Brand management
- FR-1.1: Create/update a brand profile (colors, typography, tone, platforms, content pillars) via wizard or JSON import (`tools/init_brand.py`). **Implemented.**
- FR-1.2: Brand profile is the single input consumed by every downstream generation/render/compliance step — no step may hardcode brand-specific values. **Implemented, must be preserved.**

### FR-2 — Phase (content run) generation
- FR-2.1: Given `topic + outline`, generate: narration script, short-form script, subtitles, voiceover brief, music brief, infographic card specs + HTML, shot brief, `content_spec.json` (chapters/cut timings). **Implemented** (`generate_phase.py`).
- FR-2.2: Every generation step must succeed using **any one** of the configured LLM providers — no step may require one specific provider's key while another step tolerates its absence (see current bug, `architecture.md` §2, CP10). **Not yet fixed — required for Phase 1 of the roadmap.**
- FR-2.3: Run a 17-rule brand compliance check automatically as part of every phase run. **Implemented** (`compliance_checker.py`).

### FR-3 — Rendering
- FR-3.1: Assemble a final 1080p video from generated cards + voiceover + subtitles, with no camera footage required. **Implemented.**
- FR-3.2: Export the same content package into TikTok / Instagram / Twitter / LinkedIn shapes from one master render. **Implemented** (`platform_cutter.py`).
- FR-3.3: Exactly one authoritative rendering entry point per output type must exist once the `Renderer` interface lands (`architecture.md` §3/CP5) — the dashboard must not present two "does the same thing" render options with no guidance, as it does today.

### FR-4 — Raw-footage & B-roll (Phase 1B, not yet built)
- FR-4.1: Accept an uploaded talking-head/raw clip and actually use it in the final render (today `/api/upload-clip` stores the file and nothing else reads it).
- FR-4.2: Generate or fetch B-roll matching a brief (`clip_brief.md`, already generated and unconsumed) via a tiered free→cheap→paid provider chain.
- FR-4.3: Composite camera clips + B-roll + talking-head into one seamless master render (`FootageRenderer`).

### FR-5 — Viral clips trimmer (Phase 1C, not yet built)
- FR-5.1: Accept a YouTube URL or MP4 and identify 3–5 strong short-form segments.
- FR-5.2: Brand and export each segment via the existing `platform_cutter.py`, without duplicating its crop/export logic.

### FR-6 — Multi-platform publishing
- FR-6.1: Publish generated video/text to YouTube via OAuth. **Implemented.**
- FR-6.2: Generic platform publisher hook for other platforms. **Implemented, partial** — verify per-platform coverage before assuming a given platform is live.

### FR-7 — Version history
- FR-7.1: Every regenerated artifact must be snapshotted to `.versions/{step}/vN/` without deleting prior versions. **Implemented, must be preserved.**

## Non-functional requirements

### NFR-1 — Reliability / data integrity
- No pipeline step may report success (process exit 0) while producing a corrupt, partial, or mismatched-duration output. **Currently not guaranteed** — no self-evaluation loop exists (`ai/eval.py` is planned, not built). This is a Critical-priority gap (`roadmap.md` Phase 3).
- The filesystem under `youtube_scripts/setup/projects/` is the **source of truth**. Postgres (`db/db.py`) is a best-effort shadow index and must never be treated as authoritative when it disagrees with disk state.

### NFR-2 — Cost control
- Any paid API call (B-roll generation, voice cloning, cloud rendering) must be: (a) cost-capped with bounded retry (<3 attempts), (b) cached by input hash so an unchanged re-run does not re-purchase the same generation. **Hard requirement before FR-4.2 ships** — see CP3/CP4 in `architecture.md`.

### NFR-3 — Brand safety / non-interference
- No implementation work may modify or delete data under any of the four live brand directories (`chain_clarity`, `ecoWorld`, `loksewawithmanoj`, `manojsir`) as a side effect of development or testing. All demo/test runs use a disposable fixture brand (e.g. `_demo_brand`) and a scratch output directory.

### NFR-4 — Security (see `security.md` for full detail)
- The API has no authentication today; this is acceptable **only** for localhost-only use. Exposing the dashboard beyond localhost is blocked until CP7 (auth) is closed — treat this as a hard gate, not a soft recommendation, once real camera footage (a real person's face/voice) flows through `/api/upload-clip`.
- Path-traversal protection must be centralized (one shared guard function), not re-implemented per endpoint.

### NFR-5 — Extensibility
- A new AI provider, TTS engine, renderer, or platform publisher must be addable by implementing one of the plugin interfaces in `architecture.md` §3 — never by adding another `if/elif` branch to `server.py` or another disconnected top-level script.

### NFR-6 — Testability
- Every bug tracked in the historical Error Checklist (see `ARCHITECTURE_AUDIT.md`, repo root) must have a corresponding automated test before it is marked fixed. "It should be fixed" is not an accepted verification standard — see `roadmap.md`'s phase-gate rule.

### NFR-7 — Performance (qualitative — no formal SLA exists yet)
- A single phase run (script → compliance → render → platform cuts) should complete without operator babysitting on a single local machine for the content lengths currently in production (~10–12 min long-form). No numeric latency target is committed yet; establishing one is deferred until the job queue (CP3) exists and can report real timings.

### NFR-8 — Backward compatibility
- Every refactor must keep `pipeline.py`'s existing CLI flags and `tools/*.py`'s existing standalone invocation working unchanged, so existing operator muscle-memory commands are never broken (`architecture.md` §5).
