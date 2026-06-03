"""
generate_phase.py — Generate all phase production files via Claude (primary) or Gemini (fallback)

Usage:
  python tools/generate_phase.py \\
    --project ecoWorld \\
    --phase 6 \\
    --topic "Economics of the World" \\
    --outline "GDP, trade, inflation, Asia, China, India"

Requires (at least one):
  ANTHROPIC_API_KEY — Claude Sonnet (primary)
  GEMINI_API_KEY    — Gemini Flash (fallback when Anthropic fails or has no credits)

  pip install anthropic google-generativeai
"""

import json
import os
import re
import argparse
import sys
from pathlib import Path

# Load .env
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Anthropic ─────────────────────────────────────────────────────────────────
try:
    import anthropic as _anthropic_lib
    _ANTHROPIC_OK = bool(os.environ.get("ANTHROPIC_API_KEY"))
except ImportError:
    _anthropic_lib = None
    _ANTHROPIC_OK = False

# ── Gemini ────────────────────────────────────────────────────────────────────
try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
    _GEMINI_CLIENT = _genai.Client(api_key=_GEMINI_KEY) if _GEMINI_KEY else None
    _GEMINI_OK = bool(_GEMINI_KEY)
except ImportError:
    _genai = None
    _genai_types = None
    _GEMINI_CLIENT = None
    _GEMINI_OK = False

if not _ANTHROPIC_OK and not _GEMINI_OK:
    print("[ERROR] No AI API key configured.")
    print("  Set ANTHROPIC_API_KEY (pip install anthropic)  — primary")
    print("  Set GEMINI_API_KEY    (pip install google-generativeai) — fallback")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"
TOOLS_DIR    = Path(__file__).parent

CLAUDE_MODEL  = "claude-sonnet-4-6"
GEMINI_MODEL  = "gemini-2.5-flash"

_BILLING_ERRORS = ("credit balance", "quota", "billing", "rate limit", "overloaded")


def load_brand(project: str) -> dict:
    with open(PROJECT_ROOT / project / "brand_profile.json", encoding="utf-8") as f:
        return json.load(f)


def load_brand_guidelines(project: str) -> str:
    path = PROJECT_ROOT / project / "brand_guidelines.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_roadmap(project: str) -> dict:
    with open(PROJECT_ROOT / project / "roadmap.json", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt(brand: dict, guidelines: str) -> str:
    forbidden = ", ".join(brand["tone_of_voice"]["forbidden_words"])
    colors = {k: v["hex"] for k, v in brand["colors"].items()}
    return f"""You are the content director for '{brand["brand_name"]}' — {brand["tagline"]}

BRAND RULES (non-negotiable):
- Voice: {brand["tone_of_voice"]["primary"]}
- Forbidden words (NEVER use): {forbidden}
- Sentence style: {brand["tone_of_voice"]["sentence_style"]}
- Analogy style: {brand["tone_of_voice"]["analogy_style"]}
- Target audience: {brand["target_audience"]}
- Brand colors (hex only, no CSS names): {json.dumps(colors)}
- Typography: {brand["typography"]["heading_font"]} (headers), {brand["typography"]["body_font"]} (body)
- Animation: always include brand 6-step sequence (fadeIn bg, slideDown logo, wordIn headline, slideUp content, stat countUp, bounce CTA)

CONTENT STANDARDS:
- Scripts: max 15 words per sentence, active voice, analogy-first
- Subtitles: max 7 words per cue line, max 2 lines, 1.5s-6s duration
- HTML cards: 1080x1080px, Navy background, all 5 brand colors, Google Fonts CDN
- Sound: 88-112 BPM, no forbidden genres (trap, hype EDM, dubstep)
- No investment advice, no price speculation, no trading framing

{guidelines[:2000] if guidelines else ""}"""


def _call_anthropic(client, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return msg.content[0].text


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    import time
    last_err = None
    for attempt in range(4):
        if attempt > 0:
            wait = 2 ** attempt
            print(f"  [GEMINI] Retry {attempt}/3 in {wait}s (503 overload)...")
            time.sleep(wait)
        try:
            response = _GEMINI_CLIENT.models.generate_content(
                model=GEMINI_MODEL,
                config=_genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
                contents=user_prompt,
            )
            return response.text
        except Exception as e:
            last_err = e
            if "503" not in str(e) and "UNAVAILABLE" not in str(e):
                raise
    raise last_err


def call_ai(client, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
    """Call Claude first; fall back to Gemini if Anthropic fails (billing/quota/auth)."""
    if client is not None:
        try:
            return _call_anthropic(client, system_prompt, user_prompt, max_tokens)
        except Exception as e:
            err = str(e).lower()
            is_recoverable = any(k in err for k in _BILLING_ERRORS)
            if is_recoverable and _GEMINI_OK:
                print(f"  [WARN] Anthropic failed ({str(e)[:80]}). Switching to Gemini...")
            elif not _GEMINI_OK:
                raise
            else:
                raise
    # Gemini path
    if not _GEMINI_OK:
        raise RuntimeError("No AI provider available. Set ANTHROPIC_API_KEY or GEMINI_API_KEY.")
    return _call_gemini(system_prompt, user_prompt)


# Keep old name as alias so nothing else breaks
def call_claude(client, system_prompt, user_prompt, max_tokens=4000):
    return call_ai(client, system_prompt, user_prompt, max_tokens)


def generate_script(client, system_prompt: str, phase: int, topic: str, outline: str, duration_min: int) -> str:
    return call_claude(client, system_prompt, f"""Write a complete YouTube video script for Phase {phase}:

TITLE: {topic}
OUTLINE: {outline}
TARGET DURATION: {duration_min} minutes (approximately {duration_min * 150} words spoken)

Structure:
- HOOK (0:00-0:12): dramatic real-world stat or event, introduce the question
- SECTION 1-5: each with [TITLE CARD], [B-ROLL], SPOKEN narration, ON-SCREEN TEXT
- CLOSE: summary + subscribe CTA with Phase {phase} of 5 reference

Requirements:
- Max 15 words per sentence
- Each ON-SCREEN TEXT line: hex color and style
- Analogy-driven explanations throughout
- No forbidden words
- No investment advice""", max_tokens=4000)


def generate_script_short(client, system_prompt: str, phase: int, topic: str, script: str) -> str:
    return call_claude(client, system_prompt, f"""Based on this full script for Phase {phase}: {topic}

Write a 60-second short-form script (YouTube Shorts / TikTok / Instagram Reel).

Structure:
- [TITLE CARD]: punchy hook
- SPOKEN: 3 key takeaways from the full video, each 1-2 sentences max
- ON-SCREEN TEXT: brand hex colors for each key point
- End with: "Full breakdown — link in bio. Chain Clarity."

First 100 words of full script for reference:
{script[:500]}""", max_tokens=600)


def generate_srt(client, system_prompt: str, script: str) -> str:
    return call_claude(client, system_prompt, f"""Convert the SPOKEN sections of this script into SRT subtitle format.

Rules:
- Max 7 words per cue line
- Max 2 lines per cue
- Duration 1.5s-4.5s per cue
- Speaking pace: approximately 150 words per minute
- Number cues starting from 1
- Format: number, timecode (HH:MM:SS,mmm --> HH:MM:SS,mmm), text

Script (SPOKEN sections only):
{script}

Return ONLY the SRT content, no explanation.""", max_tokens=3000)


def generate_voiceover_brief(client, system_prompt: str, topic: str, script: str) -> str:
    return call_claude(client, system_prompt, f"""Write a voiceover brief for: {topic}

Based on this script excerpt:
{script[:1500]}

Include:
- Overall delivery style (2-3 sentences)
- Section-by-section pacing guide with emphasis notes
- Technical specs (sample rate, format, target LUFS)
- Pronunciation notes for any technical terms

Format as Markdown.""", max_tokens=1500)


def generate_music_brief(client, system_prompt: str, topic: str) -> str:
    return call_claude(client, system_prompt, f"""Write a music brief for a Chain Clarity video about: {topic}

Include:
- Overall mood (3-4 sentences)
- Section-by-section breakdown with BPM (always 88-112), mood, instrumentation
- Technical requirements table (duration, format, LUFS, fade)
- Royalty-free search terms (use brand_profile.json standard terms + topic-specific)
- Note forbidden genres

Format as Markdown.""", max_tokens=800)


def generate_infographics_brief(client, system_prompt: str, topic: str, script: str) -> str:
    return call_claude(client, system_prompt, f"""Write an infographics brief for 3 animated cards for: {topic}

Based on this script:
{script[:2000]}

For each card:
- Title
- Concept (what it visualizes)
- Layout description
- Color rules (hex only)
- 6-step animation sequence (brand standard)
- Stat/data point
- CTA strip text

Format as Markdown. All hex colors must be from brand palette: #00D4AA #F5A623 #8B9BB4 #0A0E1A #7B5CF0""", max_tokens=2000)


def generate_clip_brief(client, system_prompt: str, topic: str, script: str) -> str:
    return call_claude(client, system_prompt, f"""Write a clip brief (shot list) for a {len(script.split()) // 150}-minute video about: {topic}

Based on this script:
{script[:2000]}

Format as a Markdown table with columns: # | Duration | Type | Description | Text Overlay
Types: TITLE CARD | B-ROLL | ANIMATION | SCREEN RECORD | TEXT CARD | TRANSITION | PRODUCT SHOT | END CARD

Include shots for: hook, each main section, close, end card.
All text overlays must use brand hex colors.""", max_tokens=2000)


def generate_html_card(client, system_prompt: str, phase: int, card_num: int, topic: str, card_brief: str) -> str:
    return call_claude(client, system_prompt, f"""Write a complete 1080x1080px animated HTML infographic card.

Phase: {phase}
Card: {card_num}
Topic: {topic}
Card brief: {card_brief}

Requirements:
- DOCTYPE html, meta viewport width=1080
- Google Fonts CDN: Space Grotesk, Inter, JetBrains Mono
- Brand hex colors: #00D4AA #F5A623 #8B9BB4 #0A0E1A #7B5CF0 (no CSS color names)
- 6-step brand animation: fadeIn bg -> slideDown logo -> wordIn headline -> slideUp content -> countUp stat -> bounce CTA
- Chain Clarity logo SVG (use exact SVG from brand_profile.json)
- Phase label in logo area
- CSS animations only (no external libraries)
- JavaScript only for counter animation if needed

Return ONLY the complete HTML file content, starting with <!-- EXPORT comment -->""", max_tokens=3000)


def generate_content_spec(phase: int, topic: str, script: str, tags: list) -> dict:
    slug = topic.lower().replace(" ", "-").replace("—", "").replace("'", "")
    slug = re.sub(r'[^a-z0-9-]', '', slug)[:60]
    return {
        "project": "chain_clarity",
        "phase": phase,
        "title": topic,
        "slug": slug,
        "duration_min": len(script.split()) // 150,
        "status": "generated",
        "tags": tags,
        "hashtags": [f"#{''.join(t.split())}" for t in tags[:8]],
        "platform_cuts": {
            "tiktok_hook":    {"start": "0:00", "end": "0:15", "aspect": "9:16"},
            "tiktok_main":    {"start": "0:00", "end": "1:00", "aspect": "9:16"},
            "instagram_reel": {"start": "0:00", "end": "1:00", "aspect": "9:16"},
            "twitter_clip":   {"start": "0:30", "end": "1:00", "aspect": "16:9"},
        },
        "text_overlays": [
            {"time": "0:00", "text": f"Chain Clarity | Phase {phase}", "position": "top-left", "color": "#8B9BB4"},
            {"time": "0:05", "text": f"#{tags[0]} #{tags[1]}" if len(tags) >= 2 else "", "position": "bottom-left", "color": "#8B9BB4"},
        ],
        "tags_file": "../../tags_and_metadata.json",
        "infographic_cards": 3,
        "compliance_status": "PENDING"
    }


def write_phase_files(phase_dir: Path, assets_dir: Path, files: dict):
    phase_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in files.items():
        if filename.startswith("card_"):
            path = assets_dir / filename
        else:
            path = phase_dir / filename

        if isinstance(content, dict):
            path.write_text(json.dumps(content, indent=2), encoding="utf-8")
        else:
            path.write_text(content, encoding="utf-8")
        print(f"  [ok] {filename}")


def run_compliance_check(project: str, phase: int):
    import subprocess
    checker = TOOLS_DIR / "compliance_checker.py"
    if checker.exists():
        result = subprocess.run(
            [sys.executable, str(checker), "--project", project, "--phase", str(phase)],
            capture_output=True, text=True
        )
        print(result.stdout[-500:] if result.stdout else "")
        if result.returncode != 0:
            print(f"  [WARN] Compliance check issues: {result.stderr[-200:]}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate all phase production files via Claude (primary) or Gemini (fallback)"
    )
    parser.add_argument("--project",  default="chain_clarity")
    parser.add_argument("--phase",    type=int, required=True)
    parser.add_argument("--topic",    required=True, help="Video title / topic")
    parser.add_argument("--outline",  default="", help="Key subtopics comma-separated")
    parser.add_argument("--duration", type=int, default=12, help="Target duration in minutes")
    parser.add_argument("--tags",     default="education,explainer", help="Comma-separated tags")
    parser.add_argument("--provider", choices=["auto", "anthropic", "gemini"], default="auto",
                        help="Force a specific AI provider (default: auto = Anthropic then Gemini)")
    args = parser.parse_args()

    # Build Anthropic client if available and not forced to Gemini
    client = None
    if _ANTHROPIC_OK and args.provider in ("auto", "anthropic"):
        client = _anthropic_lib.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        print(f"  [AI] Primary provider: Claude ({CLAUDE_MODEL})")
    elif _GEMINI_OK:
        print(f"  [AI] Provider: Gemini ({GEMINI_MODEL})")
    else:
        print("[ERROR] No AI provider available.")
        sys.exit(1)

    if args.provider == "gemini":
        client = None  # Force Gemini path
    brand = load_brand(args.project)
    guidelines = load_brand_guidelines(args.project)
    system_prompt = build_system_prompt(brand, guidelines)

    phase_dir = PROJECT_ROOT / args.project / f"phase_{args.phase}"
    assets_dir = phase_dir / "infographic_assets"
    tags = [t.strip() for t in args.tags.split(",")]

    print(f"\n{'='*60}")
    print(f"Generating Phase {args.phase}: {args.topic}")
    print(f"{'='*60}")

    files = {}

    print("\n[1/9] Generating script.md...")
    script = generate_script(client, system_prompt, args.phase, args.topic, args.outline, args.duration)
    files["script.md"] = script

    print("[2/9] Generating script_short.md...")
    files["script_short.md"] = generate_script_short(client, system_prompt, args.phase, args.topic, script)

    print("[3/9] Generating subtitles.srt...")
    files["subtitles.srt"] = generate_srt(client, system_prompt, script)

    print("[4/9] Generating voiceover_brief.md...")
    files["voiceover_brief.md"] = generate_voiceover_brief(client, system_prompt, args.topic, script)

    print("[5/9] Generating music_brief.md...")
    files["music_brief.md"] = generate_music_brief(client, system_prompt, args.topic)

    print("[6/9] Generating infographics.md...")
    infographics_brief = generate_infographics_brief(client, system_prompt, args.topic, script)
    files["infographics.md"] = infographics_brief

    print("[7/9] Generating clip_brief.md...")
    files["clip_brief.md"] = generate_clip_brief(client, system_prompt, args.topic, script)

    print("[8/9] Generating HTML infographic cards...")
    for card_num in range(1, 4):
        card_brief = f"Card {card_num} from brief:\n{infographics_brief[card_num*200:(card_num+1)*400]}"
        html = generate_html_card(client, system_prompt, args.phase, card_num, args.topic, card_brief)
        files[f"card_0{card_num}.html"] = html

    print("[9/9] Generating content_spec.json...")
    files["content_spec.json"] = generate_content_spec(args.phase, args.topic, script, tags)

    write_phase_files(phase_dir, assets_dir, files)

    print("\nRunning compliance check...")
    run_compliance_check(args.project, args.phase)

    print(f"\n[DONE] Phase {args.phase} generated successfully!")
    print(f"   -> {phase_dir}")
    print(f"\nNext: python tools/text_content_generator.py --phase {args.phase}")
    print(f"Next: python tools/platform_cutter.py --phase {args.phase} --video <path>")


if __name__ == "__main__":
    main()
