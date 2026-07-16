#!/usr/bin/env python3
"""
tools/init_brand.py — Scaffold a complete new brand project

Creates every folder, template file, and database record a new brand needs
so the pipeline runs without any manual setup.

Usage (interactive):
    python tools/init_brand.py

Usage (from JSON):
    python tools/init_brand.py --from-json path/to/brand_profile.json

Usage (CLI flags):
    python tools/init_brand.py \\
        --slug myBrand \\
        --name "My Brand" \\
        --tagline "Learn something new." \\
        --niche "Technology Education" \\
        --primary-color "#00D4AA" \\
        --bg-color "#0A0E1A"

What it creates:
    youtube_scripts/setup/projects/{slug}/
        brand_profile.json          ← Full brand identity
        brand_guidelines.md         ← Human-readable brand rules
        roadmap.json                ← 5-phase content roadmap scaffold
        tags_and_metadata.json      ← SEO tags + hashtags
        setup_guide.md              ← Step-by-step what to do next
        phase_1/ ... phase_5/
            README.md               ← Phase production checklist
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent
PROJECT_ROOT = BASE_DIR / "youtube_scripts" / "setup" / "projects"
sys.path.insert(0, str(BASE_DIR))

# Load .env
_env = BASE_DIR / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ── DB (optional) ─────────────────────────────────────────────────────────────
try:
    from db.db import upsert_brand, upsert_phase, is_available as db_available
    _DB = True
except ImportError:
    _DB = False
    def db_available(): return False
    def upsert_brand(_): return False
    def upsert_phase(*_): return False


# =============================================================================
# Template generators
# =============================================================================

def _brand_profile(slug: str, name: str, tagline: str, niche: str,
                   primary_color: str, bg_color: str,
                   secondary_color: str, highlight_color: str) -> dict:
    return {
        "brand_slug":      slug,
        "brand_name":      name,
        "tagline":         tagline,
        "niche":           niche,
        "target_audience": f"Curious learners who want to understand {niche} in plain language",
        "platforms":       ["YouTube", "TikTok", "Instagram"],
        "tone_of_voice": {
            "primary":       f"Clear, friendly expert — explains {niche} simply without dumbing it down",
            "forbidden_words": ["simply", "just", "obviously", "easy", "basic", "guaranteed"],
            "sentence_style":  "Short declarative sentences. Max 15 words per sentence. Active voice.",
            "analogy_style":   "Everyday objects and situations. Never explain complex ideas with equally complex analogies."
        },
        "colors": {
            "primary":    {"name": "Primary",    "hex": primary_color,   "usage": "headers, CTAs, key stats"},
            "secondary":  {"name": "Secondary",  "hex": secondary_color, "usage": "accents, icons, stat callouts"},
            "neutral":    {"name": "Neutral",    "hex": "#8B9BB4",       "usage": "body text, secondary labels"},
            "background": {"name": "Background", "hex": bg_color,        "usage": "card and screen backgrounds"},
            "highlight":  {"name": "Highlight",  "hex": highlight_color, "usage": "emphasis, pull quotes, chapter markers"}
        },
        "typography": {
            "heading_font":     "Space Grotesk",
            "body_font":        "Inter",
            "code_font":        "JetBrains Mono",
            "min_body_size_px":   48,
            "min_header_size_px": 72,
            "max_words_per_line": 7
        },
        "logo": {
            "concept": f"A clean, modern mark representing {name}.",
            "symbol":  "To be designed",
            "svg_code": ""
        },
        "sound_identity": {
            "intro_music_style":        "Warm, focused background — forward momentum without distraction",
            "bpm_range":                "90–115",
            "mood_keywords":            ["curious", "optimistic", "intelligent", "accessible"],
            "forbidden_genres":         ["aggressive EDM", "hype music", "countdown builds"],
            "royalty_free_search_terms": [
                "light acoustic background",
                "calm upbeat corporate",
                "minimal positive background"
            ]
        },
        "content_pillars": [
            f"{niche} Fundamentals",
            f"Advanced {niche} Concepts",
            "Real-World Applications",
            "Industry News & Analysis",
            "Beginner Explainers"
        ],
        "card_dimensions": {
            "instagram_post":    "1080x1080px",
            "stories_reels":     "1080x1920px",
            "youtube_thumbnail": "1280x720px",
            "youtube_endscreen": "1920x1080px"
        },
        "animation_style": {
            "default_transition": "slide-up",
            "duration_ms":        400,
            "text_animation":     "typewriter",
            "easing":             "ease-out"
        }
    }


def _brand_guidelines(profile: dict) -> str:
    slug  = profile.get("brand_slug", "")
    name  = profile.get("brand_name", slug)
    tag   = profile.get("tagline", "")
    niche = profile.get("niche", "")
    tone  = profile.get("tone_of_voice", {})
    colors = profile.get("colors", {})
    typo   = profile.get("typography", {})
    pillars = profile.get("content_pillars", [])
    forbidden = ", ".join(tone.get("forbidden_words", []))

    return f"""# {name} — Brand Guidelines

> **{tag}**

---

## 1. Brand Identity

| Field | Value |
|-------|-------|
| Brand Slug | `{slug}` |
| Niche | {niche} |
| Platforms | {", ".join(profile.get("platforms", []))} |

**Target Audience:**
{profile.get("target_audience", "")}

---

## 2. Tone of Voice

**Voice:** {tone.get("primary", "")}

**Sentence Style:** {tone.get("sentence_style", "")}

**Analogy Style:** {tone.get("analogy_style", "")}

**Forbidden Words (never use):**
{", ".join([f"`{w}`" for w in tone.get("forbidden_words", [])])}

---

## 3. Color Palette

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Primary | {colors.get("primary",{}).get("name","")} | `{colors.get("primary",{}).get("hex","")}` | {colors.get("primary",{}).get("usage","")} |
| Secondary | {colors.get("secondary",{}).get("name","")} | `{colors.get("secondary",{}).get("hex","")}` | {colors.get("secondary",{}).get("usage","")} |
| Neutral | {colors.get("neutral",{}).get("name","")} | `{colors.get("neutral",{}).get("hex","")}` | {colors.get("neutral",{}).get("usage","")} |
| Background | {colors.get("background",{}).get("name","")} | `{colors.get("background",{}).get("hex","")}` | {colors.get("background",{}).get("usage","")} |
| Highlight | {colors.get("highlight",{}).get("name","")} | `{colors.get("highlight",{}).get("hex","")}` | {colors.get("highlight",{}).get("usage","")} |

**Rule:** Use hex values only. Never use CSS color names (`red`, `blue`, etc.).

---

## 4. Typography

| Role | Font | Min Size |
|------|------|----------|
| Headings | {typo.get("heading_font","Space Grotesk")} | {typo.get("min_header_size_px",72)}px |
| Body | {typo.get("body_font","Inter")} | {typo.get("min_body_size_px",48)}px |
| Code | {typo.get("code_font","JetBrains Mono")} | - |

**Rule:** Always load fonts from Google Fonts CDN. Max {typo.get("max_words_per_line",7)} words per line.

---

## 5. Content Pillars

{"".join([f"{i+1}. {p}{chr(10)}" for i, p in enumerate(pillars)])}

---

## 6. Animation Sequence (6 steps — always in this order)

1. `fadeIn` — element fades into view
2. `slideDown` — header slides down from top
3. `wordIn` — key terms appear word by word
4. `slideUp` — supporting text slides up
5. `countUp` — stats animate from 0 to value
6. `bounce` — CTA or key icon bounces once

**Transition:** {profile.get("animation_style", {}).get("default_transition", "slide-up")}
**Duration:** {profile.get("animation_style", {}).get("duration_ms", 400)}ms
**Easing:** {profile.get("animation_style", {}).get("easing", "ease-out")}

---

## 7. Infographic Cards

- **Instagram Post / YouTube Thumbnail card:** 1080×1080px
- **Reels / Stories:** 1080×1920px
- Background always: `{colors.get("background",{}).get("hex","")}`
- All 5 brand colors must appear somewhere on each card
- Text must pass WCAG AA contrast against background

---

## 8. Sound Identity

| Field | Value |
|-------|-------|
| Style | {profile.get("sound_identity", {}).get("intro_music_style", "")} |
| BPM Range | {profile.get("sound_identity", {}).get("bpm_range", "")} |
| Mood | {", ".join(profile.get("sound_identity", {}).get("mood_keywords", []))} |

**Forbidden Genres:** {", ".join(profile.get("sound_identity", {}).get("forbidden_genres", []))}

---

*Generated by Bhrikuty Film Director — {datetime.now().strftime("%Y-%m-%d")}*
"""


def _roadmap(slug: str, name: str, pillars: list) -> dict:
    phases = []
    for i, pillar in enumerate(pillars[:5], 1):
        phases.append({
            "phase":          i,
            "title":          pillar,
            "status":         "pending",
            "learning_goals": [
                f"Understand the core concepts of {pillar}",
                f"Explain {pillar} to a complete beginner",
                f"Apply {pillar} knowledge in real-world scenarios"
            ],
            "content_breakdown": [
                {"type": "long-form",   "duration_min": 12, "platform": "YouTube"},
                {"type": "short-form",  "duration_min": 1,  "platform": "TikTok / Instagram Reels"},
                {"type": "infographic", "card_count":    4,  "platform": "Instagram / Twitter"},
                {"type": "article",     "words":       1500,  "platform": "Blog / LinkedIn"},
                {"type": "thread",      "tweets":         7,  "platform": "Twitter / X"}
            ],
            "topics": []
        })
    return {
        "brand_slug":   slug,
        "brand_name":   name,
        "total_phases": 5,
        "phases":       phases,
        "created_at":   datetime.now().isoformat()
    }


def _tags_and_metadata(name: str, niche: str, pillars: list) -> dict:
    slug_niche = niche.lower().replace(" ", "")
    return {
        "brand_name": name,
        "niche":      niche,
        "youtube": {
            "channel_keywords": pillars[:5],
            "default_tags":     [niche.lower(), "education", "explainer", "learn"]
        },
        "tiktok": {
            "hashtags": [f"#{p.replace(' ', '').lower()}" for p in pillars[:3]]
                        + ["#learnontiktok", "#education", f"#{slug_niche}"]
        },
        "instagram": {
            "hashtags": [f"#{p.replace(' ', '').lower()}" for p in pillars[:5]]
                        + ["#education", "#learning", "#explainer", f"#{slug_niche}"]
        },
        "seo_keywords": pillars + [niche, f"{niche} explained", f"learn {niche}"],
        "updated_at": datetime.now().isoformat()
    }


def _phase_readme(phase_num: int, brand_name: str) -> str:
    return f"""# {brand_name} — Phase {phase_num} Production Checklist

> Complete each step in order. Do not skip steps.

## Pre-Production
- [ ] Topic confirmed and approved
- [ ] Outline written (3–5 key points)
- [ ] Duration decided (default: 12 min)
- [ ] Tags and keywords prepared

## Step 1 — Script Generation
```
python pipeline.py --project {"{brand_slug}"} --phase {phase_num} --topic "Your Topic" --outline "Your outline" --duration 12
```
- [ ] `script.md` generated (> 1,000 words)
- [ ] `script_short.md` generated (60-second cut)
- [ ] `voiceover_brief.md` generated
- [ ] `clip_brief.md` generated
- [ ] `subtitles.srt` generated

## Step 2 — Compliance Check
```
python tools/compliance_checker.py --project {"{brand_slug}"} --phase {phase_num}
```
- [ ] `compliance_report_auto.md` status is PASS or PASS_WITH_WARNINGS
- [ ] No FAIL items in the report
- [ ] Forbidden words not present

## Step 3 — Infographic Cards
```
# (auto-generated in Step 1 — check infographic_assets/)
```
- [ ] `infographic_assets/card_01.html` exists
- [ ] `infographic_assets/card_02.html` exists
- [ ] All cards use brand colors only
- [ ] Cards pass visual review

## Step 4 — Voiceover
```
python tools/tts/kokoro_voiceover.py --phase {phase_num} --project {"{brand_slug}"}
```
- [ ] `voiceover/phase_{phase_num}.wav` exists
- [ ] Audio is clean — no clipping, noise
- [ ] Pacing matches voiceover_brief.md
- [ ] Duration matches target

## Step 5 — Video Assembly
- [ ] Raw footage captured / sourced
- [ ] Video assembled with voiceover
- [ ] Subtitles burned (if required)
- [ ] Final video exported as 1920×1080 MP4

## Step 6 — Platform Cuts
```
python tools/platform_cutter.py --project {"{brand_slug}"} --phase {phase_num} --video _output/phase_{phase_num:02d}/final.mp4
```
- [ ] `_output/phase_{phase_num:02d}/youtube/final_1080p.mp4`
- [ ] `_output/phase_{phase_num:02d}/tiktok/clip_01_hook.mp4`
- [ ] `_output/phase_{phase_num:02d}/instagram/reel_60s.mp4`
- [ ] `_output/phase_{phase_num:02d}/twitter/card_clip.mp4`

## Step 7 — Text Content
```
python tools/text_content_generator.py --project {"{brand_slug}"} --phase {phase_num}
```
- [ ] `_output/phase_{phase_num:02d}/youtube/description.txt`
- [ ] `_output/phase_{phase_num:02d}/twitter/thread.txt`
- [ ] `_output/phase_{phase_num:02d}/linkedin/article.md`
- [ ] `_output/phase_{phase_num:02d}/blog/post.md`

## Step 8 — Review & Publish
- [ ] All files reviewed by a human
- [ ] YouTube video uploaded + description added
- [ ] TikTok clips uploaded
- [ ] Instagram reel + carousel posted
- [ ] Twitter thread posted
- [ ] LinkedIn article published
- [ ] Blog post published

---
*Bhrikuty Film Director — Phase {phase_num} of 5*
"""


def _setup_guide(profile: dict) -> str:
    slug = profile.get("brand_slug", "")
    name = profile.get("brand_name", slug)
    return f"""# {name} — Setup & Next Steps

Your brand **{name}** (`{slug}`) has been created. Follow these steps to produce your first video.

---

## ✅ What Was Created

```
youtube_scripts/setup/projects/{slug}/
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
python pipeline.py \\
  --project {slug} \\
  --phase 1 \\
  --topic "Your first video topic" \\
  --outline "Point 1, Point 2, Point 3" \\
  --duration 12 \\
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
python tools/compliance_checker.py --project {slug} --phase 1
```

Open `phase_1/compliance_report_auto.md` and resolve any FAIL items.

---

## 🚀 Step 5 — Generate Voiceover

```bash
# Kokoro (free, CPU):
python tools/tts/kokoro_voiceover.py --phase 1 --project {slug}

# ElevenLabs (paid, best quality) — needs ELEVENLABS_API_KEY in .env:
python tools/tts/elevenlabs_voiceover.py --phase 1 --project {slug}
```

---

## 🚀 Step 6 — Export Platform Clips

After assembling your video:
```bash
python tools/platform_cutter.py \\
  --project {slug} \\
  --phase 1 \\
  --video path/to/your/final.mp4
```

---

## 🚀 Step 7 — Generate Text Content

```bash
python tools/text_content_generator.py --project {slug} --phase 1
```

This creates YouTube description, Twitter thread, LinkedIn article, blog post, and GitHub README.

---

## 📋 Phase Checklists

Each `phase_N/README.md` has a detailed checklist. Work through it top to bottom before publishing.

---

## 📊 Dashboard

Track everything at `http://localhost:8080` after running `python server.py`.

---

*Created: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""


# =============================================================================
# Main scaffold function
# =============================================================================

def scaffold_brand(profile: dict, num_phases: int = 5, quiet: bool = False) -> Path:
    """
    Given a brand_profile dict, create all project files + DB records.
    Returns the project directory Path.
    """
    slug = profile.get("brand_slug", "").strip()
    name = profile.get("brand_name", slug)
    if not slug:
        raise ValueError("brand_slug is required")

    proj_dir = PROJECT_ROOT / slug
    proj_dir.mkdir(parents=True, exist_ok=True)

    def log(msg):
        if not quiet:
            print(msg)

    log(f"\n{'='*60}")
    log(f"  Scaffolding brand: {name} ({slug})")
    log(f"{'='*60}")

    # ── 1. brand_profile.json ─────────────────────────────────────────────────
    bp_path = proj_dir / "brand_profile.json"
    bp_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  [ok] brand_profile.json")

    # ── 2. brand_guidelines.md ────────────────────────────────────────────────
    (proj_dir / "brand_guidelines.md").write_text(
        _brand_guidelines(profile), encoding="utf-8"
    )
    log(f"  [ok] brand_guidelines.md")

    # ── 3. roadmap.json ───────────────────────────────────────────────────────
    pillars = profile.get("content_pillars", [])
    (proj_dir / "roadmap.json").write_text(
        json.dumps(_roadmap(slug, name, pillars), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    log(f"  [ok] roadmap.json")

    # ── 4. tags_and_metadata.json ─────────────────────────────────────────────
    niche = profile.get("niche", "")
    (proj_dir / "tags_and_metadata.json").write_text(
        json.dumps(_tags_and_metadata(name, niche, pillars), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    log(f"  [ok] tags_and_metadata.json")

    # ── 5. Phase directories ──────────────────────────────────────────────────
    for i in range(1, num_phases + 1):
        phase_dir = proj_dir / f"phase_{i}"
        phase_dir.mkdir(exist_ok=True)
        readme = _phase_readme(i, name).replace("{brand_slug}", slug)
        (phase_dir / "README.md").write_text(readme, encoding="utf-8")
        (proj_dir / "_output" / f"phase_{i:02d}").mkdir(parents=True, exist_ok=True)
        log(f"  [ok] phase_{i}/ + _output/phase_{i:02d}/")

    # ── 6. setup_guide.md ─────────────────────────────────────────────────────
    (proj_dir / "setup_guide.md").write_text(_setup_guide(profile), encoding="utf-8")
    log(f"  [ok] setup_guide.md")

    # ── 7. DB records ─────────────────────────────────────────────────────────
    if db_available():
        ok = upsert_brand(profile)
        if ok:
            log(f"  [DB] brand record saved")
            for i in range(1, num_phases + 1):
                upsert_phase(slug, i)
            log(f"  [DB] {num_phases} phase records saved")
        else:
            log(f"  [WARN] DB: brand upsert failed (file scaffold complete)")
    else:
        log(f"  [INFO] DB not available - file scaffold only")

    log(f"\n  Brand ready: {proj_dir}")
    log(f"  Next: python pipeline.py --project {slug} --phase 1 --topic \"...\" --outline \"...\"")
    log(f"{'='*60}\n")

    return proj_dir


# =============================================================================
# Interactive prompts
# =============================================================================

def _prompt(label: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    val = input(f"  {label}{hint}: ").strip()
    return val or default


def interactive_wizard() -> dict:
    print("\n" + "="*60)
    print("  BHRIKUTY — New Brand Setup Wizard")
    print("="*60)
    print("  Press Enter to accept defaults.\n")

    slug  = _prompt("Brand slug (no spaces, e.g. ecoWorld)")
    name  = _prompt("Brand name",          f"{slug} Channel")
    tag   = _prompt("Tagline",             "Learn something new.")
    niche = _prompt("Niche / topic area",  "Education")
    pc    = _prompt("Primary color hex",   "#00D4AA")
    sc    = _prompt("Secondary color hex", "#F5A623")
    bg    = _prompt("Background color hex","#0A0E1A")
    hi    = _prompt("Highlight color hex", "#7B5CF0")

    print("\n  Content pillars (5 main topic areas).")
    pillars = []
    for i in range(1, 6):
        p = _prompt(f"  Pillar {i}", f"{niche} Topic {i}")
        pillars.append(p)

    return _brand_profile(slug, name, tag, niche, pc, bg, sc, hi) | {"content_pillars": pillars}


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Scaffold a new brand project")
    parser.add_argument("--slug",            help="Brand slug (folder name)")
    parser.add_argument("--name",            help="Brand display name")
    parser.add_argument("--tagline",         default="Learn something new.")
    parser.add_argument("--niche",           default="Education")
    parser.add_argument("--primary-color",   default="#00D4AA")
    parser.add_argument("--secondary-color", default="#F5A623")
    parser.add_argument("--bg-color",        default="#0A0E1A")
    parser.add_argument("--highlight-color", default="#7B5CF0")
    parser.add_argument("--phases",          type=int, default=5)
    parser.add_argument("--from-json",       help="Path to an existing brand_profile.json")
    args = parser.parse_args()

    if args.from_json:
        profile = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    elif args.slug:
        profile = _brand_profile(
            args.slug,
            args.name or args.slug,
            args.tagline,
            args.niche,
            args.primary_color,
            args.bg_color,
            args.secondary_color,
            args.highlight_color,
        )
    else:
        profile = interactive_wizard()

    scaffold_brand(profile, num_phases=args.phases)


if __name__ == "__main__":
    main()
