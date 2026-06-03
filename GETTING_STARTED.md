# Getting Started — Step by Step

> Complete guide to install, set up, create a brand, create a project, and generate your first video.
> Tested on Windows 11 with Python 3.12 and Node.js 24.

---

## What you will have at the end

```
Brand (e.g. "Chain Clarity")
 └── Project / Phase (e.g. Phase 6 — "How NFTs Work")
      ├── script.md          ← full 12-min narration script
      ├── script_short.md    ← 60-second TikTok cut
      ├── subtitles.srt      ← captions
      ├── voiceover_brief.md ← pacing guide for TTS
      ├── clip_brief.md      ← shot-by-shot video guide
      ├── infographics.md    ← card layout specs
      ├── content_spec.json  ← YouTube chapters, platform cuts, tags
      └── infographic_assets/
           ├── card_01.html
           ├── card_02.html
           └── card_03.html
```

Everything viewable and runnable from the browser at `http://localhost:8080`.

---

## STEP 1 — Install FFmpeg

FFmpeg is required to cut video clips for each platform.

**Windows (PowerShell as Administrator):**
```powershell
winget install --id Gyan.FFmpeg -e
```

Then **close and reopen your terminal**, then verify:
```bash
ffmpeg -version
```

You should see something like `ffmpeg version 7.x.x`.

> If `winget` is not available, download from https://ffmpeg.org/download.html  
> Extract it, add the `bin/` folder to your System PATH.

---

## STEP 2 — Install Python Packages

Open a terminal in the project folder:

```bash
cd c:\claude_projects\bhrikuty
```

Install all required packages:

```bash
pip install anthropic moviepy faster-whisper
```

This installs:
- `anthropic` — Claude API for script generation (required)
- `moviepy` — video compositing
- `faster-whisper` — free local audio transcription

**Verify:**
```bash
python -c "import anthropic; print('OK')"
```

---

## STEP 3 — Install Remotion (for Infographic Cards)

```bash
cd remotion
npm install
cd ..
```

This downloads all React/Remotion packages needed to render animated infographic cards.

**Verify:**
```bash
node remotion/node_modules/.bin/remotion --version
```

---

## STEP 4 — Get Your Anthropic API Key

1. Go to **https://console.anthropic.com**
2. Sign in or create a free account
3. Click **API Keys** in the left sidebar
4. Click **Create Key**
5. Copy the key — it starts with `sk-ant-api03-...`

> The free tier gives you enough credits to generate several scripts.

---

## STEP 5 — Create Your .env File

In the project folder, copy the example file:

**Windows:**
```bash
copy .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

Now open `.env` in any text editor (Notepad, VS Code, etc.) and fill in your key:

```env
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Leave everything else blank for now — all other keys are optional.

**Save the file.** Never share or commit this file.

---

## STEP 6 — Start the Dashboard Server

```bash
python server.py
```

You will see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Bhrikuty Film Director — Dashboard Server
  Open: http://localhost:8080
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Open your browser and go to:

```
http://localhost:8080
```

**Keep this terminal open** — the server must stay running while you use the dashboard.

> To stop the server: press `Ctrl + C` in the terminal.

---

## STEP 7 — Create a Brand

Go to: **http://localhost:8080/brand**

Click **+ New Brand** and fill in the form:

### Required fields

| Field | What to enter | Example |
|-------|--------------|---------|
| **Brand / Company Name** | Your channel or company name | `Chain Clarity` |
| **Brand Slug** | Auto-filled from name — letters and underscores only | `chain_clarity` |
| **Tagline** | One-line brand promise | `Blockchain, without the noise.` |
| **Niche / Industry** | Your content category | `Blockchain & Crypto Education` |
| **Target Audience** | Who watches your content | `Curious learners 22–40 who want to understand crypto technically` |

### Color Palette

Click each color box to open the color picker, or type a hex code directly:

| Slot | What it's for | Suggested color |
|------|--------------|-----------------|
| **Primary** | Headers, CTAs, key stats | `#00D4AA` (teal) |
| **Secondary** | Accents, icons | `#F5A623` (gold) |
| **Neutral** | Body text | `#8B9BB4` (slate) |
| **Background** | Page/card backgrounds | `#0A0E1A` (dark navy) |
| **Highlight** | Pull quotes, chapter markers | `#7B5CF0` (violet) |

### Typography

| Field | Value |
|-------|-------|
| Heading Font | `Space Grotesk` |
| Body Font | `Inter` |
| Code Font | `JetBrains Mono` |

### Platforms (check all you target)

- ✅ YouTube
- ✅ TikTok
- ✅ Instagram
- ✅ Twitter/X
- ✅ LinkedIn

### Content Pillars

Click **+ Add Pillar** for each topic series. Example:
1. How Blockchain Works
2. Cryptocurrency Fundamentals
3. DeFi & Smart Contracts
4. Security & Self-Custody
5. Real-World Blockchain Applications

### Tone of Voice

| Field | What to write |
|-------|--------------|
| **Primary Tone** | `Trusted senior engineer explaining to a sharp student — clear, direct, never hype-driven` |
| **Sentence Style** | `Short declarative sentences. Max 15 words. No passive voice. Lead with the concept.` |
| **Forbidden Words** | `moon, lambo, HODL, simply, just, obviously, easy, guaranteed, rich, explosive` |

### Social Links

Add your channel URLs:
- YouTube: `https://www.youtube.com/@yourchannel`
- Instagram: `https://www.instagram.com/yourchannel`
- TikTok: `https://www.tiktok.com/@yourchannel`

### Save

Click **💾 Create Brand**

**What happens:** Creates the folder `youtube_scripts/setup/projects/chain_clarity/brand_profile.json` with all your brand settings. Every piece of content generated will respect these rules.

---

## STEP 8 — Plan Your Project

Your brand is set. Now plan what videos to make.

Open (or create) the roadmap file:

```
youtube_scripts/setup/projects/chain_clarity/roadmap.json
```

Add phases like this:

```json
[
  {
    "phase": 1,
    "title": "How Blockchain Works",
    "learning_goals": [
      "Understand what a block is",
      "Explain consensus without jargon",
      "Know why blockchain is different from a database"
    ],
    "content_breakdown": [
      { "type": "long-form", "duration_min": 12 },
      { "type": "short-form", "duration_min": 1 },
      { "type": "infographic", "card_count": 3 }
    ]
  },
  {
    "phase": 2,
    "title": "Bitcoin vs Ethereum",
    "learning_goals": [
      "Understand Proof of Work vs Proof of Stake",
      "Know what makes Ethereum programmable"
    ],
    "content_breakdown": [
      { "type": "long-form", "duration_min": 14 },
      { "type": "short-form", "duration_min": 1 },
      { "type": "infographic", "card_count": 3 }
    ]
  }
]
```

> You can skip this step and just pass `--topic` and `--outline` directly in the next step.

---

## STEP 9 — Generate Your First Video Content

This is where the AI writes the script, briefs, captions, and infographic specs.

### Option A — From the Browser (easiest)

1. Go to **http://localhost:8080**
2. Scroll to **New Video Project**
3. Fill in **Step 1 — Topic & Outline**:

   | Field | Example |
   |-------|---------|
   | Project Name | `chain_clarity` |
   | Phase Number | `1` |
   | Video Topic | `How Blockchain Works — No Bank Required` |
   | Duration | `12` |
   | Tags | `blockchain,crypto,web3,chainclarity` |
   | Outline | `1. What is a block 2. What is the chain 3. How consensus works 4. Why immutability matters 5. What blockchain cannot do` |

4. Click **Next** through Steps 2–4 (keep defaults)
5. On **Step 5**, click **▶ Run on Server**
6. Watch the terminal at the bottom of the page — live output streams in

### Option B — From the Terminal

```bash
python pipeline.py \
  --project chain_clarity \
  --phase 1 \
  --topic "How Blockchain Works — No Bank Required" \
  --outline "blocks and chains, consensus, immutability, what blockchain cannot do" \
  --duration 12 \
  --tags "blockchain,crypto,web3,chainclarity"
```

**Windows PowerShell (single line):**
```powershell
python pipeline.py --project chain_clarity --phase 1 --topic "How Blockchain Works" --outline "blocks, chains, consensus, immutability" --duration 12
```

### What gets created

After 1–3 minutes (depending on Claude API speed):

```
youtube_scripts/setup/projects/chain_clarity/phase_1/
├── script.md                  ← ~3,000 words, 12-min narration
├── script_short.md            ← ~400 words, 60-second cut
├── voiceover_brief.md         ← pacing and emphasis guide
├── clip_brief.md              ← 38 shot-by-shot instructions
├── music_brief.md             ← BPM, mood, genre guidance
├── infographics.md            ← 3-card layout specs
├── content_spec.json          ← YouTube chapters, platform cuts, tags
├── subtitles.srt              ← auto-timed captions
├── compliance_report_auto.md  ← 17 brand rule checks
└── infographic_assets/
    ├── card_01.html
    ├── card_02.html
    └── card_03.html
```

---

## STEP 10 — View Your Content in the Browser

Go to the phase dashboard:

```
http://localhost:8080/phase/chain_clarity/1
```

Here you can:

| Tab | What you see |
|-----|-------------|
| **Overview** | YouTube chapters, platform cut timestamps, tags |
| **Script** | Full color-coded script — click 📋 to copy |
| **Short Script** | The 60-second TikTok/Reels cut |
| **Infographics** | Live preview of all card HTML files |
| **Subtitles** | SRT file with color-coded timestamps |
| **Compliance** | Pass/Warn/Fail for all 17 brand rules |
| **All Files** | Every file — click 👁 to read, 📋 to copy |

Click **Open →** on any infographic card to view it full size in a new tab.

---

## STEP 11 — Generate Voiceover

Choose one option based on your setup:

### Option A — Kokoro (FREE, no GPU needed) ✅ Recommended

```bash
pip install kokoro soundfile
python tools/tts/kokoro_voiceover.py --phase 1 --voice af_heart
```

Voices available: `af_heart`, `af_bella`, `am_adam`, `bf_emma`, `bm_george`

### Option B — ElevenLabs (PAID, best quality)

1. Sign up at https://elevenlabs.io (free tier: 10,000 chars/month)
2. Get your API key from the dashboard
3. Add to `.env`: `ELEVENLABS_API_KEY=your-key-here`
4. Run:

```bash
pip install elevenlabs
python tools/tts/elevenlabs_voiceover.py --phase 1 --voice_id 21m00Tcm4TlvDq8ikWAM
```

### Option C — Chatterbox (FREE, needs GPU 8GB+)

```bash
pip install chatterbox-tts torch torchaudio
python tools/tts/chatterbox_voiceover.py --phase 1
```

**Output:** `youtube_scripts/setup/projects/chain_clarity/phase_1/voiceover/phase_01.wav`

---

## STEP 12 — Build Infographic Cards

The cards are already viewable as HTML in the browser. To render them as proper MP4/PNG files:

### Option A — Remotion (animated, highest quality)

```bash
cd remotion
node scripts/render_all_cards.js --phase 1
cd ..
```

**Output:** `_output/phase_01/instagram/card_01.mp4`, `card_01.png`, etc.

### Option B — Screenshot from browser (quick)

1. Open `http://localhost:8080/phase/chain_clarity/1`
2. Click **🃏 Infographics** tab
3. Click **Open →** on each card — it opens at full 1080×1080
4. Press `F12` → Device toolbar → set 1080×1080 → screenshot

---

## STEP 13 — Auto-Transcribe (Improve Subtitles)

The generated `subtitles.srt` is timed by word count. For accurate timing after voiceover:

```bash
python tools/transcribe.py --phase 1 --engine faster-whisper
```

**Output:** `phase_1/subtitles_auto.srt` — word-accurate captions with real timestamps.

---

## STEP 14 — Run Compliance Check

```bash
python tools/compliance_checker.py --project chain_clarity --phase 1
```

This checks 17 brand rules:
- Tone of voice ✅
- Color codes in cards ✅
- Typography ✅
- Subtitle length (≤7 words/line) ✅
- Forbidden words not used ✅
- Brand hashtags included ✅
- etc.

View the report at:
```
http://localhost:8080/phase/chain_clarity/1
```
Click **✅ Compliance** tab.

---

## STEP 15 — Generate Platform Clips

Requires FFmpeg (installed in Step 1) and a rendered video file.

```bash
python tools/platform_cutter.py \
  --project chain_clarity \
  --phase 1 \
  --video path/to/your/final_video.mp4
```

**Output:**
```
youtube_scripts/setup/projects/chain_clarity/_output/phase_01/
├── youtube/    final_1080p.mp4 · description.txt · subtitles.srt
├── tiktok/     clip_01_hook.mp4 (:15) · clip_02_main.mp4 (:60)
├── instagram/  reel_60s.mp4 · carousel_1.png · carousel_2.png · carousel_3.png
├── twitter/    card_clip.mp4 (:30) · thread.txt
├── linkedin/   clip.mp4 (:45) · article.md
├── blog/       post.md
└── github/     README.md
```

---

## STEP 16 — Generate Text Content

```bash
python tools/text_content_generator.py --project chain_clarity --phase 1
```

Requires `ANTHROPIC_API_KEY` in `.env`. Generates:

| File | Platform | What's inside |
|------|----------|--------------|
| `youtube/description.txt` | YouTube | SEO description, timestamps, tags |
| `twitter/thread.txt` | Twitter/X | 7-tweet thread with hook, data points, CTA |
| `linkedin/article.md` | LinkedIn | 800-word professional article |
| `blog/post.md` | Blog | 1,500-word SEO post with YouTube embed |
| `instagram/caption_reel.txt` | Instagram | Caption + 15 hashtags |
| `github/README.md` | GitHub | Project README with code samples |

---

## STEP 17 — Review Everything & Publish

1. Check the pipeline summary:

```bash
cat youtube_scripts/setup/projects/chain_clarity/_output/phase_01/PIPELINE_SUMMARY.md
```

2. Or view in browser:

```
http://localhost:8080/phase/chain_clarity/1
```

The pipeline steps table shows exactly what is ✅ Done and ⬜ Pending.

3. Upload to each platform manually using the files in `_output/phase_01/`.

---

## Daily Workflow (After First Setup)

Once everything is installed, your daily workflow is:

```bash
# 1. Start the server
python server.py

# 2. Open browser
# http://localhost:8080

# 3. Create new phase content
python pipeline.py --project chain_clarity --phase 2 --topic "Your Topic" --outline "point 1, point 2, point 3"

# 4. Generate voiceover
python tools/tts/kokoro_voiceover.py --phase 2 --voice af_heart

# 5. Check compliance
python tools/compliance_checker.py --project chain_clarity --phase 2

# 6. Generate text content
python tools/text_content_generator.py --project chain_clarity --phase 2
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install anthropic
```

### "ffmpeg: command not found"
```bash
# Windows
winget install --id Gyan.FFmpeg -e
# Then restart your terminal
```

### "Server offline" shown in dashboard
The server is not running. Open a new terminal and run:
```bash
python server.py
```

### Pipeline fails with "ANTHROPIC_API_KEY not set"
Open `.env` and make sure your key is on the first line with no spaces:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Infographic cards show blank iframes
The cards use local HTML — open them directly:
```
http://localhost:8080/media/chain_clarity/1/infographic_assets/card_01.html
```

### Compliance check shows all FAIL
This is normal on first run — it means the compliance checker found items to improve. Read `compliance_report_auto.md` to see which checks need attention. Most are WARN not FAIL.

---

## Minimum Cost to Run

| Stage | Free Option | Paid Option |
|-------|------------|-------------|
| Script generation | Claude free tier ($5 credit on signup) | Claude API ~$0.05/script |
| Voiceover | Kokoro-TTS (free, CPU) | ElevenLabs $5/mo |
| Transcription | faster-whisper (free, local) | AssemblyAI $0.03/video |
| Images/Cards | HTML cards (free, built-in) | FLUX.1 API $0.055/image |
| Video rendering | FFmpeg + MoviePy (free) | Creatomate $0.38/min |
| B-roll | None (script only) | Kling AI $7.99/mo |

**Minimum to start: $0** — Claude free credits + Kokoro-TTS + faster-whisper + HTML cards + FFmpeg covers the entire pipeline.

---

## Quick Reference

```bash
# Start server
python server.py

# Generate new phase (full pipeline)
python pipeline.py --project BRAND --phase N --topic "Title" --outline "points"

# Re-run existing phase (skip script generation)
python pipeline.py --project BRAND --phase N --skip-generate

# Voiceover only
python tools/tts/kokoro_voiceover.py --phase N --voice af_heart

# Compliance check only
python tools/compliance_checker.py --project BRAND --phase N

# Platform cuts only (needs video file)
python tools/platform_cutter.py --project BRAND --phase N --video path/to/video.mp4

# Text content only
python tools/text_content_generator.py --project BRAND --phase N
```

---

## Browser Pages

| URL | What it does |
|-----|-------------|
| `http://localhost:8080` | Main dashboard — pipeline control |
| `http://localhost:8080/brand` | Create / edit your brand |
| `http://localhost:8080/projects` | Browse all projects, mark favourites |
| `http://localhost:8080/phase/chain_clarity/1` | Phase 1 dashboard — view all files |
| `http://localhost:8080/phase/chain_clarity/2` | Phase 2 dashboard |
