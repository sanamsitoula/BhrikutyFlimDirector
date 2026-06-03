# Bhrikuty Film Director

<div align="center">

**AI-powered content factory — Brand → Project → 7-Platform Content Package**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green?style=flat-square&logo=node.js)](https://nodejs.org)
[![Claude API](https://img.shields.io/badge/Claude-Sonnet_4.6-orange?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

[Quick Start](#quick-start) · [Dashboard](#dashboard-pages) · [Getting Started Guide](GETTING_STARTED.md) · [Live Demo](#chain-clarity--live-example)

</div>

---

## What is Bhrikuty?

Bhrikuty is an end-to-end content production system. You give it a **topic** and it produces a fully **brand-compliant 7-platform content package** — YouTube video script, TikTok clips, Instagram reels, Twitter thread, LinkedIn article, blog post, and GitHub README — all driven by a single pipeline command.

The system is built around three layers:

```
Brand  →  Project  →  Content
  ↓           ↓           ↓
Colors      Topic      Script
Fonts       Phase      Voiceover
Tone        Outline    Infographic Cards
Pillars     Roadmap    Platform Clips
Social                 Text Content
```

---

## How It Works

```
                        TOPIC + OUTLINE
                               │
                               ▼
              ┌────────────────────────────────┐
              │     DIRECTOR (pipeline.py)      │
              │  Script · Briefs · Compliance   │
              └──────────────┬─────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
  │   PICASSO    │  │   DiCAPRIO   │  │  TEXT ENGINE     │
  │  Infographics│  │  Video Cuts  │  │  Blog · Thread   │
  │  Remotion    │  │  platform_   │  │  LinkedIn · YT   │
  │  HTML Cards  │  │  cutter.py   │  │  Instagram · GH  │
  └──────────────┘  └──────────────┘  └──────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
              ┌────────────────────────────────┐
              │      COMPLIANCE CHECKER        │
              │     17 brand rules validated   │
              └──────────────┬─────────────────┘
                             │
                             ▼
              ┌────────────────────────────────┐
              │       _output/phase_XX/        │
              │  youtube/  tiktok/  instagram/ │
              │  twitter/  linkedin/ blog/     │
              │  github/   publish_checklist   │
              └────────────────────────────────┘
```

---

## Quick Start

**You need:** Python 3.11+, Node.js 18+, FFmpeg, and an Anthropic API key.

```bash
# 1. Clone the repo
git clone https://github.com/sanamsitoula/BhrikutyFlimDirector.git
cd BhrikutyFlimDirector

# 2. Install Python packages
pip install anthropic moviepy faster-whisper

# 3. Install Remotion
cd remotion && npm install && cd ..

# 4. Set up your API key
copy .env.example .env
# Open .env → add: ANTHROPIC_API_KEY=sk-ant-...

# 5. Start the dashboard
python server.py
```

Open **http://localhost:8080** in your browser.

> Full step-by-step instructions with screenshots and troubleshooting: **[GETTING_STARTED.md](GETTING_STARTED.md)**

---

## Dashboard Pages

| URL | Page | What you do there |
|-----|------|-------------------|
| `http://localhost:8080/` | **Main Dashboard** | Run the pipeline, watch live output, view project status |
| `http://localhost:8080/brand` | **Brand Setup** | Create your brand — colors, fonts, tone, social links |
| `http://localhost:8080/projects` | **Projects Browser** | Favourite projects, search, view all phases at a glance |
| `http://localhost:8080/phase/{project}/{num}` | **Phase Dashboard** | View scripts, infographics, compliance — per phase |

---

## Chain Clarity — Live Example

The **Chain Clarity** brand comes pre-loaded as a working example — 5 completed phases of blockchain education content.

| Phase | Title | Duration | Script | Cards | SRT | Comply |
|-------|-------|----------|--------|-------|-----|--------|
| 1 | How Blockchain Works — No Bank Required | 12 min | ✅ | ✅ 4 | ✅ | ⚠️ PASS |
| 2 | Bitcoin vs Ethereum — What's Actually Different | 14 min | ✅ | ✅ 3 | ✅ | ⚠️ PASS |
| 3 | DeFi Explained — Your Bank Has No CEO | 13 min | ✅ | ✅ 3 | ✅ | ⚠️ PASS |
| 4 | How Crypto Gets Stolen — And How to Stop It | 11 min | ✅ | ✅ 3 | ✅ | ⚠️ PASS |
| 5 | Blockchain Is Not Just Crypto — Real Use Cases | 12 min | ✅ | ✅ 3 | ✅ | ⚠️ PASS |

Browse any phase at `http://localhost:8080/phase/chain_clarity/1`

---

## Platform Output

One pipeline run produces a complete package for every platform:

| Platform | Files produced | Specs |
|----------|---------------|-------|
| **YouTube** | `final_1080p.mp4` · `description.txt` · `subtitles.srt` | 1920×1080, H.264, SEO description, timestamps |
| **TikTok** | `clip_01_hook.mp4` · `clip_02_main.mp4` | 1080×1920, 9:16, :15 hook + :60 main |
| **Instagram** | `reel_60s.mp4` · `carousel_1–3.png` · `caption.txt` | 9:16 reel + 1:1 carousel |
| **Twitter/X** | `thread.txt` · `card_clip.mp4` | 7-tweet thread + :30 clip |
| **LinkedIn** | `article.md` · `clip.mp4` | 800-word article + :45 clip |
| **Blog** | `post.md` | 1,500-word SEO post with YouTube embed |
| **GitHub** | `README.md` | Structured project README |

---

## Project Structure

```
BhrikutyFlimDirector/
│
├── server.py                    ← Web dashboard server — run this first
├── pipeline.py                  ← CLI entry point — Film Director
├── dashboard.html               ← Main pipeline control UI
├── brand.html                   ← Brand creation & management
├── projects.html                ← Projects browser with favourites
├── phase_dashboard.html         ← Per-phase content dashboard
├── .env.example                 ← Copy to .env, fill in API keys
├── GETTING_STARTED.md           ← Full 17-step setup guide
│
├── tools/
│   ├── generate_phase.py        ← AI script + brief generation
│   ├── compliance_checker.py    ← 17 brand rule checks
│   ├── platform_cutter.py       ← Platform-specific video exports
│   ├── text_content_generator.py← Blog · thread · article · README
│   ├── TOOL_GUIDE.md            ← Tool installation and code samples
│   └── tts/
│       ├── kokoro_voiceover.py  ← Free CPU voiceover
│       ├── chatterbox_voiceover.py ← Free GPU voiceover (voice clone)
│       └── elevenlabs_voiceover.py ← Paid voiceover (best quality)
│
├── remotion/                    ← Animated infographic cards (React)
│   ├── package.json
│   └── scripts/render_all_cards.js
│
├── myvideo/edit/
│   ├── burn_text.py             ← Text overlay on video
│   ├── generate_voiceover.py    ← Qwen3-TTS (current default)
│   └── clean_voice.py           ← Audio cleanup
│
└── youtube_scripts/setup/projects/
    └── {brand_slug}/            ← One folder per brand
        ├── brand_profile.json   ← Colors, fonts, tone, social links
        ├── roadmap.json         ← Phase plan
        ├── tags_and_metadata.json
        ├── phase_1/
        │   ├── script.md
        │   ├── script_short.md
        │   ├── subtitles.srt
        │   ├── voiceover_brief.md
        │   ├── clip_brief.md
        │   ├── music_brief.md
        │   ├── infographics.md
        │   ├── content_spec.json
        │   ├── compliance_report_auto.md
        │   └── infographic_assets/
        │       ├── card_01.html
        │       └── card_02.html
        ├── phase_2/ … phase_N/
        └── _output/
            └── phase_01/
                ├── youtube/
                ├── tiktok/
                ├── instagram/
                ├── twitter/
                ├── linkedin/
                ├── blog/
                └── github/
```

---

## Brand Setup

Create your brand identity at `http://localhost:8080/brand`. Everything you set here flows into every piece of generated content.

| Setting | Example (Chain Clarity) |
|---------|------------------------|
| **Brand Name** | Chain Clarity |
| **Tagline** | Blockchain, without the noise. |
| **Niche** | Blockchain & Crypto Education |
| **Primary Color** | `#00D4AA` — Electric Teal |
| **Secondary Color** | `#F5A623` — Deep Gold |
| **Background** | `#0A0E1A` — Deep Navy |
| **Highlight** | `#7B5CF0` — Electric Violet |
| **Heading Font** | Space Grotesk |
| **Body Font** | Inter |
| **Platforms** | YouTube · TikTok · Instagram |
| **Forbidden Words** | moon, lambo, HODL, simply, obviously, easy, guaranteed |

Brand profile saved to `{project}/brand_profile.json` — versioned with the project.

---

## Content Generation

### From the Dashboard (no terminal needed)

1. Open `http://localhost:8080`
2. Fill in **New Video Project** — topic, phase, outline
3. Click **▶ Run on Server**
4. Watch live output in the terminal drawer

### From the Terminal

```bash
python pipeline.py \
  --project chain_clarity \
  --phase 6 \
  --topic "How NFTs Actually Work" \
  --outline "ERC-721 standard, real use cases, concert tickets, land registry, resale royalties" \
  --duration 12 \
  --tags "nft,blockchain,crypto,web3,chainclarity"
```

### All pipeline flags

| Flag | Default | Description |
|------|---------|-------------|
| `--project` | `chain_clarity` | Brand/project folder name |
| `--phase` | *(required)* | Phase number |
| `--topic` | — | Video title |
| `--outline` | — | Key points |
| `--duration` | `12` | Target minutes |
| `--tags` | `blockchain,crypto,web3` | Comma-separated tags |
| `--video` | — | Path to master video (enables cuts) |
| `--skip-generate` | off | Skip script generation |
| `--skip-voiceover` | off | Skip voiceover |
| `--skip-remotion` | off | Skip card rendering |
| `--skip-text` | off | Skip text content |

---

## Voiceover / TTS

Choose the engine that fits your budget and hardware:

| Engine | Cost | GPU? | Voice Clone | Quality | Command |
|--------|------|------|-------------|---------|---------|
| **Kokoro-TTS** | Free | No | No | ⭐⭐⭐⭐ | `pip install kokoro soundfile` |
| **Chatterbox TTS** | Free | Yes (8GB) | Yes (5s ref) | ⭐⭐⭐⭐⭐ | `pip install chatterbox-tts torch` |
| **ElevenLabs** | $5–22/mo | Cloud | Yes | ⭐⭐⭐⭐⭐ | `pip install elevenlabs` |
| **Qwen3-TTS** | Pay/use | Partial | Yes | ⭐⭐⭐⭐ | `pip install dashscope` |

```bash
# Kokoro — free, no GPU
python tools/tts/kokoro_voiceover.py --phase 1 --voice af_heart

# Chatterbox — free, GPU required
python tools/tts/chatterbox_voiceover.py --phase 1 --reference voice.wav

# ElevenLabs — paid, best quality
python tools/tts/elevenlabs_voiceover.py --phase 1 --voice_id YOUR_VOICE_ID
```

---

## Compliance Checker

All generated content is automatically checked against 17 brand rules:

```bash
# Check one phase
python tools/compliance_checker.py --project chain_clarity --phase 1

# Check all phases
python tools/compliance_checker.py --project chain_clarity --phase all
```

Checks include: tone of voice, color codes, typography, subtitle length, forbidden words, brand hashtags, animation sequences, and more.

Results: **PASS** · **PASS_WITH_WARNINGS** · **FAIL**

---

## Phase Dashboard

Every phase has its own browser dashboard at:

```
http://localhost:8080/phase/{project}/{phase_number}
```

| Tab | Content |
|-----|---------|
| Overview | YouTube chapters, platform cut timestamps, keyword tags |
| Script | Full `script.md` — color-coded headings, inline copy |
| Short Script | 60-second `script_short.md` for TikTok/Reels |
| Infographics | Live iframe previews of all card HTML files |
| Audio | Player when voiceover exists · voiceover brief when not |
| Video | Player when rendered · clip brief when not |
| Compliance | Full compliance report with pass/warn/fail per check |
| All Files | Every source file — click to view, click to copy |

The **Pipeline Steps** table at the top shows exactly what is done and what is pending for every phase, with action buttons for each step.

---

## Projects Browser

`http://localhost:8080/projects`

- ⭐ **Favourite** any project — pinned to the top, saved in localStorage
- 🔍 **Search** projects by name
- **Sort** by name, completion %, or phase count
- Each row expands to show all phases with compliance badges and open links
- Click **↗ Open** on any phase to open its dedicated dashboard in a new tab

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
# REQUIRED
ANTHROPIC_API_KEY=sk-ant-api03-...

# TTS — pick one
ELEVENLABS_API_KEY=          # paid, best quality
DASHSCOPE_API_KEY=           # freemium, Qwen3-TTS
# Kokoro and Chatterbox run fully locally — no key needed

# Transcription — optional
ASSEMBLYAI_API_KEY=          # $0.03/video, auto YouTube chapters
DEEPGRAM_API_KEY=            # lowest latency

# Image generation — optional
BFL_API_KEY=                 # FLUX.1 pro, $0.055/image
IDEOGRAM_API_KEY=            # best text-in-image, $0.08/image

# Video B-roll — optional
RUNWAY_API_KEY=              # Gen-4, $0.05/sec
KLING_API_KEY=               # $7.99/mo
```

---

## Cost to Run

| Approach | Monthly Cost | What you get |
|----------|-------------|-------------|
| **All free** | $0 | Kokoro-TTS · faster-whisper · HTML cards · FFmpeg · Claude free credits |
| **Hybrid** | ~$18–21 | ElevenLabs $5 · AssemblyAI ~$2 · Kling AI $8 · Claude API ~$3 |
| **Full paid** | ~$50+ | ElevenLabs Creator $22 · Runway Gen-4 · Ideogram · AssemblyAI |

---

## Quick Command Reference

```bash
# Start dashboard server
python server.py

# Generate new phase
python pipeline.py --project BRAND --phase N --topic "Title" --outline "point1, point2"

# Re-run existing phase (skip script generation)
python pipeline.py --project BRAND --phase N --skip-generate

# Voiceover only
python tools/tts/kokoro_voiceover.py --phase N --voice af_heart

# Compliance check
python tools/compliance_checker.py --project BRAND --phase N

# Platform cuts
python tools/platform_cutter.py --project BRAND --phase N --video path/to/video.mp4

# Text content (blog, thread, article)
python tools/text_content_generator.py --project BRAND --phase N
```

---

## Requirements

```
Python     3.11+
Node.js    18+
FFmpeg     (any recent version)
```

```bash
# Python packages
pip install anthropic moviepy faster-whisper

# Optional TTS
pip install kokoro soundfile
pip install elevenlabs
pip install chatterbox-tts torch torchaudio

# Optional transcription
pip install whisperx

# Remotion
cd remotion && npm install
```

---

## Credits & Inspirations

### Architecture
- [HyperEdit](https://github.com/kevinbadi/hyperedit) — 3-agent Director/Picasso/DiCaprio architecture and intent routing

### AI & Generation
- [Anthropic Claude](https://anthropic.com) — script generation, text content, compliance analysis
- [Claude Code](https://claude.ai/code) — built the entire web dashboard during development

### Voiceover
- [Kokoro-TTS](https://github.com/hexgrad/kokoro) · [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) · [ElevenLabs](https://elevenlabs.io) · [Qwen3-TTS](https://dashscope.aliyuncs.com) · [F5-TTS](https://github.com/SWivid/F5-TTS)

### Video
- [FFmpeg](https://ffmpeg.org) · [MoviePy](https://zulko.github.io/moviepy/) · [Remotion](https://remotion.dev) · [Motion Canvas](https://motioncanvas.io)

### Transcription
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [WhisperX](https://github.com/m-bain/whisperX) · [AssemblyAI](https://assemblyai.com) · [Deepgram](https://deepgram.com)

### Images
- [FLUX.1](https://blackforestlabs.ai) · [Ideogram](https://ideogram.ai) · [Recraft](https://recraft.ai) · [Midjourney](https://midjourney.com)

### Publishing Platforms
YouTube · TikTok · Instagram · Twitter/X · LinkedIn · Blog · GitHub

### Creator Inspirations

| Category | Creators |
|----------|---------|
| Blockchain education | Whiteboard Crypto · Coin Bureau · Andreas Antonopoulos · Finematics · Patrick Collins |
| Tech explainers | Fireship · 3Blue1Brown · Kurzgesagt · Veritasium |
| Coding education | Traversy Media · Theo t3.gg · NetworkChuck |
| Content strategy | Ali Abdaal · MKBHD · Colin and Samir · Alex Hormozi |

### Fonts
[Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) · [Inter](https://fonts.google.com/specimen/Inter) · [JetBrains Mono](https://www.jetbrains.com/legalforms/fonts/)

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Built with ❤️ for content creators who want to work smarter, not harder.

**[⭐ Star this repo](https://github.com/sanamsitoula/BhrikutyFlimDirector)** if it saves you time.

</div>
