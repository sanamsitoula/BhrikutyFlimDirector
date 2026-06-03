# Bhrikuty Film Director

<div align="center">

**AI-powered content factory — Brand → Project → 7-Platform Content Package**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green?style=flat-square&logo=node.js)](https://nodejs.org)
[![Claude API](https://img.shields.io/badge/Claude-Sonnet_4.6-orange?style=flat-square)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-blue?style=flat-square)](https://aistudio.google.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue?style=flat-square&logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open_Source-❤️-red?style=flat-square)](https://github.com/sanamsitoula/BhrikutyFlimDirector)

</div>

---

## What is Bhrikuty?

Give it a **topic**. It produces a complete **7-platform content package** — YouTube script, TikTok clips, Instagram reels, Twitter thread, LinkedIn article, blog post, GitHub README — all brand-compliant, generated in one pipeline run.

```
Brand Profile  →  Pipeline  →  7-Platform Package
   (once)          (per video)     (per video)
```

## Open Source

Built with love for the open source community. Contributions welcome!

⭐ Star this repo: https://github.com/sanamsitoula/BhrikutyFlimDirector
🐛 Issues & PRs: https://github.com/sanamsitoula/BhrikutyFlimDirector/issues

---

## Architecture

```
TOPIC + OUTLINE
      │
      ▼
┌─────────────────────────────────────────────┐
│  pipeline.py  (orchestrator)                │
│                                             │
│  Step 1 → generate_phase.py                 │
│           Claude (primary) or               │
│           Gemini (auto-fallback)            │
│  Step 2 → compliance_checker.py             │
│  Step 3 → remotion/ (infographic cards)     │
│  Step 4 → tools/tts/ (voiceover)            │
│  Step 5 → text_content_generator.py         │
│  Step 6 → platform_cutter.py (FFmpeg)       │
└─────────────────────────────────────────────┘
      │
      ▼
_output/phase_XX/
  youtube/   tiktok/   instagram/
  twitter/   linkedin/  blog/  github/
```

**Data layer:**
- Files are the source of truth for all generated content
- PostgreSQL stores brand metadata, pipeline run history, compliance logs
- Dashboard reads both — DB for speed, files as fallback

---

## Quick Setup (run once)

```bash
# 1. Clone
git clone https://github.com/sanamsitoula/BhrikutyFlimDirector.git
cd BhrikutyFlimDirector

# 2. Copy and fill in your API keys
cp .env.example .env   # then edit .env

# 3. Install everything globally (one command)
python install.py
```

`install.py` handles all packages, DB schema, and system tool checks. You never run it per-project or per-brand — it's global, once.

---

## Step-by-Step Setup

### Step 1 — Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11–3.13 recommended (3.14 works but Kokoro TTS unavailable) | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| FFmpeg | any | `winget install ffmpeg` (Windows) / `brew install ffmpeg` (Mac) |
| PostgreSQL | 15+ | https://postgresql.org |

Verify each:
```bash
python --version
node --version
ffmpeg -version
psql --version
```

---

### Step 2 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
# ── AI Providers (at least ONE required) ──────────────
ANTHROPIC_API_KEY=sk-ant-api03-...   # Primary — Claude Sonnet 4.6
GEMINI_API_KEY=your-gemini-key       # Fallback — Gemini 2.5 Flash (auto-used when Anthropic fails)

# ── Database ──────────────────────────────────────────
DB_HOST=localhost
DB_PORT=5432
DB_NAME=press_jemc
DB_USER=postgres
DB_PASSWORD=your-password

# ── TTS / Voiceover (add key for whichever you use) ───
ELEVENLABS_API_KEY=   # Paid, best quality
DASHSCOPE_API_KEY=    # Freemium — Qwen3-TTS

# ── Optional ──────────────────────────────────────────
ASSEMBLYAI_API_KEY=   # Auto YouTube chapters
OPENAI_API_KEY=       # ChatGPT GPT-4o / DALL-E images
BFL_API_KEY=          # FLUX.1 images
RUNWAY_API_KEY=       # Runway Gen-4 B-roll
```

**AI fallback logic:**
1. Try Anthropic (Claude Sonnet) — best quality
2. If Anthropic fails (no credits / quota) → automatically switches to Gemini 2.5 Flash
3. Force a provider: `python pipeline.py ... --provider gemini`

Get a free Gemini key: `aistudio.google.com` → Get API Key

**All supported AI providers:**
- `anthropic` — Claude Sonnet 4.6 (primary, best quality)
- `gemini` — Gemini 2.5 Flash (auto-fallback)
- `openai` — ChatGPT GPT-4o (optional, `OPENAI_API_KEY`)
- `dashscope` — Qwen3 (optional, `DASHSCOPE_API_KEY`)

Force a provider: `python tools/generate_phase.py --project ecoWorld --phase 1 --topic "..." --provider openai`

---

### Step 3 — Run the Installer

```bash
python install.py
```

This installs all Python packages, applies the DB schema, sets up Remotion, and checks system tools. Run it once — it's shared across all brands, projects, and phases.

```bash
python install.py --check    # see what's installed
python install.py --tts      # TTS engines only
python install.py --node     # Remotion (Node.js) only
python install.py --db       # apply DB schema only
python install.py --core     # core packages only
```

**What gets installed:**

| Package | Purpose | Status |
|---------|---------|--------|
| `anthropic` | Claude API (primary AI) | Required |
| `google-genai` | Gemini API (fallback AI) | Required |
| `psycopg2-binary` | PostgreSQL driver | Required |
| `elevenlabs` | ElevenLabs TTS (paid) | Optional |
| `dashscope` | Qwen3-TTS (freemium) | Optional |
| `kokoro` | Free CPU TTS | Python ≤3.12 only on Windows |
| `moviepy` | Video compositing | Optional |
| `faster-whisper` | Auto transcription | Optional |

> **Kokoro on Python 3.14 / Windows:** Kokoro requires compiling C extensions with MinGW GCC ≥8.4. If you're on Python 3.14, use ElevenLabs or DashScope for TTS instead.

---

### Step 4 — Create Your First Brand

Every video series needs a brand. Run the wizard once per brand:

```bash
python tools/init_brand.py
```

Or supply flags:
```bash
python tools/init_brand.py \
  --slug ecoWorld \
  --name "Eco World" \
  --tagline "Economics, finally making sense." \
  --niche "Economics Education"
```

**What this creates automatically:**
```
youtube_scripts/setup/projects/ecoWorld/
├── brand_profile.json       ← Full brand identity (edit to customise)
├── brand_guidelines.md      ← Rules for your content team
├── roadmap.json             ← 5-phase content plan scaffold
├── tags_and_metadata.json   ← SEO tags + hashtags per platform
├── setup_guide.md           ← Your personalised next-step guide
├── phase_1/README.md        ← Phase 1 production checklist
├── phase_2/README.md  ...  phase_5/README.md
└── _output/phase_01/ ...  phase_05/   ← Export directories
```

It also inserts the brand and phase records into PostgreSQL.

Also available from the web dashboard: `http://localhost:8080/brand`

---

### Step 5 — Run the Pipeline

```bash
python pipeline.py \
  --project ecoWorld \
  --phase 1 \
  --topic "What is GDP and why does it matter?" \
  --outline "Definition, how measured, why it changes, what it misses" \
  --duration 12 \
  --tags "gdp,economics,macroeconomics"
```

**Pipeline steps:**

| Step | Script | Produces |
|------|--------|---------|
| 1 | `generate_phase.py` | `script.md`, `script_short.md`, `subtitles.srt`, `voiceover_brief.md`, `clip_brief.md`, `music_brief.md`, `infographics.md`, `content_spec.json`, `infographic_assets/card_0*.html` |
| 2 | `compliance_checker.py` | `compliance_report_auto.md` — 17 brand rule checks |
| 3 | `remotion/` | Animated infographic cards |
| 4 | `tools/tts/` | `voiceover/phase_N.wav` |
| 5 | `text_content_generator.py` | `youtube/description.txt`, `twitter/thread.txt`, `linkedin/article.md`, `blog/post.md`, `github/README.md` |
| 6 | `platform_cutter.py` | `youtube/final_1080p.mp4`, `tiktok/clip_*.mp4`, `instagram/reel_60s.mp4` |

**Skip flags:**
```bash
--skip-generate     # skip Step 1 (use existing files)
--skip-voiceover    # skip Step 4
--skip-remotion     # skip Step 3
--skip-text         # skip Step 5
--provider gemini   # force Gemini instead of Claude
--provider anthropic # force Claude
```

Each run is logged to `pipeline_runs` table in PostgreSQL.

---

### Step 6 — Check Compliance

```bash
python tools/compliance_checker.py --project ecoWorld --phase 1
```

17 checks: forbidden words, sentence length, subtitle timing, brand colors, font CDN, animation sequence, card dimensions, SRT format, no investment advice, and more.

Status: **PASS** / **PASS_WITH_WARNINGS** / **FAIL**

---

### Step 7 — Generate Voiceover

The pipeline auto-selects the best available engine:

```bash
# Voiceover runs automatically in Step 4 of the pipeline.
# To run manually:

# ElevenLabs (paid, best quality) — needs ELEVENLABS_API_KEY
python tools/tts/elevenlabs_voiceover.py --phase 1 --project ecoWorld

# DashScope / Qwen3-TTS (freemium) — needs DASHSCOPE_API_KEY
python tools/tts/dashscope_voiceover.py --phase 1 --project ecoWorld

# Kokoro (free, CPU) — Python <=3.12 only on Windows
pip install kokoro soundfile
python tools/tts/kokoro_voiceover.py --phase 1 --project ecoWorld
```

---

### Step 8 — Export Platform Clips

After assembling your video:
```bash
python tools/platform_cutter.py \
  --project ecoWorld \
  --phase 1 \
  --video path/to/your/final.mp4
```

Exports to `_output/phase_01/`: YouTube (16:9), TikTok (9:16), Instagram Reels (9:16), Twitter, LinkedIn.

---

### Step 9 — Generate Text Content

```bash
python tools/text_content_generator.py --project ecoWorld --phase 1
```

Generates: YouTube description, Twitter thread, LinkedIn article, blog post, Instagram caption, GitHub README.

---

### Step 10 — Dashboard

```bash
python server.py
# Open http://localhost:8080
```

**Pages:**

| URL | What it shows |
|-----|--------------|
| `/` | Pipeline runner + live output |
| `/projects` | All brands + progress |
| `/brand` | Create / edit brand |
| `/phase/{slug}/{num}` | Phase detail |

**Manual Content Editor** (at bottom of dashboard):  
When AI credits are low — paste content from ChatGPT, Claude.ai, or Gemini web, select file type, click **Save File**. Works without any API key.

**API endpoints:**

| Method | Endpoint | Returns |
|--------|----------|---------|
| GET | `/api/brands` | All brands |
| POST | `/api/brands` | Create brand (full scaffold) |
| GET | `/api/projects/{slug}/summary` | Phase progress |
| GET | `/api/projects/{slug}/runs` | Pipeline history (DB) |
| POST | `/api/run` | Start pipeline job |
| GET | `/api/jobs/{id}/stream` | Live output (SSE) |
| POST | `/api/save-file` | Save pasted content |
| GET | `/api/db-status` | PostgreSQL status |

---

## Project Structure

```
BhrikutyFlimDirector/
│
├── install.py                    ← Global one-time setup (run once)
├── pipeline.py                   ← CLI pipeline runner
├── server.py                     ← Dashboard server (port 8080)
├── .env                          ← API keys (never commit)
├── .env.example                  ← Template
├── requirements.txt              ← Python dependencies
│
├── db/
│   ├── schema.sql                ← PostgreSQL DDL (run via install.py --db)
│   └── db.py                     ← Connection module (graceful fallback)
│
├── tools/
│   ├── init_brand.py             ← Brand scaffold (files + DB records)
│   ├── generate_phase.py         ← Claude/Gemini content generation
│   ├── compliance_checker.py     ← 17-rule brand compliance
│   ├── platform_cutter.py        ← FFmpeg platform exports
│   ├── text_content_generator.py ← Platform-specific text content
│   └── tts/
│       ├── kokoro_voiceover.py   ← Free TTS (Python ≤3.12)
│       ├── elevenlabs_voiceover.py
│       └── dashscope_voiceover.py
│
├── dashboard.html                ← Main pipeline UI
├── projects.html                 ← Projects browser
├── brand.html                    ← Brand creation/editing
├── phase_dashboard.html          ← Per-phase detail
│
└── youtube_scripts/setup/projects/
    └── {brand_slug}/
        ├── brand_profile.json
        ├── brand_guidelines.md
        ├── roadmap.json
        ├── tags_and_metadata.json
        ├── setup_guide.md
        ├── phase_1/ ... phase_N/
        │   ├── README.md          ← Checklist
        │   ├── script.md
        │   ├── subtitles.srt
        │   ├── compliance_report_auto.md
        │   └── infographic_assets/
        └── _output/phase_01/ ... phase_NN/
            ├── youtube/
            ├── tiktok/
            ├── instagram/
            ├── twitter/
            ├── linkedin/
            ├── blog/
            └── github/
```

---

## Database

Schema is in `db/schema.sql`. Applied automatically by `python install.py --db`.

```sql
-- Run history for a brand
SELECT run_id, phase_num, status, started_at
FROM pipeline_runs WHERE brand_slug = 'ecoWorld'
ORDER BY started_at DESC;

-- Phase status
SELECT phase_num, topic, status FROM phases
WHERE brand_slug = 'ecoWorld' ORDER BY phase_num;

-- Compliance history
SELECT phase_num, overall_status, checked_at
FROM compliance_logs WHERE brand_slug = 'ecoWorld';
```

**Tables:** `brands`, `phases`, `pipeline_runs`, `pipeline_steps`, `generated_files`, `compliance_logs`, `content_specs`

---

## Manual Content Editor

When AI credits are low, use the paste editor in the dashboard (`http://localhost:8080`):

1. Scroll to **Manual Content Editor**
2. Select project + phase + file type
3. Paste content (from ChatGPT, Claude.ai, Gemini web, etc.)
4. Click **Save File**

Or via API:
```bash
curl -X POST http://localhost:8080/api/save-file \
  -H "Content-Type: application/json" \
  -d '{"project":"ecoWorld","phase":1,"filename":"script.md","content":"..."}'
```

---

## TTS Engine Comparison

| Engine | Cost | Requires | Quality | Python 3.14 Win |
|--------|------|---------|---------|----------------|
| Kokoro | Free | CPU only | ⭐⭐⭐⭐ | Not supported |
| ElevenLabs | $5–22/mo | API key | ⭐⭐⭐⭐⭐ | Yes |
| DashScope/Qwen3 | Freemium | API key | ⭐⭐⭐⭐ | Yes |
| Chatterbox | Free | 8GB GPU | ⭐⭐⭐⭐⭐ | Manual install |

---

## Troubleshooting

**`ANTHROPIC_API_KEY not set` / low credits**
→ The pipeline automatically switches to Gemini. Set `GEMINI_API_KEY` in `.env`.

**`ffmpeg not found`**
→ Run `python install.py --check` — it detects and adds common ffmpeg paths to PATH.

**`npm not found` / Remotion fails**
→ Install Node.js 18+ from nodejs.org. Use `--skip-remotion` to bypass.

**Kokoro fails to install (numpy build error)**
→ Known issue on Python 3.14 / Windows with MinGW GCC <8.4. Use ElevenLabs or DashScope instead.

**`database "press_jemc" does not exist`**
→ Run `python install.py --db` to create the DB and apply the schema.

**Port 8080 already in use**
→ `$env:PORT=8081; python server.py` (PowerShell)

**`brand_profile.json not found`**
→ Run `python tools/init_brand.py --slug your-brand` first.

---

## Example: Complete Run

```bash
# 1. Setup (once ever)
python install.py

# 2. Create brand (once per brand)
python tools/init_brand.py --slug ecoWorld --name "Eco World" \
  --tagline "Economics, finally making sense." --niche "Economics Education"

# 3. Run pipeline (once per video)
python pipeline.py \
  --project ecoWorld --phase 1 \
  --topic "What is GDP?" \
  --outline "Definition, measurement, why it rises/falls, what it misses" \
  --duration 12 --tags "gdp,economics,macro"

# 4. Check compliance
python tools/compliance_checker.py --project ecoWorld --phase 1

# 5. Export clips (after assembling video)
python tools/platform_cutter.py --project ecoWorld --phase 1 \
  --video _output/phase_01/final.mp4

# 6. Generate text content
python tools/text_content_generator.py --project ecoWorld --phase 1

# 7. Track everything
python server.py   # open http://localhost:8080
```

---

## Git Workflow — Step by Step

```bash
# 1. Clone the repo
git clone https://github.com/sanamsitoula/BhrikutyFlimDirector.git
cd BhrikutyFlimDirector

# 2. Create your working branch
git checkout -b feat/my-brand

# 3. Stage your changes
git add server.py tools/ phase_dashboard.html dashboard.html

# 4. Commit with a clear message
git commit -m "feat: add ecoWorld brand with phase 1 content"

# 5. Push to GitHub
git push -u origin feat/my-brand

# 6. Open a Pull Request on GitHub
# → https://github.com/sanamsitoula/BhrikutyFlimDirector/pulls
```

Commit conventions:
| Prefix | Use for |
|--------|---------|
| `feat:` | New brand, phase, or feature |
| `fix:` | Bug fix |
| `docs:` | README, guides |
| `chore:` | Deps, cleanup |

---

*Bhrikuty Film Director — AI content production system*
