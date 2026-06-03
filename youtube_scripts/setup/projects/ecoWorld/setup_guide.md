# Eco World — Setup & Next Steps

Your brand **Eco World** (`ecoWorld`) has been created. Follow these steps to produce your first video.

---

## ✅ What Was Created

```
youtube_scripts/setup/projects/ecoWorld/
├── brand_profile.json          ← Your brand identity (edit to customise)
├── brand_guidelines.md         ← Human-readable rules for your team
├── roadmap.json                ← 5-phase content plan
├── tags_and_metadata.json      ← SEO tags and hashtags
├── setup_guide.md              ← This file
├── phase_1/README.md           ← Phase 1 production checklist
├── phase_2/README.md
├── phase_3/README.md
├── phase_4/README.md
└── phase_5/README.md
```

---

## 🚀 Step 1 — Set Your API Key

Make sure your `.env` file has your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## 🚀 Step 2 — Customise Your Brand Profile

Open `brand_profile.json` and update:
- `tone_of_voice.forbidden_words` — add any words your brand avoids
- `content_pillars` — refine your 5 main topic areas
- `colors` — adjust to your actual brand hex codes
- `logo.svg_code` — add your SVG logo markup

---

## 🚀 Step 3 — Run Your First Pipeline

```bash
python pipeline.py \
  --project ecoWorld \
  --phase 1 \
  --topic "Your first video topic" \
  --outline "Point 1, Point 2, Point 3" \
  --duration 12 \
  --tags "tag1,tag2,tag3"
```

Or use the web dashboard:
```bash
python server.py
# Open http://localhost:8080
```

---

## 🚀 Step 4 — Check Compliance

```bash
python tools/compliance_checker.py --project ecoWorld --phase 1
```

Open `phase_1/compliance_report_auto.md` and resolve any FAIL items.

---

## 🚀 Step 5 — Generate Voiceover

```bash
# Kokoro (free, CPU):
python tools/tts/kokoro_voiceover.py --phase 1 --project ecoWorld

# ElevenLabs (paid, best quality) — needs ELEVENLABS_API_KEY in .env:
python tools/tts/elevenlabs_voiceover.py --phase 1 --project ecoWorld
```

---

## 🚀 Step 6 — Export Platform Clips

After assembling your video:
```bash
python tools/platform_cutter.py \
  --project ecoWorld \
  --phase 1 \
  --video path/to/your/final.mp4
```

---

## 🚀 Step 7 — Generate Text Content

```bash
python tools/text_content_generator.py --project ecoWorld --phase 1
```

This creates YouTube description, Twitter thread, LinkedIn article, blog post, and GitHub README.

---

## 📋 Phase Checklists

Each `phase_N/README.md` has a detailed checklist. Work through it top to bottom before publishing.

---

## 📊 Dashboard

Track everything at `http://localhost:8080` after running `python server.py`.

---

*Created: 2026-06-03 10:57*
