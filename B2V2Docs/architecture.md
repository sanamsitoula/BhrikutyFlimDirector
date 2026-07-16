# architecture.md — System Architecture (Priority 1)

**Status of this document**: describes the system **as it exists today** (AS-IS) and the **target module boundary** (TO-BE, "Bhrikuty 2.0") that all new work should move toward. Every future architectural decision is checked against this file first. Nothing here authorizes deleting a currently-working code path — see "Nothing is deleted" at the end.

---

## 1. What the system is

Bhrikuty Film Director is a **single-operator content factory**: given a brand profile and a topic, it produces a script, subtitles, branded infographic cards, a voiceover, a rendered video, and an 8-platform content package (YouTube, Shorts, TikTok, Instagram, Twitter, LinkedIn, blog, GitHub). It is in production today with four live brands under `youtube_scripts/setup/projects/` (`chain_clarity`, `ecoWorld`, `loksewawithmanoj`, `manojsir`).

## 2. AS-IS architecture

```
BhrikutyFlimDirector/
├── server.py            # 1,715 lines — HTTP server + ALL routes + dashboard logic + business logic
├── pipeline.py           # ~372 lines — CLI orchestrator; shells out to tools/*.py as separate OS processes
├── install.py            # setup/bootstrap (pip/npm installs, schema apply) — duplicates config logic
├── db/                   # optional PostgreSQL shadow index (db.py, schema.sql, migrate.py, sync.py)
├── tools/                # ~15 independent CLI scripts, no shared package structure
│   ├── generate_phase.py         # AI script/content generation (Claude → Gemini → Qwen fallback, per-script)
│   ├── compliance_checker.py     # 17-rule brand compliance (rule-based, not LLM)
│   ├── platform_cutter.py        # ffmpeg cuts for TikTok/IG/Twitter/LinkedIn
│   ├── text_content_generator.py # blog/twitter/linkedin/github text
│   ├── init_brand.py             # manual brand onboarding wizard
│   ├── video/create_video.py     # ffmpeg + Playwright card-to-slideshow assembly
│   ├── video/remotion_composer.py # stitches MP4 scenes from an EXTERNAL sibling project (see below)
│   ├── tts/                      # 5 parallel TTS engine scripts (kokoro, elevenlabs, dashscope, edge, chatterbox)
│   ├── publish/                  # YouTube + generic platform publishers (OAuth)
│   ├── research/apify_trends.py  # raw social-scraping data, no synthesis step
│   └── social_apis/              # vendored third-party repo with its OWN nested .git (anti-pattern)
├── remotion/             # Node/TS sub-project — renders ONLY infographic-card Ken-Burns slideshow to PNG
├── youtube_scripts/setup/projects/{brand}/  # ALL PERSISTENT STATE — filesystem is source of truth
│   └── phase_N/{script.md, subtitles.srt, content_spec.json, voiceover/, clips/, .versions/}
├── dashboard.html, projects.html, brand.html, tools.html, phase_dashboard.html  # static frontend, no framework
└── .env / .env.example   # ~20 flat env vars, 3 separately hand-rolled parsers
```

### Classification

- **Not layered / not DDD / not modular.** `server.py` mixes HTTP transport, routing, business logic (regex parsing of scripts/infographics, compliance status), and persistence access in one file.
- **No shared domain model.** A "brand," "phase," or "pipeline run" exists only as a JSON blob on disk or a row shape in `db/db.py` — no Python class represents any of them.
- **Orchestration = subprocess chaining**, not function calls. `pipeline.py` launches each `tools/*.py` script as a separate OS process via `subprocess.run`. This buys crash isolation at the cost of shared in-memory state, typed interfaces, and per-step Python startup cost.
- **Dual, best-effort persistence.** The filesystem (`phase_N/*.md|json`, `.versions/`) is the real source of truth. PostgreSQL (`db/db.py`) is a shadow index — every write is wrapped in `try/except: pass`, so it can silently drift from disk state. `db/sync.py` is a manual patch, not an enforced invariant.
- **Three disconnected video-rendering paths** coexist with no owning contract:
  1. `create_video.py` — Playwright screenshot of HTML cards → ffmpeg cross-fade + audio + subtitles. Does not use this repo's Remotion project.
  2. `remotion_composer.py` — stitches pre-rendered MP4 scenes from `D:\claude_project\LearnRemotion\out`, a **sibling project outside this repo** (overridable via `REMOTION_OUT_DIR`).
  3. `remotion/` (this repo's own Node project) — renders only static card PNGs, consumed by path 1.

  The dashboard exposes `create_video` and `remotion_compose` as if interchangeable `cmd_type`s with no guidance on which to use when. **This is a real architectural seam, not a naming issue — treat it as such in any rendering work.**

### Confirmed structural risks (do not repeat these patterns in new code)

- `.env` loader and the Claude→Gemini→Qwen provider-fallback chain are each independently reimplemented in `server.py`, `pipeline.py`, and `generate_phase.py`.
- `pipeline.py`'s Step 5 gate is hardcoded to `"ANTHROPIC_API_KEY" in os.environ` rather than "is any provider configured" — a confirmed bug (tracked as E10 in the historical audit), not a design choice to imitate.
- Path-traversal guards (`if any(c in filename for c in ("../", "..\\", "/", "\\"))`) are hand-rolled per-endpoint in `server.py` rather than centralized.

## 3. TO-BE architecture (Bhrikuty 2.0 — target module boundary)

**Principle: preserve every working code path.** New work introduces module boundaries and plugin seams *around* existing logic — it does not require deleting or rewriting a currently-working script in one pass.

```
api/            thin HTTP layer — routes only, no business logic
  routes: brands, phases, jobs, media

core/           extracted business logic (the "domain" today's code doesn't have)
  brand.py      — Brand model (currently a JSON blob)
  phase.py      — Phase/PipelineRun model
  queue.py      — durable job queue (replaces unbounded threading.Thread)
  config.py     — the ONE env/config loader (replaces 3 duplicated parsers)

ai/             the ONLY layer that calls an LLM
  providers.py  — LLMProvider interface: complete(prompt, system_prompt) -> str
                  implementations: Anthropic, OpenAI/Codex, Qwen/DashScope, MiniMax, Gemini
                  selected by an ordered config preference list, NOT per-step env-var checks
  prompts/      — script, subtitles, compliance-adjacent, text-content templates
  eval.py       — bounded self-check loop (generate → eval → retry, <3 loops), currently absent

research/       (optional, additive — manual --topic/--outline path is unaffected)
  deep_research.py — ResearchProvider: idea -> sourced topic+outline

render/         plugin seam — ALL video assembly goes through one Renderer contract
  Renderer interface: render(spec) -> Path
  remotion_renderer.py   — wraps existing remotion/ card path (default)
  ffmpeg_assembler.py    — wraps existing create_video.py (default)
  footage_renderer.py    — NEW: camera clips + B-roll + talking-head compositing
  hyperframes_renderer.py / huashu_renderer.py — optional plugins

footage/        (new — only needed once raw-footage editing ships)
  footage_editor.py, clip_sourcer.py, highlight_detector.py, broll/ (BRollProvider)

tts/            TTSEngine plugins — wraps existing 5 engines + optional OpenVoice cloning

audiovis/       MusicProvider, BackgroundMatteProvider (Phase 1D-scoped, currently unimplemented)

publish/        wraps existing tools/publish/* — Publisher interface

db/             UNCHANGED schema, formalized as an explicit filesystem-is-truth / Postgres-is-index contract
```

### Enforced dependency direction

```
api/ → core/ → { ai/, render/, publish/, footage/, tts/, audiovis/ } → db/
```

Nothing in `core/`, `ai/`, `render/`, `footage/`, `tts/`, `audiovis/`, or `publish/` may import from `api/`. This single rule, once enforced (by import-linting in CI once it exists), prevents `server.py`'s current problem: business logic that is only reachable by going through the HTTP handler.

### Plugin interfaces (the extensibility contract)

Any new engine, provider, or platform is added by implementing **one of these interfaces** — never by adding another `if/elif` branch to `server.py` or another top-level script in `tools/`.

| Interface | Signature | Existing implementations (wrapped, unchanged behavior) | New implementations land here |
|---|---|---|---|
| `Renderer` | `render(spec) -> Path` | `RemotionRenderer`, `FfmpegAssembler` | `FootageRenderer`, `HyperFramesRenderer`, `HuashuRenderer` |
| `TTSEngine` | `synthesize(text, brand_voice) -> Path` | Kokoro, ElevenLabs, DashScope, EdgeTTS, Chatterbox | `OpenVoiceEngine` (cloning) |
| `Publisher` | `publish(platform, asset) -> PublishResult` | YouTube, generic platform publishers | — |
| `LLMProvider` | `complete(prompt, system_prompt) -> str` | Anthropic, Gemini, Qwen/DashScope | OpenAI/Codex, MiniMax |
| `ResearchProvider` | `research(idea) -> Brief` | — (none exist yet) | `DeepResearchProvider` |
| `BRollProvider` | `generate_broll(prompt, duration, style) -> Path` | — (`.env.example` keys cataloged, never implemented) | Pexels/Pixabay (free), StableVideoDiffusion (free), Kling (cheap), Runway (paid) |
| `MusicProvider` | `generate_or_fetch(brief) -> Path` | Two tiers implemented side by side in Phase 1 (`tools/audio/music_provider.py`), per `coding-rules.md` RULE 0 — neither replaces the other: **Tier A — Manual** (operator downloads a track themselves, e.g. from Pixabay Music at pixabay.com/music/ — Pixabay has no public Music/Audio search API, verified against pixabay.com/api/docs/, so this is a manual-drop tier, not an API integration — file goes in `phase_N/music/manual/`, checked first); **Tier B — Jamendo** (developer.jamendo.com, real documented tracks-search API, automated fallback when no manual file is present) | MusicGen (free), Mubert/Soundraw (cheap), AIVA (paid) |
| `BackgroundMatteProvider` | `replace_background(clip, target) -> Path` | — | RVM/MediaPipe (free), remove.bg (cheap), Runway (paid) |
| `FootageEditor` | `edit(clips, transcript) -> EDL` | — | transcript-first silence/filler-cut editor (video-use pattern) |
| `ClipSourcer` | `fetch(url_or_path) -> RawFootage` | reuses existing `/api/upload-clip` | yt-dlp-based YouTube fetch |
| `HighlightDetector` | `find_clips(transcript, footage) -> List[ClipCandidate]` | — (genuinely new capability, no prior code) | heuristic pass + LLM re-rank |

A capability is not "done" until it: (a) implements one of these interfaces rather than a bespoke script, (b) has an automated test, (c) has its prerequisite choke point (below) independently reverified closed.

## 4. Choke points — must close before the corresponding new capability is added

| # | Choke point | Blocks |
|---|---|---|
| CP1 | No shared config/provider-fallback library | Any new LLM/engine — would duplicate the pattern a 10th time |
| CP2 | Subprocess-chaining with file-only handoffs | Iterative/stateful footage-editing loops |
| CP3 | No job queue, unbounded daemon threads | **Hard blocker before any paid B-roll/voice API** — cost/runaway-spend risk |
| CP4 | No render/generation cache | Re-running a phase would silently re-purchase paid B-roll/voice already generated once |
| CP5 | No single `Renderer` contract (3 disconnected paths today) | A 4th uncoordinated rendering path (`FootageRenderer`) repeating the same problem |
| CP6 | No visual/self-evaluation loop | Silent shipping of broken footage/B-roll composites (larger failure surface than card slideshows) |
| CP7 | No auth on the API, including `/api/upload-clip` | Exposing real camera footage/faces beyond localhost |
| CP8 | Compliance checking is text/color-rule only | Cannot verify B-roll/talking-head clips against brand guidelines |
| CP9 | `.env.example` documents unimplemented keys, omits required ones | Ambiguity between "real" and "aspirational" config for anyone extending the system |
| CP10 | LLM provider selection hardcoded per-step (`ANTHROPIC_API_KEY` check) | Every new provider added on top inherits the same per-step gating bug |
| CP11 | No highlight/virality-scoring capability | The viral-clips requirement — this is a genuinely new capability, not a rewire |
| CP12 | No intake/orchestration layer in front of the plugin system | The outcome-oriented "one input, many outputs" product experience (Phase 7 of the roadmap) |

## 5. "Nothing is deleted" rule

Every existing working code path — `create_video.py`, `pipeline.py`'s CLI, `tools/*.py`'s CLI entry points, the dashboard's phase-by-phase manual flow — **stays available** through the TO-BE architecture. New modules **wrap** existing scripts as their first (default) plugin implementation; they do not replace them. The four live brands' existing runs must continue to work unmodified throughout any refactor.

## 6. When this document conflicts with a request

If a requested implementation would violate the dependency direction in §3, duplicate a pattern flagged in §2, or delete a working path in violation of §5 — **stop and explain the conflict** before implementing. Do not silently choose an interpretation.
