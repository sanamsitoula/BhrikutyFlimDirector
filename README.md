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

## Credits & Acknowledgements

Bhrikuty is built on the shoulders of outstanding open-source projects, APIs, and platforms. Full credit to every tool and team listed below.

---

### Architecture Inspiration

| Project | Author | What we borrowed |
|---------|--------|-----------------|
| [HyperEdit](https://github.com/kevinbadi/hyperedit) | Kevin Badi | 3-agent Director/Picasso/DiCaprio architecture, context-aware intent routing, FFmpeg server pattern, dead-air removal |

---

### AI & Script Generation

| Tool | Provider | Usage in Bhrikuty |
|------|----------|-------------------|
| [Claude API — Sonnet 4.6](https://www.anthropic.com/claude) | Anthropic | Script generation, text content (blog, LinkedIn, thread, YouTube description), compliance analysis |
| [Claude Code](https://claude.ai/code) | Anthropic | Built the entire web dashboard, server, and pipeline tooling during development |

---

### Text-to-Speech / Voiceover

| Tool | License | Usage in Bhrikuty |
|------|---------|-------------------|
| [ElevenLabs](https://elevenlabs.io) | Commercial | Paid TTS option — `tools/tts/elevenlabs_voiceover.py` |
| [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) | MIT | Free GPU TTS with voice cloning — `tools/tts/chatterbox_voiceover.py` |
| [Kokoro-TTS](https://github.com/hexgrad/kokoro) | Apache 2.0 | Free CPU-capable TTS, #1 on TTS Arena — `tools/tts/kokoro_voiceover.py` |
| [Qwen3-TTS / DashScope](https://dashscope.aliyuncs.com) | Freemium | Current default multilingual TTS — `myvideo/edit/generate_voiceover.py` |
| [F5-TTS](https://github.com/SWivid/F5-TTS) | MIT | Alternative free GPU TTS with EN/ZH bilingual support |
| [XTTS-v2](https://github.com/coqui-ai/TTS) | Custom | 17-language voice cloning via Coqui TTS |
| [StyleTTS2](https://github.com/yl4579/StyleTTS2) | MIT | High-quality English TTS alternative |
| [OpenVoice v2](https://github.com/myshell-ai/OpenVoice) | MIT | Cross-lingual voice cloning |
| [Piper TTS](https://github.com/rhasspy/piper) | MIT | Lightweight multilingual offline TTS |

---

### Video Rendering & Motion Graphics

| Tool | License | Usage in Bhrikuty |
|------|---------|-------------------|
| [FFmpeg](https://ffmpeg.org) | LGPL/GPL | Base video layer — transcoding, audio normalization, dead-air removal, format conversion |
| [MoviePy](https://zulko.github.io/moviepy/) | MIT | Python-native video compositing — `tools/render/moviepy_render.py` |
| [Remotion](https://remotion.dev) | Freemium | React-based animated infographic cards — `remotion/` |
| [Motion Canvas](https://motioncanvas.io) | MIT | 3Blue1Brown-style mathematical explainer animations |
| [Revideo](https://re.video) | MIT | Remotion fork with rendering API |
| [Runway Gen-4](https://runwayml.com) | Commercial | AI-generated cinematic B-roll (~$0.05/sec) |
| [Kling AI](https://klingai.com) | Commercial | Cost-effective AI B-roll ($7.99/mo) |
| [Creatomate](https://creatomate.com) | Commercial | JSON-template video rendering API (~$0.38/min) |
| [DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve) | Free/Paid | Pro color grading and manual editing |

---

### Transcription & Subtitles

| Tool | License | Usage in Bhrikuty |
|------|---------|-------------------|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT | Default free CPU transcription — `tools/transcribe.py` |
| [WhisperX](https://github.com/m-bain/whisperX) | BSD-4 | GPU-accelerated word-level transcription with speaker diarization |
| [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) | MIT | Apple Silicon / CPU whisper — no Python dependency |
| [Gladia Solaria-1](https://www.gladia.io) | Commercial | Paid transcription with 100-language translation (~$0.04/video) |
| [AssemblyAI Universal-2](https://www.assemblyai.com) | Commercial | Paid transcription with auto YouTube chapters (~$0.03/video) |
| [Deepgram Nova-3](https://deepgram.com) | Commercial | Lowest-latency cloud transcription — best for live streaming |

---

### Thumbnail & Image Generation

| Tool | License | Usage in Bhrikuty |
|------|---------|-------------------|
| [FLUX.1 schnell](https://blackforestlabs.ai) | Apache 2.0 | Local GPU thumbnail generation (24GB VRAM) |
| [FLUX.1 pro via BFL API](https://api.bfl.ml) | Commercial | Cloud FLUX — no GPU needed (~$0.055/image) |
| [Ideogram v2](https://ideogram.ai) | Commercial | Best text-in-image rendering (~$0.08/image) |
| [Recraft v3](https://www.recraft.ai) | Commercial | Vector-style brand graphics, SVG output |
| [Midjourney v6.1](https://www.midjourney.com) | Commercial | Highest aesthetic quality for hero images |
| [DALL-E 3](https://openai.com/dall-e-3) | Commercial | OpenAI image generation (~$0.04/image) |
| [Adobe Firefly 3](https://firefly.adobe.com) | Commercial | IP-indemnified images for monetized content |
| [Stable Diffusion / ComfyUI](https://github.com/comfyanonymous/ComfyUI) | GPL | Local image generation with LoRA fine-tuning |

---

### Workflow Orchestration

| Tool | License | Usage in Bhrikuty |
|------|---------|-------------------|
| `pipeline.py` | MIT | Custom Python director — the current orchestration layer |
| [n8n](https://n8n.io) | Fair-code | Visual 400+ integration workflow builder (self-hostable) |
| [CrewAI](https://www.crewai.com) | MIT | Role-based multi-agent orchestration |
| [Dify](https://dify.ai) | Apache 2.0 | Visual LLMOps pipeline builder with RAG |
| [Flowise](https://flowiseai.com) | MIT | Drag-and-drop LLM flows |
| [Prefect](https://www.prefect.io) | Apache 2.0 | Python-native workflow with retries and caching |
| [Temporal](https://temporal.io) | MIT SDK | Durable fault-tolerant workflow for GPU workloads |

---

### Publishing Platforms

| Platform | What Bhrikuty creates for it |
|----------|------------------------------|
| [YouTube](https://www.youtube.com) | `final_1080p.mp4` · `description.txt` · `subtitles.srt` · thumbnail · chapters |
| [TikTok](https://www.tiktok.com) | `clip_01_hook.mp4` (:15, 9:16) · `clip_02_main.mp4` (:60, 9:16) |
| [Instagram](https://www.instagram.com) | `reel_60s.mp4` · `carousel_1–3.png` · `caption_reel.txt` |
| [Twitter / X](https://twitter.com) | `card_clip.mp4` (:30) · `thread.txt` (7-tweet breakdown) |
| [LinkedIn](https://www.linkedin.com) | `clip.mp4` (:45) · `article.md` (800-word professional article) |
| [Blog / Website](https://wordpress.org) | `post.md` (1500-word SEO post with YouTube embed) |
| [GitHub](https://github.com) | `README.md` (structured project README with code samples) |

---

### Content Creation APIs & Publishing Tools

| Tool | Purpose |
|------|---------|
| [YouTube Data API v3](https://developers.google.com/youtube/v3) | Automated upload — title, description, tags, SRT, thumbnail, scheduled publish |
| [Metricool](https://metricool.com) | Multi-platform scheduling and analytics |
| [n8n YouTube Node](https://n8n.io/integrations/youtube/) | Combined pipeline + publishing in one workflow |

---

### Fonts

| Font | Foundry | Usage |
|------|---------|-------|
| [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) | Florian Karsten | All headings across dashboard, cards, and brand assets |
| [Inter](https://fonts.google.com/specimen/Inter) | Rasmus Andersson | Body text across all UI pages |
| [JetBrains Mono](https://www.jetbrains.com/legalforms/fonts/) | JetBrains | Code overlays and infographic card monospace text |

---

### Web Dashboard (Built in this project)

| File | What it does |
|------|-------------|
| `server.py` | Zero-dependency Python HTTP server with SSE streaming and threaded request handling |
| `dashboard.html` | Main pipeline control — 5-step wizard, live terminal drawer, projects status table |
| `brand.html` | Brand identity setup — colors, fonts, tone of voice, social links, content pillars |
| `projects.html` | Projects browser — favourites (localStorage), search, sort, accordion phase list |
| `phase_dashboard.html` | Per-phase dashboard — pipeline steps, file viewer, infographic iframes, audio/video players |

---

### Python Libraries

| Library | Usage |
|---------|-------|
| [anthropic](https://pypi.org/project/anthropic/) | Claude API for script and text generation |
| [moviepy](https://pypi.org/project/moviepy/) | Video compositing and rendering |
| [faster-whisper](https://pypi.org/project/faster-whisper/) | Audio transcription |
| [kokoro](https://pypi.org/project/kokoro/) | Kokoro-TTS voiceover |
| [soundfile](https://pypi.org/project/soundfile/) | Audio file I/O |
| [elevenlabs](https://pypi.org/project/elevenlabs/) | ElevenLabs TTS API |
| [dashscope](https://pypi.org/project/dashscope/) | Qwen3-TTS / DashScope API |
| [chatterbox-tts](https://pypi.org/project/chatterbox-tts/) | Chatterbox voice cloning TTS |
| [torch / torchaudio](https://pytorch.org) | GPU inference for Chatterbox and WhisperX |

---

### Node.js Packages (Remotion)

| Package | Usage |
|---------|-------|
| [remotion](https://www.npmjs.com/package/remotion) | Core Remotion video rendering |
| [@remotion/player](https://www.npmjs.com/package/@remotion/player) | In-browser preview |
| [@remotion/renderer](https://www.npmjs.com/package/@remotion/renderer) | Server-side render to MP4 |

---

### Special Thanks

- **[Chain Clarity](https://github.com/sanamsitoula/BhrikutyFlimDirector)** — the flagship brand built with this system, covering blockchain education across 7 platforms
- **[Anthropic](https://www.anthropic.com)** — for Claude, the AI that generates every script, article, thread, and README in this pipeline
- **The open-source community** — every free tool in this stack represents thousands of hours of contributed work
