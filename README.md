# Bhrikuty — Film Director Content Factory

> **Brand → Project → Content — One Pipeline**

Bhrikuty is an AI-powered content production system. Define your brand once, create projects under it, then run a single command to produce a 7-platform content package: YouTube video, TikTok clips, Instagram reels, Twitter thread, LinkedIn article, blog post, and GitHub README.

---

## Complete Flow

```
STEP 0  Set up prerequisites (Python, ffmpeg, Node.js)
   ↓
STEP 1  Copy .env.example → .env  (add your API keys)
   ↓
STEP 2  Start the web dashboard
   ↓
STEP 3  Create a Brand  (/brand)
        — name, colors, fonts, tone of voice, social links
   ↓
STEP 4  Create a Project  (/projects)
        — tied to your brand, named by topic series
   ↓
STEP 5  Generate Content  (/  →  New Video Project)
        — topic, outline, phase number → run pipeline
   ↓
STEP 6  Voiceover  (TTS engine of your choice)
   ↓
STEP 7  Build Infographic Cards  (Remotion or HTML screenshots)
   ↓
STEP 8  Assemble Video  (FFmpeg + MoviePy)
   ↓
STEP 9  Auto-Transcribe  (faster-whisper or WhisperX)
   ↓
STEP 10 Compliance Check  (17 brand rules validated)
   ↓
STEP 11 Export Platform Clips  (YouTube · TikTok · Instagram · Twitter · LinkedIn)
   ↓
STEP 12 Generate Text Content  (blog · thread · article · GitHub README)
   ↓
STEP 13 Review & Publish
```

---

## Project Structure

```
bhrikuty/
├── server.py                          ← Web dashboard server (run this first)
├── pipeline.py                        ← Film Director entry point (CLI)
├── dashboard.html                     ← Main dashboard UI
├── projects.html                      ← Projects browser with favourites
├── brand.html                         ← Brand setup and management
├── phase_dashboard.html               ← Per-phase content dashboard
├── .env.example                       ← Copy to .env, fill in keys
├── README.md
│
├── tools/
│   ├── generate_phase.py              ← AI script + brief generation
│   ├── compliance_checker.py          ← 17 brand rule checks
│   ├── platform_cutter.py             ← Export per-platform clips
│   ├── text_content_generator.py      ← Blog · thread · article · README
│   └── tts/
│       ├── kokoro_voiceover.py        ← Free (CPU, no GPU needed)
│       ├── chatterbox_voiceover.py    ← Free (GPU, voice cloning)
│       └── elevenlabs_voiceover.py    ← Paid (best quality)
│
├── remotion/                          ← Animated infographic cards (React)
│   ├── package.json
│   └── scripts/render_all_cards.js
│
├── myvideo/edit/
│   ├── burn_text.py                   ← Text overlay on video
│   ├── generate_voiceover.py          ← Qwen3-TTS (current default)
│   └── clean_voice.py                 ← Audio cleanup
│
└── youtube_scripts/setup/projects/
    └── {brand_slug}/                  ← One folder per brand/project
        ├── brand_profile.json         ← Brand identity (colors, fonts, tone)
        ├── roadmap.json               ← Phase plan
        ├── tags_and_metadata.json     ← Platform tags
        ├── compliance_log.json
        ├── phase_1/
        │   ├── script.md              ← Full narration script
        │   ├── script_short.md        ← 60-second cut
        │   ├── subtitles.srt          ← Captions
        │   ├── voiceover_brief.md     ← TTS pacing guide
        │   ├── clip_brief.md          ← Shot-by-shot assembly guide
        │   ├── music_brief.md         ← BPM, mood, instrumentation
        │   ├── infographics.md        ← Card layout specs
        │   ├── content_spec.json      ← Platform cuts, tags, YouTube chapters
        │   ├── compliance_report.md   ← Manual compliance
        │   ├── compliance_report_auto.md ← Auto-generated compliance
        │   └── infographic_assets/
        │       ├── card_01.html
        │       ├── card_02.html
        │       └── card_03.html
        ├── phase_2/ … phase_N/
        └── _output/
            └── phase_01/
                ├── youtube/  final_1080p.mp4 · description.txt · subtitles.srt
                ├── tiktok/   clip_01_hook.mp4 · clip_02_main.mp4
                ├── instagram/ reel_60s.mp4 · carousel_1.png … carousel_3.png
                ├── twitter/  card_clip.mp4 · thread.txt
                ├── linkedin/ clip.mp4 · article.md
                ├── blog/     post.md
                ├── github/   README.md
                └── PIPELINE_SUMMARY.md
```

---

## STEP 0 — Prerequisites

### Python 3.11+

```bash
# Verify
python --version
```

### Core Python packages

```bash
pip install anthropic moviepy faster-whisper
```

### FFmpeg (required for video cuts)

```bash
# Windows
winget install ffmpeg

# Mac
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# Verify
ffmpeg -version
```

### Node.js 18+ (required for Remotion card rendering)

```bash
# Download from https://nodejs.org
# Verify
node --version
```

### Install Remotion dependencies (once)

```bash
cd remotion
npm install
cd ..
```

---

## STEP 1 — Environment Setup

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
# REQUIRED — for script generation and text content
ANTHROPIC_API_KEY=sk-ant-api03-...

# TTS — pick ONE (others are optional)
ELEVENLABS_API_KEY=          # Paid, best quality
DASHSCOPE_API_KEY=           # Freemium, Qwen3-TTS (current default)
# Chatterbox + Kokoro run locally — no key needed

# Transcription — optional (faster-whisper is free and runs locally)
ASSEMBLYAI_API_KEY=

# Image generation — optional
BFL_API_KEY=

# Video B-roll — optional
RUNWAY_API_KEY=
KLING_API_KEY=
```

---

## STEP 2 — Start the Dashboard Server

```bash
python server.py
```

Open your browser:

```
http://localhost:8080
```

The server runs on port 8080 by default. To change the port:

```bash
PORT=3000 python server.py
```

**All four pages are now available:**

| URL | Page |
|-----|------|
| `http://localhost:8080/` | Main Dashboard (pipeline control) |
| `http://localhost:8080/brand` | Brand Setup & Management |
| `http://localhost:8080/projects` | Projects Browser with Favourites |
| `http://localhost:8080/phase/{project}/{num}` | Per-Phase Content Dashboard |

---

## STEP 3 — Create a Brand

Go to: **`http://localhost:8080/brand`**

Click **+ New Brand** and fill in:

| Field | Example |
|-------|---------|
| Brand / Company Name | `Chain Clarity` |
| Brand Slug | `chain_clarity` (auto-generated from name) |
| Tagline | `Blockchain, without the noise.` |
| Niche / Industry | `Blockchain & Crypto Education` |
| Target Audience | `Curious learners ages 22–40…` |
| Platforms | YouTube, TikTok, Instagram |
| Primary Color | `#00D4AA` (Electric Teal) |
| Secondary Color | `#F5A623` (Deep Gold) |
| Background Color | `#0A0E1A` (Deep Navy) |
| Heading Font | `Space Grotesk` |
| Body Font | `Inter` |
| Content Pillars | How Blockchain Works, DeFi, Security… |
| Tone of Voice | Trusted senior engineer explaining… |
| Forbidden Words | moon, lambo, HODL, simply, obviously… |
| Social Links | YouTube channel URL, Instagram URL, etc. |

Click **💾 Create Brand** — this creates:

```
youtube_scripts/setup/projects/chain_clarity/
└── brand_profile.json
```

---

## STEP 4 — Plan Your Project (Roadmap)

Edit `youtube_scripts/setup/projects/{brand_slug}/roadmap.json`:

```json
[
  {
    "phase": 1,
    "title": "How Blockchain Works",
    "learning_goals": [
      "Understand what a block and chain are",
      "Explain consensus without jargon"
    ],
    "content_breakdown": [
      { "type": "long-form", "duration_min": 12 },
      { "type": "short-form", "duration_min": 1 },
      { "type": "infographic", "card_count": 3 }
    ]
  }
]
```

Or skip this step and pass `--topic` + `--outline` directly to `pipeline.py`.

---

## STEP 5 — Generate Content (Script + Briefs)

### Option A — From the Dashboard (recommended)

1. Open `http://localhost:8080`
2. Fill in **Step 1** — Project Name, Phase Number, Topic, Outline
3. Click through Steps 2–4 (TTS engine, render engine, platforms)
4. Go to **Step 5** → click **▶ Run on Server**
5. Watch live output in the terminal drawer at the bottom

### Option B — CLI

```bash
# Generate a new phase from scratch
python pipeline.py \
  --project chain_clarity \
  --phase 1 \
  --topic "How Blockchain Works — No Bank Required" \
  --outline "blocks and chains, consensus, immutability, why it matters"

# Skip content generation (re-run compliance + cuts on existing phase)
python pipeline.py \
  --project chain_clarity \
  --phase 1 \
  --skip-generate

# Skip voiceover too (only run compliance and platform cuts)
python pipeline.py \
  --project chain_clarity \
  --phase 1 \
  --skip-generate \
  --skip-voiceover
```

**Output — `phase_1/` folder created:**

| File | Description |
|------|-------------|
| `script.md` | Full narration script (12 min, brand voice enforced) |
| `script_short.md` | 60-second short-form cut |
| `voiceover_brief.md` | Pacing + emphasis guide for TTS |
| `music_brief.md` | BPM 88–112, mood, instrumentation |
| `clip_brief.md` | Shot-by-shot assembly guide |
| `infographics.md` | Layout specs for animated cards |
| `content_spec.json` | Platform cuts, tags, YouTube chapters |
| `subtitles.srt` | Auto-timed captions |
| `compliance_report_auto.md` | Brand audit (17 checks) |

---

## STEP 6 — Generate Voiceover (TTS)

Pick the engine that fits your setup:

```bash
# FREE — No GPU required (recommended for most users)
pip install kokoro soundfile
python tools/tts/kokoro_voiceover.py --phase 1 --voice af_heart

# FREE — Best quality (requires CUDA GPU 8GB+)
pip install chatterbox-tts torch torchaudio
python tools/tts/chatterbox_voiceover.py --phase 1 --reference voice_sample.wav

# PAID — Industry standard, fastest
pip install elevenlabs
python tools/tts/elevenlabs_voiceover.py --phase 1 --voice_id YOUR_VOICE_ID

# CURRENT DEFAULT — Qwen3-TTS / DashScope (requires DASHSCOPE_API_KEY)
python myvideo/edit/generate_voiceover.py --script youtube_scripts/setup/projects/chain_clarity/phase_1/script.md
```

**Output:** `phase_1/voiceover/phase_01.wav`

---

## STEP 7 — Build Infographic Cards

```bash
# Option A: Remotion — animated React components (best quality)
cd remotion
node scripts/render_all_cards.js --phase 1
cd ..

# Option B: HTML cards — open in browser, screenshot manually
# open: youtube_scripts/setup/projects/chain_clarity/phase_1/infographic_assets/card_01.html
```

**Preview cards in the browser:**

Open `http://localhost:8080/phase/chain_clarity/1` → click the **🃏 Infographics** tab.

Each card opens full-size in a new tab via **Open →**.

---

## STEP 8 — Assemble the Video

```bash
# FFmpeg + PIL (current pipeline)
python myvideo/edit/burn_text.py --phase 1

# MoviePy (upgraded pipeline)
python tools/render/moviepy_render.py --phase 1
```

**Output:** `_output/phase_01/youtube/final_1080p.mp4` (1920×1080, H.264)

---

## STEP 9 — Auto-Transcribe and Generate SRT

```bash
# FREE — CPU-friendly (no GPU needed)
python tools/transcribe.py --phase 1 --engine faster-whisper

# FREE — Best (requires GPU, word-level timestamps)
pip install whisperx
whisperx _output/phase_01/youtube/final_1080p.mp4 \
  --model large-v3-turbo --language en --word_timestamps True \
  --output_dir youtube_scripts/setup/projects/chain_clarity/phase_1/ \
  --output_format srt

# PAID — Auto YouTube chapters ($0.03/video)
python tools/transcribe.py --phase 1 --engine assemblyai
```

**Output:** `phase_1/subtitles_auto.srt`

---

## STEP 10 — Run Compliance Check

```bash
# Check one phase
python tools/compliance_checker.py --project chain_clarity --phase 1

# Check all phases
python tools/compliance_checker.py --project chain_clarity --phase all
```

All 17 brand checks must reach **PASS** or **PASS_WITH_WARNINGS** before publishing.

View compliance report in the browser:

```
http://localhost:8080/phase/chain_clarity/1
```

Click **✅ Compliance** tab.

---

## STEP 11 — Export Platform Clips

```bash
python tools/platform_cutter.py \
  --project chain_clarity \
  --phase 1 \
  --video _output/phase_01/youtube/final_1080p.mp4
```

**Output structure:**

```
_output/phase_01/
├── youtube/    final_1080p.mp4 · description.txt · subtitles.srt
├── tiktok/     clip_01_hook.mp4 (:15, 9:16) · clip_02_main.mp4 (:60, 9:16)
├── instagram/  reel_60s.mp4 · carousel_1.png · carousel_2.png · carousel_3.png
├── twitter/    card_clip.mp4 (:30) · thread.txt
├── linkedin/   clip.mp4 (:45) · article.md
├── blog/       post.md
└── github/     README.md
```

All clips include brand watermark (`#00D4AA` teal, top-right), content name overlay, and brand hashtags.

---

## STEP 12 — Generate Text Content

```bash
python tools/text_content_generator.py --project chain_clarity --phase 1
```

Requires `ANTHROPIC_API_KEY`. Generates:

| Platform | File | Description |
|----------|------|-------------|
| YouTube | `youtube/description.txt` | SEO description, chapter timestamps, tags |
| Twitter/X | `twitter/thread.txt` | 7-tweet thread (hook→insight→data→CTA) |
| LinkedIn | `linkedin/article.md` | 800-word professional article |
| Blog | `blog/post.md` | 1500-word SEO post + YouTube embed |
| Instagram | `instagram/caption_reel.txt` | Punchy caption + 15 hashtags |
| GitHub | `github/README.md` | Structured project README |

---

## STEP 13 — Review and Publish

```bash
# View the publish checklist
cat _output/phase_01/PIPELINE_SUMMARY.md
```

Or open the phase dashboard:

```
http://localhost:8080/phase/chain_clarity/1
```

The pipeline steps table shows exactly which steps are ✅ Done and ⬜ Pending. Click **▶ Run Pipeline** to re-run any step from the browser.

---

## Browser Dashboard Reference

### Main Dashboard — `http://localhost:8080`

- **Existing Projects** — table showing all phases with completion status
- **New Video Project** — 5-step wizard to configure and run the pipeline
- **▶ Run on Server** — executes pipeline and streams live output to browser terminal
- **Tool Matrix** — 38 tools across 7 stages with install commands

### Brand Setup — `http://localhost:8080/brand`

- Create and edit brand profiles (colors, fonts, tone, social links)
- Brand profile stored as `brand_profile.json` per project
- All generated content inherits brand colors, fonts, and tone rules
- Live logo preview, color swatches, forbidden words list

### Projects Browser — `http://localhost:8080/projects`

- **Favourites** — star any project to pin it at the top (saved in browser localStorage)
- **All Projects** — accordion list with phase breakdown
- **Sort** by name, completion %, or phase count
- **Search** to filter projects
- Each phase row links directly to its dashboard
- Copy pipeline command for any project

### Phase Dashboard — `http://localhost:8080/phase/{project}/{phase}`

Opens in a **new tab** per phase:

| Tab | Content |
|-----|---------|
| Overview | YouTube chapters, platform cuts, tags |
| Script | Full `script.md` with heading colors |
| Short Script | 60-second `script_short.md` |
| Infographics | Embedded card iframes + "Open full size" |
| Audio | Player (if voiceover exists) + voiceover brief |
| Video | Player (if rendered) + clip brief |
| Compliance | Full compliance report |
| All Files | Table of every file — click 👁 View to read inline |

---

## Quick Command Reference

| Goal | Command |
|------|---------|
| **Start dashboard** | `python server.py` |
| **Open dashboard** | `http://localhost:8080` |
| **Generate new phase** | `python pipeline.py --project chain_clarity --phase 6 --topic "NFTs" --outline "ERC-721, tickets, land registry"` |
| **Re-run existing phase** | `python pipeline.py --project chain_clarity --phase 1 --skip-generate` |
| **Compliance check only** | `python tools/compliance_checker.py --project chain_clarity --phase 1` |
| **Platform cuts only** | `python tools/platform_cutter.py --project chain_clarity --phase 1 --video path/to/final.mp4` |
| **Text content only** | `python tools/text_content_generator.py --project chain_clarity --phase 1` |
| **TTS — Kokoro (free)** | `python tools/tts/kokoro_voiceover.py --phase 1 --voice af_heart` |
| **TTS — Chatterbox (free GPU)** | `python tools/tts/chatterbox_voiceover.py --phase 1 --reference voice.wav` |
| **TTS — ElevenLabs (paid)** | `python tools/tts/elevenlabs_voiceover.py --phase 1 --voice_id YOUR_ID` |

---

## `pipeline.py` — All Flags

```bash
python pipeline.py [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--project` | `chain_clarity` | Project (brand) folder name |
| `--phase` | *(required)* | Phase number (integer) |
| `--topic` | — | Video title (required unless `--skip-generate`) |
| `--outline` | — | Key points / content outline |
| `--duration` | `12` | Target duration in minutes |
| `--tags` | `blockchain,crypto,web3,chainclarity` | Comma-separated tags |
| `--video` | — | Path to master video (enables platform cuts) |
| `--skip-generate` | off | Skip script + brief generation |
| `--skip-voiceover` | off | Skip voiceover generation |
| `--skip-remotion` | off | Skip Remotion card rendering |
| `--skip-text` | off | Skip text content generation |

---

## Chain Clarity — Current Status

| Phase | Topic | Script | Cards | SRT | Comply | VO | Video |
|-------|-------|--------|-------|-----|--------|----|-------|
| 1 | How Blockchain Works | ✅ | ✅ 4 | ✅ | ⚠️ PASS | ❌ | ❌ |
| 2 | Bitcoin vs Ethereum | ✅ | ✅ 3 | ✅ | ⚠️ PASS | ❌ | ❌ |
| 3 | DeFi & Smart Contracts | ✅ | ✅ 3 | ✅ | ⚠️ PASS | ❌ | ❌ |
| 4 | Security & Self-Custody | ✅ | ✅ 3 | ✅ | ⚠️ PASS | ❌ | ❌ |
| 5 | Blockchain Beyond Crypto | ✅ | ✅ 3 | ✅ | ⚠️ PASS | ❌ | ❌ |

**Next step for all phases:** Generate voiceover → assemble video → export platform clips.

```bash
# Run compliance check across all phases
python tools/compliance_checker.py --project chain_clarity --phase all
```

---

## TTS Engine Comparison

| Engine | Type | Cost | Quality | GPU? | Voice Clone |
|--------|------|------|---------|------|-------------|
| **ElevenLabs** | Paid | $5–22/mo | ⭐⭐⭐⭐⭐ | Cloud | Yes |
| **Chatterbox TTS** | Free MIT | $0 | ⭐⭐⭐⭐⭐ | Yes 8GB | Yes (5s ref) |
| **Kokoro-TTS** | Free Apache | $0 | ⭐⭐⭐⭐ | No (CPU) | No |
| **Qwen3-TTS** *(default)* | Freemium | Pay/use | ⭐⭐⭐⭐ | Partial | Yes |

**Pick by situation:**
- No GPU, free → **Kokoro-TTS**
- Has GPU, free + voice clone → **Chatterbox TTS**
- Paid, best quality → **ElevenLabs Creator** ($22/mo)
- Multilingual (Chinese/Japanese) → **Qwen3-TTS**

---

## Environment Variables

See `.env.example` for the full list. Minimum required:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Credits

- [HyperEdit](https://github.com/kevinbadi/hyperedit) — 3-agent architecture, intent routing, FFmpeg pattern
- [Remotion](https://remotion.dev) — Code-as-video React components
- [WhisperX](https://github.com/m-bain/whisperX) — Word-level transcription
- [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) — Open-source voice cloning
- [Kokoro-TTS](https://github.com/hexgrad/kokoro) — #1 TTS Arena open model
