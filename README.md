# Bhrikuty Film Director

<div align="center">

**AI-powered content factory — Brand → Script → Compliance → 7-Platform Package**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green?style=flat-square&logo=node.js)](https://nodejs.org)
[![Claude API](https://img.shields.io/badge/Claude-Sonnet_4.6-orange?style=flat-square)](https://anthropic.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-blue?style=flat-square)](https://aistudio.google.com)
[![ChatGPT](https://img.shields.io/badge/ChatGPT-GPT--4o-green?style=flat-square)](https://openai.com)
[![Qwen](https://img.shields.io/badge/Qwen3-DashScope-purple?style=flat-square)](https://dashscope.aliyuncs.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue?style=flat-square&logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open_Source-%E2%9D%A4%EF%B8%8F-red?style=flat-square)](https://github.com/sanamsitoula/BhrikutyFlimDirector)

</div>

---

## What is Bhrikuty?

Give it a **brand** and a **topic**. It produces a complete **7-platform content package** — YouTube script, TikTok clips, Instagram reels, Twitter thread, LinkedIn article, blog post — all brand-compliant, generated in one pipeline run.

```
Brand Profile  →  Phase  →  Script + Cards + Audio + Cuts + Text
   (once)         (per video)        (per platform)
```

**Built for the open source community.**
⭐ Star: https://github.com/sanamsitoula/BhrikutyFlimDirector
🐛 Issues & PRs: https://github.com/sanamsitoula/BhrikutyFlimDirector/issues

---

## Architecture

```
TOPIC + OUTLINE
      │
      ▼
┌──────────────────────────────────────────────────────┐
│  pipeline.py  (orchestrator)                         │
│                                                      │
│  Step 1.1  generate_phase.py  →  script.md           │
│  Step 1.2                    →  script_short.md      │
│  Step 1.3                    →  subtitles.srt        │
│  Step 1.4                    →  voiceover_brief.md   │
│  Step 1.5                    →  music_brief.md       │
│  Step 1.6                    →  infographics.md      │
│  Step 1.7                    →  clip_brief.md        │
│  Step 1.8                    →  card_0*.html         │
│  Step 1.9                    →  content_spec.json    │
│                                                      │
│  Step 2    compliance_checker.py  →  report          │
│  Step 3    tools/tts/             →  voiceover/      │
│  Step 4    remotion/              →  animated cards  │
│  Step 5    text_content_generator →  platform text   │
│  Step 6    platform_cutter.py     →  video cuts      │
└──────────────────────────────────────────────────────┘
      │
      ▼
_output/phase_XX/
  youtube/  tiktok/  instagram/  twitter/  linkedin/  blog/
```

**AI providers (auto-fallback chain):**
Claude Sonnet 4.6 → Gemini 2.5 Flash → ChatGPT GPT-4o → Qwen3 (DashScope)

**Data layer:**
- Files are the source of truth for all generated content
- PostgreSQL stores brand metadata, pipeline run history, compliance logs
- Dashboard reads both — DB for speed, files as fallback

---

## Quick Setup

```bash
# 1. Clone
git clone https://github.com/sanamsitoula/BhrikutyFlimDirector.git
cd BhrikutyFlimDirector

# 2. Copy and fill in API keys
cp .env.example .env

# 3. Install (once, global)
python install.py
```

---

## Step-by-Step Setup

### Step 1 — Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11–3.13 recommended (3.14 works, Kokoro TTS unavailable) | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| FFmpeg | any | `winget install ffmpeg` (Windows) / `brew install ffmpeg` (Mac) |
| PostgreSQL | 15+ | https://postgresql.org |

```bash
python --version && node --version && ffmpeg -version && psql --version
```

---

### Step 2 — Environment Variables

```env
# ── AI Providers (at least ONE required) ──────────────
ANTHROPIC_API_KEY=sk-ant-...    # Claude Sonnet 4.6 (primary)
GEMINI_API_KEY=AIza...          # Gemini 2.5 Flash (auto-fallback — free tier at aistudio.google.com)
OPENAI_API_KEY=sk-...           # ChatGPT GPT-4o (optional)
DASHSCOPE_API_KEY=sk-...        # Qwen3 (optional — dashscope.aliyuncs.com → Model Studio → API Keys)

# ── Database ──────────────────────────────────────────
DB_HOST=localhost
DB_PORT=5432
DB_NAME=press_jemc
DB_USER=postgres
DB_PASSWORD=your-password

# ── TTS / Voiceover ────────────────────────────────────
ELEVENLABS_API_KEY=    # Paid — best quality
DASHSCOPE_API_KEY=     # Freemium — Qwen3-TTS (same key as script AI)

# ── Optional ──────────────────────────────────────────
ASSEMBLYAI_API_KEY=    # Auto YouTube chapters
BFL_API_KEY=           # FLUX.1 images
RUNWAY_API_KEY=        # Runway Gen-4 b-roll
KLING_API_KEY=         # Kling AI video
```

**AI fallback logic — fully automatic:**
1. Try Anthropic (Claude Sonnet) — best quality
2. If Anthropic fails (no credits / quota / billing) → Gemini 2.5 Flash
3. Gemini 429 rate-limit → auto-waits the suggested retry delay, then retries
4. Force a provider: `--provider gemini` / `--provider openai` / `--provider dashscope`

**DashScope free tier setup:**
1. Go to `dashscope.aliyuncs.com` → sign up with Alibaba Cloud
2. Model Studio → API Keys → Create key
3. Add `DASHSCOPE_API_KEY=sk-xxx` to `.env`

---

### Step 3 — Install

```bash
python install.py                 # everything
python install.py --check         # see what's installed / missing
python install.py --core          # Python packages only
python install.py --tts           # TTS engines only
python install.py --db            # apply DB schema only
python install.py --node          # Remotion (Node.js) only
```

| Package | Purpose | Notes |
|---------|---------|-------|
| `anthropic` | Claude API | Required |
| `google-genai` | Gemini API | Required (free tier) |
| `psycopg2-binary` | PostgreSQL | Required |
| `elevenlabs` | Best quality TTS | Paid |
| `dashscope` | Qwen3-TTS + Qwen3 AI | Freemium |
| `kokoro` | Free CPU TTS | Python ≤3.12 on Windows |
| `faster-whisper` | Local transcription | Optional |
| `moviepy` | Video compositing | Optional |

---

### Step 4 — Create Your First Brand

```bash
python tools/init_brand.py \
  --slug ecoWorld \
  --name "Eco World" \
  --tagline "Economics, finally making sense." \
  --niche "Economics Education"
```

Or from the dashboard at `http://localhost:8080/brand`.

**Created automatically:**
```
youtube_scripts/setup/projects/ecoWorld/
├── brand_profile.json       ← Colors, typography, tone, audience, pillars
├── brand_guidelines.md      ← Human-readable rules
├── roadmap.json             ← 5-phase content plan
├── tags_and_metadata.json   ← SEO tags per platform
├── phase_1/ ... phase_5/
│   └── README.md            ← Production checklist per phase
└── _output/phase_01/ ... phase_05/
```

---

### Step 5 — Run the Pipeline

```bash
python pipeline.py \
  --project ecoWorld \
  --phase 1 \
  --topic "Microeconomics Basics" \
  --outline "supply and demand, elasticity, market equilibrium" \
  --duration 12 \
  --tags "economics,micro,education"
```

**Flags:**
```bash
--provider gemini        # force Gemini instead of Claude
--provider openai        # force ChatGPT
--provider dashscope     # force Qwen3
--skip-generate          # skip Step 1 (use existing files)
--skip-voiceover         # skip TTS
--skip-remotion          # skip Remotion card render
--skip-text              # skip text content
--video path/to/mp4      # provide existing video for platform cuts
```

**Generate a single file (fastest, no full pipeline):**
```bash
# Seed file — required first, needs topic + outline
python tools/generate_phase.py --project ecoWorld --phase 1 \
  --topic "Microeconomics Basics" --outline "supply and demand" --only script.md

# All other files derive from script.md on disk
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

### Step 6 — Compliance Check

```bash
python tools/compliance_checker.py --project ecoWorld --phase 1
```

**17 checks:** forbidden words, sentence length (max 15 words), subtitle timing, brand hex colors, font CDN (Space Grotesk + Inter + JetBrains Mono), animation sequence timings, card dimensions, SRT format, sound identity, no investment advice.

**Animation sequence (compliance-enforced timings):**
```css
animation: fadeIn   0.2s forwards;   /* Step 1 — background */
animation: slideDown 0.3s forwards;  /* Step 2 — logo */
animation: wordIn   0.15s forwards;  /* Step 3 — headline words */
animation: slideUp  0.4s forwards;   /* Step 4 — content */
animation: bounce   0.3s forwards;   /* Step 5 — CTA */
```

Status: **PASS** / **PASS_WITH_WARNINGS** / **FAIL**

---

### Step 7 — Voiceover

```bash
# ElevenLabs (paid, best) — needs ELEVENLABS_API_KEY
python tools/tts/elevenlabs_voiceover.py --project ecoWorld --phase 1

# DashScope Qwen-TTS (freemium) — needs DASHSCOPE_API_KEY
python tools/tts/dashscope_voiceover.py --project ecoWorld --phase 1

# Kokoro (free, CPU) — Python <=3.12 Windows
python tools/tts/kokoro_voiceover.py --project ecoWorld --phase 1
```

**Manual voice recording (no API needed):**
1. Open `phase_1/script.md`, read the `NARRATION:` sections
2. Record with Audacity or any recorder at 44.1 kHz WAV
3. Save to `phase_1/voiceover/phase_1.wav`
4. Pipeline auto-detects it — TTS step shows Done

---

### Step 8 — Text Content

```bash
python tools/text_content_generator.py --project ecoWorld --phase 1
```

Generates: YouTube description, Twitter thread (7 tweets), LinkedIn article (800 words), blog post, Instagram caption, GitHub README.

Auto-falls back to Gemini when Anthropic credits run low.

---

### Step 9 — Platform Cuts

```bash
python tools/platform_cutter.py \
  --project ecoWorld --phase 1 \
  --video _output/phase_01/youtube/final_1080p.mp4
```

Exports: YouTube 16:9, TikTok 9:16, Instagram Reels 9:16, Twitter 16:9, LinkedIn.

---

### Step 10 — Dashboard

```bash
python server.py
# Open http://localhost:8080
# Different port: $env:PORT=8081; python server.py  (PowerShell)
```

---

## Phase Dashboard (`/phase/{brand}/{num}`)

The per-phase dashboard is the main working interface. Tabs:

| Tab | What it shows |
|-----|--------------|
| **Overview** | Video type selector (B-Roll / Screen / Animation / Manual), TTS guide, chapters, platform cuts, tags |
| **Script** | `script.md` viewer + inline editor |
| **Short Script** | `script_short.md` — 60s TikTok/Reels cut |
| **Infographics** | Card previews with clickable URLs + Copy All URLs |
| **Subtitles** | `subtitles.srt` viewer |
| **Audio** | Voiceover player + voiceover brief |
| **Video** | Inline video player + clip brief |
| **Compliance** | `compliance_report_auto.md` |
| **All Files** | File browser + inline viewer/editor |
| **Context** | Full brand identity + content breakdown → **Copy Prompt** button |

### Pipeline Steps (expanded sub-steps)

Step 1 is broken into 9 trackable sub-steps. Each shows:
- Its output file name
- What it needs (dependencies)
- Exact CLI command to run it — click **$ CMD** to reveal, **📋 Copy** or **▶ Run**

### Inline Editor (no AI required)

When a file is missing, clicking its tab shows an editor instead of an error. Type or paste content → **💾 Save**. Works without any API key — useful when AI credits are low or you want to write manually.

### Context Tab + Copy Prompt

The **📋 Context** tab shows your full brand identity in one place: colors (with swatches), typography, tone of voice, forbidden words, target audience, content pillars, sound identity.

**📋 Copy Prompt** — one click copies the entire brand + phase context as a formatted text block to paste into any AI tool (ChatGPT, Claude.ai, Gemini) before asking it to generate content.

### Infographic Card URLs

The **Infographics** tab shows:
- Clickable URL per card (e.g. `http://localhost:8081/media/ecoWorld/1/infographic_assets/card_01.html`)
- **📋 Copy** per card + **Copy All URLs** button
- Card previews (scaled iframes) + Open → full size in new tab
- `cards_manifest.json` tracks filename, URL, size, generated date

---

## Video Production Types

Select from the **Overview** tab. Your choice is saved to `phase_1/video_type.json`.

| Type | Description | Steps |
|------|-------------|-------|
| 🎞️ **B-Roll** | Stock or custom footage | Source clips → TTS → Assemble → Shorts |
| 🖥️ **Screen Recording** | OBS/ShareX capture | Record → Trim → Add cards → Cuts |
| ✨ **Animation Only** | Remotion from cards + audio | Generate cards → TTS → Remotion renders all |
| 🎙️ **Manual** | Bring your own video | Provide `--video path/file.mp4` → auto cuts |

The Overview tab shows the exact steps for your chosen type.

---

## API Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/brands` | List all brands |
| POST | `/api/brands` | Create brand (full scaffold) |
| GET | `/api/brands/{slug}` | Single brand profile |
| PUT | `/api/brands/{slug}` | Update brand profile |
| GET | `/api/phase-data?project=X&phase=N` | Full phase data (steps, files, cards, brand, roadmap) |
| GET | `/api/file?project=X&phase=N&file=Y` | Read a phase file |
| POST | `/api/save-file` | Save/create a phase file |
| POST | `/api/run` | Start full pipeline job |
| POST | `/api/run-step` | Run a single sub-step (`--only script.md` etc.) |
| GET | `/api/jobs/{id}/stream` | Live output (SSE stream) |
| GET | `/api/tools-status` | Which AI/TTS/image tools are configured |
| GET | `/api/projects/{slug}/summary` | Phase progress summary |
| GET | `/api/projects/{slug}/runs` | Pipeline run history (DB) |
| GET | `/api/db-status` | PostgreSQL availability |

---

## Project Structure

```
BhrikutyFlimDirector/
│
├── install.py                    ← Global one-time setup
├── pipeline.py                   ← CLI pipeline runner
├── server.py                     ← Dashboard server (port 8080)
├── .env                          ← API keys (never commit)
├── .env.example                  ← Template
├── requirements.txt
│
├── db/
│   ├── schema.sql                ← PostgreSQL DDL
│   └── db.py                     ← Connection helper (graceful fallback)
│
├── tools/
│   ├── init_brand.py             ← Brand scaffold
│   ├── generate_phase.py         ← Content generation (Claude/Gemini/GPT/Qwen)
│   │                                --only flag for single-file generation
│   ├── compliance_checker.py     ← 17-rule brand compliance
│   ├── platform_cutter.py        ← FFmpeg platform exports
│   ├── text_content_generator.py ← Platform text (Gemini fallback)
│   └── tts/
│       ├── kokoro_voiceover.py
│       ├── elevenlabs_voiceover.py
│       └── dashscope_voiceover.py
│
├── dashboard.html                ← Main pipeline UI + Script AI selector
├── projects.html                 ← Projects browser
├── brand.html                    ← Brand creation/editing
├── phase_dashboard.html          ← Per-phase detail (10 tabs)
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
        │   ├── video_type.json         ← B-Roll / Screen / Animation / Manual
        │   ├── voiceover/phase_N.wav
        │   └── infographic_assets/
        │       ├── card_01.html
        │       ├── card_02.html
        │       ├── card_03.html
        │       └── cards_manifest.json ← URLs, sizes, timestamps
        └── _output/phase_NN/
            ├── youtube/
            ├── tiktok/
            ├── instagram/
            ├── twitter/
            ├── linkedin/
            └── blog/
```

---

## TTS Engine Comparison

| Engine | Cost | Python 3.14 Win | Notes |
|--------|------|----------------|-------|
| Kokoro | Free | Not supported | CPU, Python ≤3.12 |
| ElevenLabs | $5–22/mo | Yes | Best quality, voice cloning |
| DashScope/Qwen3 | Freemium | Yes | Multilingual, generous free tier |
| Chatterbox | Free | Manual install | GPU, emotion control |

---

## Database

```sql
-- Run history
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

## Complete Example

```bash
# 1. Setup (once)
python install.py

# 2. Create brand
python tools/init_brand.py --slug ecoWorld --name "Eco World" \
  --tagline "Economics, finally making sense." --niche "Economics Education"

# 3. Generate all files for Phase 1
python pipeline.py --project ecoWorld --phase 1 \
  --topic "Microeconomics Basics" \
  --outline "supply and demand, elasticity, equilibrium, elasticity"

# 4. Or generate file by file (useful when AI credits are limited)
python tools/generate_phase.py --project ecoWorld --phase 1 \
  --topic "Microeconomics Basics" --outline "supply, demand, prices" \
  --only script.md
# Then paste into dashboard editor, or run each sub-step:
python tools/generate_phase.py --project ecoWorld --phase 1 --only script_short.md
python tools/generate_phase.py --project ecoWorld --phase 1 --only subtitles.srt
# ... etc.

# 5. Check compliance
python tools/compliance_checker.py --project ecoWorld --phase 1

# 6. Generate voiceover
python tools/tts/dashscope_voiceover.py --project ecoWorld --phase 1

# 7. Generate text content (falls back to Gemini if Anthropic has no credits)
python tools/text_content_generator.py --project ecoWorld --phase 1

# 8. Cut for all platforms (after video assembly)
python tools/platform_cutter.py --project ecoWorld --phase 1 \
  --video _output/phase_01/youtube/final_1080p.mp4

# 9. Dashboard
python server.py   # http://localhost:8080
```

---

## Troubleshooting

**Anthropic 400 / low credits**
→ Automatic fallback to Gemini. Get a free Gemini key at `aistudio.google.com`.

**Gemini 429 rate limit**
→ Auto-handled — waits the suggested retry delay (often 43s) and retries up to 6 times.

**`ffmpeg not found`**
→ `python install.py --check` detects and patches PATH. Or `winget install ffmpeg`.

**Kokoro fails to install**
→ Known issue on Python 3.14 / Windows. Use ElevenLabs or DashScope instead.

**`database does not exist`**
→ `python install.py --db` creates the DB and applies schema.

**DB FK constraint `pipeline_runs_brand_slug_fkey`**
→ Fixed — `create_run` in `db.py` now inserts a minimal brand row automatically before each run.

**Port 8080 in use**
→ `$env:PORT=8081; python server.py`

**`brand_profile.json not found`**
→ Run `python tools/init_brand.py --slug your-brand` first.

**Card fails compliance (JetBrains Mono / animation)**
→ Add `--font-code: 'JetBrains Mono', monospace;` to `:root` in the card CSS.
→ Animation timings must match exactly: `fadeIn 0.2s`, `slideDown 0.3s`, `wordIn 0.15s`, `slideUp 0.4s`, `bounce 0.3s`.

---

## Git Workflow

```bash
# 1. Clone
git clone https://github.com/sanamsitoula/BhrikutyFlimDirector.git
cd BhrikutyFlimDirector

# 2. Branch
git checkout -b feat/my-brand

# 3. Stage + commit
git add server.py tools/ phase_dashboard.html dashboard.html
git commit -m "feat: add ecoWorld brand with phase 1 content"

# 4. Push
git push -u origin feat/my-brand

# 5. Pull Request → https://github.com/sanamsitoula/BhrikutyFlimDirector/pulls
```

| Prefix | Use for |
|--------|---------|
| `feat:` | New brand, phase, or feature |
| `fix:` | Bug fix |
| `docs:` | README, guides |
| `chore:` | Deps, cleanup |

---

*Bhrikuty Film Director — Built with ❤️ for the open source community*
*https://github.com/sanamsitoula/BhrikutyFlimDirector*
