# Bhrikuty Film Director

<div align="center">

**AI-powered content factory — Brand → Script → Compliance → Video → 8-Platform Package**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green?style=flat-square&logo=node.js)](https://nodejs.org)
[![Claude API](https://img.shields.io/badge/Claude-Sonnet_4.6-orange?style=flat-square)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-blue?style=flat-square)](https://aistudio.google.com)
[![ChatGPT](https://img.shields.io/badge/ChatGPT-GPT--4o-green?style=flat-square)](https://openai.com)
[![Qwen](https://img.shields.io/badge/Qwen3-DashScope-purple?style=flat-square)](https://dashscope.aliyuncs.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue?style=flat-square&logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What is Bhrikuty Film Director?

Give it a **brand** and a **topic**. It produces a complete **8-platform content package** — YouTube video, TikTok clips, Instagram Reels, Twitter thread, LinkedIn article, blog post, GitHub README — all brand-compliant, generated in one pipeline run.

```
Brand Profile  →  Phase  →  Script + Cards + Audio + Video + Platform Cuts + Text
   (once)         (per video)                    (auto, no raw footage needed)
```

**Key capabilities:**
- Script, subtitles, infographic cards, voiceover, video — all from one topic
- Video generated from infographic cards + voiceover — **no camera or footage required**
- 17-rule brand compliance checker on every run
- Dashboard at `http://localhost:8080` — run every step from the browser
- AI fallback chain: Claude → Gemini → ChatGPT → Qwen3 (never blocked by one API failing)
- Unlimited phases per brand, PostgreSQL-backed run history

---

## Pipeline Overview

```
TOPIC + OUTLINE
      │
      ▼
┌──────────────────────────────────────────────────────────┐
│  pipeline.py  (orchestrator)                             │
│                                                          │
│  Step 1   generate_phase.py                              │
│    1.1 → script.md          (12-min narration)          │
│    1.2 → script_short.md    (60-sec TikTok cut)         │
│    1.3 → subtitles.srt      (auto-timed captions)       │
│    1.4 → voiceover_brief.md (pacing guide)              │
│    1.5 → music_brief.md     (BPM + mood)                │
│    1.6 → infographics.md    (card layout specs)         │
│    1.7 → clip_brief.md      (shot-by-shot guide)        │
│    1.8 → card_01.html …     (branded HTML cards)        │
│    1.9 → content_spec.json  (chapters + cut timings)    │
│                                                          │
│  Step 2   compliance_checker.py  → 17-rule report       │
│  Step 3   tools/tts/             → voiceover MP3        │
│  Step 4   tools/video/create_video.py → 1080p MP4      │
│  Step 5   text_content_generator → platform text        │
│  Step 6   platform_cutter.py     → TikTok/IG/Twitter…  │
└──────────────────────────────────────────────────────────┘
      │
      ▼
youtube_scripts/setup/projects/{brand}/_output/phase_NN/
  youtube/  youtube_shorts/  tiktok/  instagram/
  twitter/  linkedin/  blog/  github/
```

**AI fallback chain (automatic):**
```
Claude Sonnet 4.6  →  Gemini 2.5 Flash  →  ChatGPT GPT-4o  →  Qwen3 DashScope
```

---

## STEP 1 — Install Prerequisites

| Tool | Min version | Install command |
|------|-------------|----------------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| FFmpeg | 5+ | `winget install --id Gyan.FFmpeg -e` (Windows) |
| PostgreSQL | 15+ | https://postgresql.org (optional — file mode works without it) |

**Verify all four:**
```bash
python --version
node --version
ffmpeg -version
psql --version
```

**Restart your terminal** after installing FFmpeg so it appears in PATH.

---

## STEP 2 — Clone the Repository

```bash
git clone https://github.com/sanamsitoula/BhrikutyFlimDirector.git
cd BhrikutyFlimDirector
```

---

## STEP 3 — Set Up Environment Variables

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
# ── AI Providers (at least ONE required) ──────────────────────
ANTHROPIC_API_KEY=sk-ant-...       # claude.ai → API Keys (primary)
GEMINI_API_KEY=AIza...             # aistudio.google.com (free tier — auto-fallback)
OPENAI_API_KEY=sk-...              # platform.openai.com (optional)
DASHSCOPE_API_KEY=sk-...           # dashscope.aliyuncs.com (optional, freemium)

# ── Database (optional — dashboard works without PostgreSQL) ──
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bhrikutyflimdirector
DB_USER=postgres
DB_PASSWORD=your-password

# ── TTS / Voiceover ────────────────────────────────────────────
ELEVENLABS_API_KEY=                # elevenlabs.io (paid, best quality)
# DASHSCOPE_API_KEY already set above — also used for CosyVoice TTS
```

> **Minimum to start: just `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`** — everything else is optional.

---

## STEP 4 — Install Python Packages

```bash
python install.py
```

Or install manually:

```bash
pip install anthropic google-genai psycopg2-binary Pillow moviepy edge-tts
```

**Verify key packages:**
```bash
python -c "import anthropic; print('Claude OK')"
python -c "from PIL import Image; print('Pillow OK')"
python -c "import moviepy; print('MoviePy OK')"
```

| Package | Purpose | Required? |
|---------|---------|-----------|
| `anthropic` | Claude API for script generation | Yes (or Gemini) |
| `google-genai` | Gemini 2.5 Flash fallback | Recommended (free) |
| `Pillow` | Branded slide images for video | Yes |
| `moviepy` | Video compositing | For video assembly |
| `edge-tts` | Free Microsoft TTS (best for Python 3.14) | Recommended |
| `psycopg2-binary` | PostgreSQL | Optional |
| `elevenlabs` | ElevenLabs TTS (paid) | Optional |
| `playwright` | Full-quality HTML card screenshots | Optional |

---

## STEP 5 — Install Remotion (Animated Cards)

```bash
cd remotion
npm install
cd ..
```

**Verify:**
```bash
node remotion/node_modules/.bin/remotion --version
```

---

## STEP 6 — Set Up the Database (Optional)

Skip this step if you don't have PostgreSQL — the dashboard works in file-only mode.

```bash
# Apply schema
python db/migrate.py

# Sync existing projects to DB
python db/sync.py
```

All 17 schema migrations are idempotent — safe to re-run.

---

## STEP 7 — Start the Dashboard

```bash
python server.py
```

Open your browser: **http://localhost:8080**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Bhrikuty Film Director — Dashboard
  Open: http://localhost:8080
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> To use a different port: `$env:PORT=8081; python server.py` (PowerShell)

---

## STEP 8 — Create Your Brand

Go to **http://localhost:8080/brand** and click **+ New Brand**, or run:

```bash
python tools/init_brand.py \
  --slug ecoWorld \
  --name "Eco World" \
  --tagline "Economics, finally making sense." \
  --niche "Economics Education"
```

**What gets created:**
```
youtube_scripts/setup/projects/ecoWorld/
├── brand_profile.json       ← Colors, typography, tone, audience, pillars
├── brand_guidelines.md      ← Human-readable brand rules
├── roadmap.json             ← 5-phase content plan
├── phase_1/ … phase_5/
│   └── README.md            ← Production checklist per phase
└── _output/phase_01/ … phase_05/
```

---

## STEP 9 — Generate Your First Phase

### From the Browser (easiest)

1. Go to **http://localhost:8080**
2. Fill in **Step 1 — Topic & Outline**
3. Click through Steps 2–4 (keep defaults)
4. Click **▶ Run on Server** — live output streams in the terminal panel

### From the Terminal

```bash
python pipeline.py \
  --project ecoWorld \
  --phase 1 \
  --topic "Microeconomics Basics" \
  --outline "supply and demand, elasticity, market equilibrium" \
  --duration 12 \
  --tags "economics,micro,education"
```

**PowerShell (single line):**
```powershell
python pipeline.py --project ecoWorld --phase 1 --topic "Microeconomics Basics" --outline "supply, demand, prices" --duration 12
```

**Pipeline flags:**
```bash
--provider gemini        # force Gemini instead of Claude
--provider openai        # force ChatGPT
--skip-generate          # use existing files (skip AI generation)
--skip-voiceover         # skip TTS step
--skip-remotion          # skip Remotion card render
--skip-text              # skip text content generation
--video path/to/mp4      # provide existing video for platform cuts
```

**After 1–3 minutes, you get:**
```
phase_1/
├── script.md                  ← ~3,000 words, 12-min narration
├── script_short.md            ← ~400 words, 60-second TikTok cut
├── subtitles.srt              ← auto-timed captions
├── voiceover_brief.md         ← pacing + emphasis guide
├── clip_brief.md              ← 38 shot-by-shot instructions
├── music_brief.md             ← BPM, mood, genre guidance
├── infographics.md            ← card layout specs
├── content_spec.json          ← chapters, platform cuts, tags
├── compliance_report_auto.md  ← 17 brand rule checks
└── infographic_assets/
    ├── card_01.html
    ├── card_02.html
    └── card_03.html
```

---

## STEP 10 — Generate Single Files (Fine Control)

Generate any file individually without running the full pipeline:

```bash
# Seed file first — needs topic + outline
python tools/generate_phase.py --project ecoWorld --phase 1 \
  --topic "Microeconomics Basics" --outline "supply, demand, prices" \
  --only script.md

# All other files read script.md from disk — no topic/outline needed
python tools/generate_phase.py --project ecoWorld --phase 1 --only script_short.md
python tools/generate_phase.py --project ecoWorld --phase 1 --only subtitles.srt
python tools/generate_phase.py --project ecoWorld --phase 1 --only voiceover_brief.md
python tools/generate_phase.py --project ecoWorld --phase 1 --only music_brief.md
python tools/generate_phase.py --project ecoWorld --phase 1 --only infographics.md
python tools/generate_phase.py --project ecoWorld --phase 1 --only clip_brief.md
python tools/generate_phase.py --project ecoWorld --phase 1 --only card_01.html
python tools/generate_phase.py --project ecoWorld --phase 1 --only content_spec.json
```

---

## STEP 11 — Compliance Check

```bash
python tools/compliance_checker.py --project ecoWorld --phase 1
```

**17 checks enforced:**

| Check | Rule |
|-------|------|
| Tone of voice | Matches brand tone profile |
| Forbidden words | None of the banned words present |
| Sentence length | Max 15 words per sentence |
| Color codes | All hex colors match brand palette |
| Typography | Correct font CDN (Space Grotesk + Inter + JetBrains Mono) |
| Subtitle length | Max 7 words per line |
| SRT format | Valid subtitle file format |
| Animation sequence | `fadeIn 0.2s` → `slideDown 0.3s` → `wordIn 0.15s` → `slideUp 0.4s` → `bounce 0.3s` |
| Card dimensions | 1080×1080px (Instagram square) |
| Sound identity | Matches brand BPM/mood |
| Brand hashtags | Required hashtags included |
| Investment advice | No "guaranteed returns" or similar |
| + 5 more | … |

Status: **PASS** / **PASS_WITH_WARNINGS** / **FAIL**

View in browser: `http://localhost:8080/phase/ecoWorld/1` → **✅ Compliance** tab

---

## STEP 12 — Voiceover (Audio)

Choose one option:

### Voice Selector (from browser — easiest)

Open the phase dashboard → **Audio tab** → pick a voice from the voice grid → click **▶ Generate**.

| Group | Voices |
|-------|--------|
| 🇳🇵 South Asian / Nepali Male ⭐ | `en-IN-PrabhatNeural` (default), `ne-NP-SagarNeural` (native Nepali), `hi-IN-MadhurNeural` (Hindi) |
| 🌍 Other Male | `en-US-GuyNeural`, `en-GB-RyanNeural`, `en-SG-WayneNeural` |
| 🎤 Female | `en-US-JennyNeural`, `en-GB-SoniaNeural`, `en-AU-NatashaNeural`, `en-IN-NeerjaNeural` |

Selected voice is saved in browser localStorage per project+phase.

### Option A — Edge TTS (Free, recommended, works on Python 3.14)

```bash
pip install edge-tts
python tools/tts/edge_tts_voiceover.py --project ecoWorld --phase 1

# List all 300+ voices
python tools/tts/edge_tts_voiceover.py --list-voices

# Pick a voice
python tools/tts/edge_tts_voiceover.py --project ecoWorld --phase 1 --voice en-GB-RyanNeural
```

| Voice | Style |
|-------|-------|
| `en-US-JennyNeural` (default) | Warm, clear — great for education |
| `en-US-GuyNeural` | Professional male narrator |
| `en-GB-RyanNeural` | Deep documentary-style |
| `en-AU-NatashaNeural` | Friendly Australian |

### Option B — DashScope CosyVoice 2.0 (Freemium)

```bash
# Deploy CosyVoice 2.0 first:
# modelstudio.console.alibabacloud.com → Model Square → CosyVoice 2.0 → Deploy

# Verify deployment
python tools/tts/dashscope_voiceover.py --discover

# Generate
python tools/tts/dashscope_voiceover.py --project ecoWorld --phase 1
```

### Option C — ElevenLabs (Paid, best quality)

```bash
# Add ELEVENLABS_API_KEY to .env
python tools/tts/elevenlabs_voiceover.py --project ecoWorld --phase 1
```

### Option D — Manual recording

1. Open `phase_1/script.md`, read `NARRATION:` sections aloud
2. Record with Audacity at 44.1 kHz
3. Save to `phase_1/voiceover/phase_1.wav`
4. Dashboard detects it automatically — Audio tab shows player

### Option E — Browser preview (instant, no install)

Open phase dashboard → **Audio tab** → click **▶ Play Script**
Browser Web Speech API reads your script aloud — good for pacing checks.

**Output:** `phase_1/voiceover/phase_1.mp3`

---

## STEP 13 — Video Assembly

Build a complete 1080p video from infographic cards + voiceover — **no raw footage or camera needed**.

```bash
python tools/video/create_video.py \
  --project ecoWorld \
  --phase 1 \
  --burn-subs \
  --shorts
```

**What it does:**
1. Reads the 3 HTML infographic cards
2. Renders each as a 1920×1080 PNG (via Playwright if installed, else Pillow branded slides)
3. Animates each with a ken-burns slow zoom + fade in/out
4. Concatenates all card clips
5. Mixes in the voiceover MP3
6. Burns subtitles (with `--burn-subs`)
7. Exports 1920×1080 YouTube version
8. Crops to 1080×1920 Shorts version (with `--shorts`)

**Video generation tools available (shown in Video tab):**

| Tool | Input | Output | Requires |
|------|-------|--------|---------|
| `create_video.py` | HTML cards + voiceover | 1080p MP4 + Shorts 9:16 | FFmpeg + Pillow |
| `platform_cutter.py` | Master 1080p MP4 | TikTok/IG/Twitter/LinkedIn | FFmpeg |
| Text-Overlay Video | Script text | Animated text frames MP4 | FFmpeg + Pillow |
| Playwright screenshots | HTML cards | Full-quality PNGs | Playwright + Chromium |

**Install Playwright for best card quality (optional):**
```bash
pip install playwright
playwright install chromium
```
With Playwright, cards are rendered with full CSS animations and custom fonts.
Without it, Pillow draws clean branded slides automatically.

**Output:**
```
_output/phase_01/
├── youtube/final_1080p.mp4          ← 1920×1080 YouTube
└── youtube_shorts/short_1080x1920.mp4  ← 9:16 Shorts
```

---

## STEP 14 — Auto-Transcribe Subtitles (Improve Accuracy)

The generated `subtitles.srt` is AI-estimated. For word-accurate timing after voiceover:

```bash
python tools/transcribe.py --phase 1 --engine faster-whisper
```

**Output:** `phase_1/subtitles_auto.srt` — real word-level timestamps

---

## STEP 15 — Text Content Generation

```bash
python tools/text_content_generator.py --project ecoWorld --phase 1
```

**Generates:**

| File | Platform | Content |
|------|----------|---------|
| `youtube/description.txt` | YouTube | SEO description + timestamps + tags |
| `twitter/thread.txt` | Twitter/X | 7-tweet thread with hook + CTA |
| `linkedin/article.md` | LinkedIn | 800-word professional article |
| `blog/post.md` | Blog | 1,500-word SEO post |
| `instagram/caption_reel.txt` | Instagram | Caption + 15 hashtags |
| `github/README.md` | GitHub | Project README with embed |

Auto-falls back to Gemini when Anthropic credits run low.

---

## STEP 16 — Platform Cuts

Requires FFmpeg and the assembled 1080p video from Step 13.

```bash
python tools/platform_cutter.py \
  --project ecoWorld \
  --phase 1 \
  --video _output/phase_01/youtube/final_1080p.mp4
```

**Output:**
```
_output/phase_01/
├── youtube/        final_1080p.mp4  description.txt  subtitles.srt
├── youtube_shorts/ short_1080x1920.mp4
├── tiktok/         clip_01_hook.mp4 (:15)  clip_02_main.mp4 (:60)
├── instagram/      reel_60s.mp4  carousel_1-3.png
├── twitter/        card_clip.mp4 (:30)  thread.txt
├── linkedin/       clip.mp4 (:45)  article.md
├── blog/           post.md
└── github/         README.md
```

---

## STEP 17 — Adding More Phases

### From Projects page

1. Go to **http://localhost:8080/projects**
2. Expand a brand accordion
3. Click **➕ New Phase** — scaffolds the folder + registers in DB + opens dashboard pre-filled

### From the terminal

```bash
python pipeline.py --project ecoWorld --phase 7 \
  --topic "Game Theory Basics" \
  --outline "Nash equilibrium, prisoner's dilemma, zero-sum games"
```

Phases are numbered dynamically — there is **no limit**. The Projects page shows them newest-first (descending order).

---

## STEP 18 — View Everything in the Browser

| URL | What it shows |
|-----|--------------|
| `http://localhost:8080` | Main dashboard + New Video Project form |
| `http://localhost:8080/projects` | All brands + phases (newest first) |
| `http://localhost:8080/brand` | Create / edit brand |
| `http://localhost:8080/phase/ecoWorld/1` | Phase 1 detail — all 10 tabs |
| `http://localhost:8080/phase/ecoWorld/2` | Phase 2 detail |

### Phase Dashboard Tabs

| Tab | Content |
|-----|---------|
| **Overview** | Video type selector, TTS guide, YouTube chapters, platform cuts, tags |
| **Script** | `script.md` viewer + inline editor |
| **Short Script** | `script_short.md` — 60-second cut |
| **Infographics** | HTML card previews + URLs + open full-size |
| **Subtitles** | `subtitles.srt` with color-coded timestamps |
| **Audio** | Voiceover player + upload + browser preview |
| **Video** | YouTube player + Shorts player + clips folder + tool panel |
| **Compliance** | 17-rule report: PASS / WARN / FAIL per rule |
| **All Files** | File browser with inline viewer + editor |
| **📤 Outputs** | All 8 platform outputs — each with **▶ Run** button |
| **📋 Context** | Brand identity + Copy Prompt for AI tools |

---

## STEP 19 — Publish Checklist

```bash
# Check the pipeline summary
cat youtube_scripts/setup/projects/ecoWorld/_output/phase_01/PIPELINE_SUMMARY.md

# Or view in browser
# http://localhost:8080/phase/ecoWorld/1  →  📤 Outputs tab
```

Upload files from `_output/phase_01/` to each platform manually.

---

## Daily Workflow (After First Setup)

```bash
# 1. Start the server
python server.py

# 2. Open browser
# http://localhost:8080

# 3. Create new phase (full pipeline)
python pipeline.py --project ecoWorld --phase 2 \
  --topic "Your Topic" --outline "point 1, point 2, point 3"

# 4. Generate voiceover
python tools/tts/edge_tts_voiceover.py --project ecoWorld --phase 2

# 5. Build video
python tools/video/create_video.py --project ecoWorld --phase 2 --burn-subs --shorts

# 6. Check compliance
python tools/compliance_checker.py --project ecoWorld --phase 2

# 7. Generate text content
python tools/text_content_generator.py --project ecoWorld --phase 2

# 8. Cut for all platforms
python tools/platform_cutter.py --project ecoWorld --phase 2 \
  --video _output/phase_02/youtube/final_1080p.mp4
```

---

## Step Versioning — Re-run Without Losing Old Files

Every time you re-run a pipeline step from the dashboard (voiceover, video, platform cuts, etc.), the **old output is backed up automatically** before the new run starts. No data is ever deleted.

### How it works

```
phase_1/
├── voiceover/
│   └── phase_1.mp3          ← always the latest run
└── .versions/
    └── voiceover/
        ├── v1/              ← first run (backed up before v2 overwrote it)
        │   └── voiceover/
        │       └── phase_1.mp3
        └── v2/              ← second run (backed up before v3 overwrote it)
            └── voiceover/
                └── phase_1.mp3
```

### In the Dashboard

Each step row shows a **📁 N versions** badge when older versions exist. Click it to open the **Version History** panel showing every version with:
- Version number (v1, v2, v3…)
- Timestamp of when it was created
- File list with sizes
- Path for manual access

### Steps that are versioned

| Step | Step key | What is backed up |
|------|----------|-------------------|
| TTS / Voiceover | `voiceover` | `voiceover/` directory |
| Video Assembly | `video` | `_output/youtube/`, `_output/youtube_shorts/` |
| Platform Cuts | `platform` | `_output/tiktok/`, `instagram/`, `twitter/`, `linkedin/` |
| Text Content | `text` | `_output/blog/`, `_output/github/` |
| Script Generation | `script` | `script.md`, `subtitles.srt`, cards, etc. |
| Compliance | `compliance` | `compliance_report_auto.md` |

### API

```bash
# List all versions for a phase
GET /api/file-versions?project=ecoWorld&phase=1

# List versions for a specific step
GET /api/file-versions?project=ecoWorld&phase=1&step=voiceover
```

### PostgreSQL

Every version is also recorded in the `asset_versions` table:

```sql
SELECT version, file_name, media_url, file_size, created_at
FROM asset_versions
WHERE brand_slug = 'ecoWorld' AND phase_num = 1 AND step_key = 'voiceover'
ORDER BY version DESC;
```

---

## Debug & Diagnostics

```bash
# Full system check (FFmpeg, Python deps, Node, Remotion, project structure)
python tools/debug_pipeline.py

# FFmpeg deep test (10 operations: encode, cut, concat, scale, subtitles, audio)
python tools/debug_ffmpeg.py

# One-click full debug suite
tools\run_debug.bat        # Windows
./tools/run_debug.sh       # Mac / Linux
```

**Reports saved to:**
- `debug_report.md` — full system report
- `_debug_test/remotion_output/remotion_report.json` — Remotion specific

---

## API Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/brands` | List all brands |
| POST | `/api/brands` | Create brand (full scaffold) |
| GET | `/api/brands/{slug}` | Single brand profile |
| PUT | `/api/brands/{slug}` | Update brand profile |
| GET | `/api/phase-data?project=X&phase=N` | Full phase data (steps, files, cards, clips, brand) |
| GET | `/api/file?project=X&phase=N&file=Y` | Read a phase file |
| POST | `/api/save-file` | Save / create a phase file |
| POST | `/api/create-phase` | Scaffold new phase dir + register in DB |
| POST | `/api/run` | Start full pipeline job |
| POST | `/api/run-step` | Run single tool (`cmd_type`: generate / create_video / platform_cut / text_content / tts / compliance) |
| GET | `/api/jobs/{id}/stream` | Live output SSE stream |
| POST | `/api/upload-audio` | Upload voiceover file → `phase_N/voiceover/` |
| POST | `/api/upload-clip` | Upload raw video clip → `phase_N/clips/` |
| GET | `/api/tools-status` | Which AI/TTS/image tools are configured |
| GET | `/api/projects/{slug}/summary` | Phase progress summary |
| GET | `/api/projects/{slug}/runs` | Pipeline run history (DB) |
| GET | `/api/db-status` | PostgreSQL availability |
| GET | `/api/db-sync?brand=X` | Sync filesystem → PostgreSQL |

---

## Project Structure

```
BhrikutyFlimDirector/
│
├── install.py                       ← One-time setup
├── pipeline.py                      ← CLI pipeline runner
├── server.py                        ← Dashboard HTTP server (port 8080)
├── .env                             ← API keys (never commit)
├── .env.example                     ← Template
├── requirements.txt
│
├── db/
│   ├── db.py                        ← PostgreSQL helper (graceful fallback)
│   ├── migrate.py                   ← Apply schema (17 migrations)
│   ├── sync.py                      ← Sync filesystem → DB
│   └── schema.sql                   ← DDL reference
│
├── tools/
│   ├── init_brand.py                ← Brand scaffold
│   ├── generate_phase.py            ← Content generation (--only flag)
│   ├── compliance_checker.py        ← 17-rule brand compliance
│   ├── platform_cutter.py           ← FFmpeg platform video exports
│   ├── text_content_generator.py    ← Platform text (Gemini fallback)
│   ├── debug_pipeline.py            ← Full system diagnostic
│   ├── debug_ffmpeg.py              ← FFmpeg deep test (10 ops)
│   ├── run_debug.bat                ← Windows debug runner
│   ├── run_debug.sh                 ← Mac/Linux debug runner
│   ├── video/
│   │   ├── create_video.py          ← Cards + voiceover → 1080p MP4 (Pillow slides)
│   │   └── setup_remotion.py
│   └── tts/
│       ├── edge_tts_voiceover.py    ← Free, no key, Python 3.14+ ⭐
│       ├── dashscope_voiceover.py   ← DashScope CosyVoice (deploy first)
│       ├── elevenlabs_voiceover.py  ← Paid, best quality
│       ├── chatterbox_voiceover.py  ← Free, GPU required
│       └── kokoro_voiceover.py      ← Free CPU, Python ≤3.12
│
├── dashboard.html                   ← Main pipeline UI
├── projects.html                    ← Projects browser (phases newest-first)
├── brand.html                       ← Brand creation / editing
├── phase_dashboard.html             ← Per-phase detail (10 tabs)
│
├── remotion/                        ← Animated card renderer (Node.js)
│   ├── src/
│   ├── scripts/
│   │   └── debug_render.js          ← Remotion diagnostic
│   └── package.json
│
└── youtube_scripts/setup/projects/
    └── {brand_slug}/
        ├── brand_profile.json
        ├── roadmap.json
        ├── phase_N/
        │   ├── script.md
        │   ├── script_short.md
        │   ├── subtitles.srt
        │   ├── voiceover_brief.md
        │   ├── music_brief.md
        │   ├── infographics.md
        │   ├── clip_brief.md
        │   ├── content_spec.json
        │   ├── compliance_report_auto.md
        │   ├── video_type.json       ← B-Roll / Screen / Animation / Manual
        │   ├── voiceover/            ← TTS audio files
        │   │   └── phase_N.mp3
        │   ├── clips/                ← Raw source clips (screen recordings, b-roll)
        │   │   └── clip_01.mp4
        │   └── infographic_assets/
        │       ├── card_01.html
        │       ├── card_02.html
        │       ├── card_03.html
        │       └── cards_manifest.json
        └── _output/phase_NN/
            ├── youtube/              final_1080p.mp4  description.txt
            ├── youtube_shorts/       short_1080x1920.mp4
            ├── tiktok/               clip_01_hook.mp4  clip_02_main.mp4
            ├── instagram/            reel_60s.mp4  carousel_1-3.png
            ├── twitter/              card_clip.mp4  thread.txt
            ├── linkedin/             clip.mp4  article.md
            ├── blog/                 post.md
            ├── github/               README.md
            └── PIPELINE_SUMMARY.md
```

---

## TTS Engine Comparison

| Engine | Cost | Python 3.14 | API Key | Notes |
|--------|------|-------------|---------|-------|
| **Edge TTS** ⭐ | Free | ✅ | None | 300+ Microsoft neural voices |
| DashScope CosyVoice 2.0 | Freemium | ✅ | `DASHSCOPE_API_KEY` | Deploy model first in workspace |
| ElevenLabs | $5–22/mo | ✅ | `ELEVENLABS_API_KEY` | Best quality, voice cloning |
| Chatterbox | Free | Manual | None | GPU required, emotion control |
| Kokoro | Free | ❌ | None | CPU only, Python ≤3.12 |

---

## Database

```bash
# Apply schema
python db/migrate.py

# Sync projects to DB
python db/sync.py

# Check DB status in dashboard
http://localhost:8080/tools   # → Database section
```

```sql
-- Phase status
SELECT phase_num, topic, status, updated_at
FROM phases WHERE brand_slug = 'ecoWorld' ORDER BY phase_num DESC;

-- Pipeline run history
SELECT run_id, phase_num, status, started_at
FROM pipeline_runs WHERE brand_slug = 'ecoWorld' ORDER BY started_at DESC;

-- Compliance history
SELECT phase_num, overall_status, checked_at
FROM compliance_logs WHERE brand_slug = 'ecoWorld';
```

**Tables:** `brands` · `phases` · `pipeline_runs` · `pipeline_steps` · `generated_files` · `compliance_logs` · `content_specs`

---

## Troubleshooting

**`ffmpeg not found`**
```bash
winget install --id Gyan.FFmpeg -e   # Windows (restart terminal after)
brew install ffmpeg                   # Mac
```

**`No module named 'PIL'`**
```bash
pip install Pillow
```

**`ModuleNotFoundError: No module named 'anthropic'`**
```bash
pip install anthropic
```

**Anthropic 400 / credits exhausted**
→ Automatic fallback to Gemini. Get a free key at `aistudio.google.com`.

**Gemini 429 rate limit**
→ Auto-handled — waits the suggested retry delay and retries up to 6 times.

**Video generation fails (CalledProcessError on FFmpeg drawtext)**
→ Fixed: `create_video.py` now uses Pillow for slide rendering — no font-path issues on Windows.

**DashScope TTS: "Model not exist" (404)**
→ CosyVoice is not deployed. Go to `modelstudio.console.alibabacloud.com` → Model Square → CosyVoice 2.0 → Deploy.
→ Check: `python tools/tts/dashscope_voiceover.py --discover`

**No audio showing in Audio tab**
→ Files must be in `phase_N/voiceover/` with `.wav`, `.mp3`, or `.ogg` extension.

**New Phase button not redirecting correctly**
→ Make sure `server.py` is running. The button calls `/api/create-phase` before redirecting.

**Port 8080 in use**
```powershell
$env:PORT=8081; python server.py
```

**`database does not exist`**
```bash
python install.py --db   # creates DB and applies schema
```

**Card compliance fails (JetBrains Mono / animation timings)**
→ Add `--font-code: 'JetBrains Mono', monospace;` to `:root` in card CSS.
→ Animation timings must match exactly: `fadeIn 0.2s` · `slideDown 0.3s` · `wordIn 0.15s` · `slideUp 0.4s` · `bounce 0.3s`.

**Run the full diagnostic:**
```bash
python tools/debug_pipeline.py
```

---

## Git Workflow

```bash
# 1. Clone
git clone https://github.com/sanamsitoula/BhrikutyFlimDirector.git
cd BhrikutyFlimDirector

# 2. Create a feature branch
git checkout -b feat/my-brand

# 3. Stage + commit
git add server.py tools/ phase_dashboard.html dashboard.html projects.html README.md
git commit -m "feat: add ecoWorld brand with phase 1 content"

# 4. Push
git push -u origin feat/my-brand
```

| Prefix | Use for |
|--------|---------|
| `feat:` | New brand, phase, or feature |
| `fix:` | Bug fix |
| `docs:` | README updates |
| `chore:` | Dependencies, cleanup |

---

## Minimum Cost to Run

| Stage | Free Option | Paid Option |
|-------|------------|-------------|
| Script generation | Gemini free tier | Claude API ~$0.05/script |
| Voiceover | Edge TTS (free, CPU) | ElevenLabs $5/mo |
| Transcription | faster-whisper (local) | AssemblyAI $0.03/video |
| Slides / Cards | Pillow (free, built-in) | Playwright HTML screenshots (free) |
| Video rendering | FFmpeg + create_video.py (free) | — |
| B-roll | None (infographic-only pipeline) | Kling AI $7.99/mo |
| Text content | Gemini free tier | Claude API |

**Minimum to start: $0** — Gemini free credits + Edge TTS + Pillow + FFmpeg covers the entire pipeline end-to-end.

---

*Bhrikuty Film Director — Built with ❤️ for the open source community*
*https://github.com/sanamsitoula/BhrikutyFlimDirector*
