"""
text_content_generator.py — Generate all text platform content via Claude API
Usage: python tools/text_content_generator.py --project chain_clarity --phase 4
       python tools/text_content_generator.py --project chain_clarity --phase all

Requires: ANTHROPIC_API_KEY environment variable
          pip install anthropic
"""

import json
import os
import argparse
import sys
from pathlib import Path

import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load .env
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

try:
    import anthropic as _anthropic_lib
    _ANTHROPIC_OK = bool(os.environ.get("ANTHROPIC_API_KEY"))
except ImportError:
    _anthropic_lib = None
    _ANTHROPIC_OK = False

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
    _GEMINI_CLIENT = _genai.Client(api_key=_GEMINI_KEY) if _GEMINI_KEY else None
    _GEMINI_OK = bool(_GEMINI_KEY)
except ImportError:
    _genai = None
    _GEMINI_CLIENT = None
    _GEMINI_OK = False

if not _ANTHROPIC_OK and not _GEMINI_OK:
    print("[ERROR] No AI API key. Set ANTHROPIC_API_KEY or GEMINI_API_KEY in .env")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"

MODEL        = "claude-sonnet-4-6"
GEMINI_MODEL = "gemini-2.5-flash"
_BILLING_ERRORS = ("credit balance", "quota", "billing", "rate limit", "overloaded",
                   "invalid_request_error", "insufficient_quota", "payment")

# DashScope / Qwen (OpenAI-compatible endpoint) — primary + secondary
_DS_KEY      = os.environ.get("DASHSCOPE_API_KEY", "")
_DS_BASE_URL = os.environ.get("DASHSCOPE_BASE_URL",
               "https://dashscope.aliyuncs.com/compatible-mode/v1")
_DS_KEY2     = os.environ.get("DASHSCOPE_API_KEY_2", "")
_DS_BASE2    = os.environ.get("DASHSCOPE_BASE_URL_2", _DS_BASE_URL)
_DS_MODEL    = os.environ.get("DASHSCOPE_MODEL", "qwen-max")
_DS_OK       = bool(_DS_KEY) or bool(_DS_KEY2)


def load_brand(project: str) -> dict:
    path = PROJECT_ROOT / project / "brand_profile.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_spec(project: str, phase_num: int) -> dict:
    path = PROJECT_ROOT / project / f"phase_{phase_num}" / "content_spec.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_script(project: str, phase_num: int) -> str:
    path = PROJECT_ROOT / project / f"phase_{phase_num}" / "script.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def build_brand_context(brand: dict) -> str:
    forbidden = ", ".join(brand["tone_of_voice"]["forbidden_words"])
    return f"""You are writing content for '{brand["brand_name"]}' — {brand["tagline"]}

Brand voice: {brand["tone_of_voice"]["primary"]}
Forbidden words (never use): {forbidden}
Sentence style: {brand["tone_of_voice"]["sentence_style"]}
Target audience: {brand["target_audience"]}
Platforms: {", ".join(brand["platforms"])}"""


_GEMINI_QUOTA_DEAD = False  # set True once daily quota is confirmed exhausted

def _call_gemini_txt(system_prompt: str, user_prompt: str) -> str:
    global _GEMINI_QUOTA_DEAD
    import time
    if _GEMINI_QUOTA_DEAD:
        raise RuntimeError("Gemini daily quota exhausted (skipping retries)")

    last_err = None
    for attempt in range(3):
        try:
            r = _GEMINI_CLIENT.models.generate_content(
                model=GEMINI_MODEL,
                config=_genai_types.GenerateContentConfig(system_instruction=system_prompt),
                contents=user_prompt,
            )
            return r.text
        except Exception as e:
            last_err = e
            s = str(e)
            if "429" in s or "RESOURCE_EXHAUSTED" in s:
                # Daily/tier quota exhausted — no point retrying, fail fast
                if any(k in s for k in ("PerDay", "free_tier", "FreeTier", "daily", "limit: 20")):
                    _GEMINI_QUOTA_DEAD = True
                    print(f"  [GEMINI] Daily quota exhausted — skipping Gemini for this session.")
                    raise last_err
                import re as __re
                m = __re.search(r'retryDelay[^0-9]*(\d+)', s)
                wait = min(int(m.group(1)) + 5 if m else 30, 30)
                print(f"  [GEMINI] Rate limit. Waiting {wait}s (attempt {attempt+1}/3)...")
                time.sleep(wait)
            elif "503" in s or "UNAVAILABLE" in s:
                time.sleep(2 ** (attempt + 1))
            else:
                raise
    raise last_err


def _call_dashscope_txt(system_prompt: str, user_prompt: str) -> str:
    """Try primary DashScope key; on failure auto-fall back to secondary key."""
    try:
        from openai import OpenAI as _OAI
    except ImportError:
        raise RuntimeError("pip install openai  # needed for DashScope/Qwen")

    configs = []
    if _DS_KEY:  configs.append((_DS_KEY,  _DS_BASE_URL, "DashScope primary"))
    if _DS_KEY2: configs.append((_DS_KEY2, _DS_BASE2,    "DashScope secondary"))
    if not configs:
        raise RuntimeError("No DASHSCOPE_API_KEY or DASHSCOPE_API_KEY_2 set in .env")

    last_err = None
    for key, base_url, label in configs:
        try:
            c = _OAI(api_key=key, base_url=base_url)
            resp = c.chat.completions.create(
                model=_DS_MODEL, max_tokens=2000,
                messages=[{"role": "system", "content": system_prompt},
                           {"role": "user",  "content": user_prompt}],
            )
            if label != "DashScope primary":
                print(f"  [OK] {label} succeeded")
            return resp.choices[0].message.content
        except Exception as e:
            print(f"  [WARN] {label} failed ({str(e)[:80]})"
                  + (" — trying secondary..." if configs.index((key, base_url, label)) < len(configs)-1 else ""))
            last_err = e
    raise last_err


def call_claude(client, system_prompt: str, user_prompt: str) -> str:
    """Call Anthropic -> Gemini -> DashScope/Qwen in cascade order."""
    tried = []

    if client is not None:
        try:
            msg = client.messages.create(
                model=MODEL, max_tokens=2000, system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return msg.content[0].text
        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in _BILLING_ERRORS):
                tried.append(f"Anthropic: {str(e)[:200]}")
                if _GEMINI_OK:
                    print(f"  [WARN] Anthropic unavailable (billing). Trying Gemini...")
                elif _DS_OK:
                    print(f"  [WARN] Anthropic unavailable (billing). Trying Qwen...")
                else:
                    raise
            else:
                raise

    if _GEMINI_OK:
        try:
            return _call_gemini_txt(system_prompt, user_prompt)
        except Exception as e:
            tried.append(f"Gemini: {str(e)[:200]}")
            if _DS_OK:
                print(f"  [WARN] Gemini failed (quota). Trying DashScope/Qwen...")
            else:
                raise RuntimeError(
                    "All providers failed:\n" + "\n".join(f"  - {p}" for p in tried)
                )

    if _DS_OK:
        return _call_dashscope_txt(system_prompt, user_prompt)

    raise RuntimeError("No AI provider available. Set ANTHROPIC_API_KEY, GEMINI_API_KEY, or DASHSCOPE_API_KEY.")


def generate_youtube_description(client, brand_ctx: str, spec: dict, script: str) -> str:
    system = brand_ctx + "\n\nWrite only the YouTube video description — no preamble, no explanation."
    user = f"""Write a YouTube video description for this video:

Title: {spec['title']}
Phase: {spec['phase']} of 5
Tags: {', '.join(spec['tags'][:8])}

Script excerpt (first section):
{script[:1200]}

Requirements:
- 3 paragraphs: hook (2-3 sentences), what viewers will learn (3-4 bullets), CTA
- Include chapter timestamps from content_spec if available
- End with a subscribe CTA that uses the brand name from the system prompt
- NO forbidden words
- Professional, educational tone"""
    return call_claude(client, system, user)


def generate_twitter_thread(client, brand_ctx: str, spec: dict, script: str) -> str:
    system = brand_ctx + "\n\nWrite only the Twitter thread — numbered tweets, no preamble."
    user = f"""Write a 7-tweet Twitter thread about this video:

Title: {spec['title']}
Key insight: {spec.get('youtube', {}).get('description_hook', spec.get('title', ''))}

Script excerpt:
{script[:800]}

Format:
1/ Hook tweet — grab attention with the key stat or insight
2/ The problem (what most people get wrong)
3/ Key concept #1 from the video
4/ Key concept #2 (data point or example)
5/ Key concept #3 (actionable insight)
6/ The takeaway — one clear sentence
7/ CTA — link to full video, subscribe mention

Rules:
- Each tweet max 240 chars
- No forbidden words
- No emojis unless essential
- Direct, factual, no hype"""
    return call_claude(client, system, user)


def generate_linkedin_article(client, brand_ctx: str, spec: dict, script: str) -> str:
    system = brand_ctx + "\n\nWrite only the LinkedIn article — no preamble or explanation."
    user = f"""Write an 800-word LinkedIn article about:

Title: {spec['title']}
Audience: use the target audience from the system prompt

Script basis:
{script[:2000]}

Structure:
- Opening: the key problem or insight (2-3 sentences, no fluff)
- 3-4 substantive sections with headers
- Real data points and examples
- Close: why this matters to professionals
- CTA: link to the full video on YouTube

Tone: use the brand voice and sentence style from the system prompt.
No forbidden words. No investment advice."""
    return call_claude(client, system, user)


def generate_blog_post(client, brand_ctx: str, spec: dict, script: str) -> str:
    system = brand_ctx + "\n\nWrite a complete blog post in Markdown — no preamble."
    user = f"""Write a 1500-word SEO blog post based on this content:

Title: {spec['title']}
SEO keywords: {', '.join(spec['tags'][:5])}
YouTube embed placeholder: [YOUTUBE_EMBED]

Script basis:
{script[:3000]}

Requirements:
- H1: the title
- Meta description at top (1 sentence, 155 chars max)
- Introduction (hook + what reader will learn)
- 4-5 H2 sections matching video structure
- Include the YouTube embed placeholder midway through
- Real examples, data points from the script
- FAQ section (3 questions + answers) at the end
- CTA: subscribe CTA using the brand name from the system prompt

SEO: include primary keyword in H1, first paragraph, and at least 2 H2s.
No forbidden words. No investment advice."""
    return call_claude(client, system, user)


def generate_instagram_caption(client, brand_ctx: str, spec: dict) -> str:
    system = brand_ctx + "\n\nWrite only the Instagram caption — no preamble."
    user = f"""Write an Instagram caption for this video content:

Title: {spec['title']}
Hook: {spec.get('youtube', {}).get('description_hook', spec.get('title', ''))[:200]}
Hashtags to include: {' '.join(spec.get('hashtags', [])[:12])}

Requirements:
- Line 1: strong hook (max 125 chars — visible before 'more')
- 3-4 lines of value: key insights as short punchy statements
- CTA: "Full breakdown in bio 🔗"
- Hashtags on final line (12-15 tags)
- Max 300 words total
- No forbidden words"""
    return call_claude(client, system, user)


def generate_github_readme(client, brand_ctx: str, spec: dict, script: str) -> str:
    system = brand_ctx + "\n\nWrite a GitHub README in Markdown — no preamble."
    user = f"""Write a GitHub README.md for this content series repository.
This README documents Phase {spec['phase']}: {spec['title']}

Include:
- Project badge row: Phase {spec['phase']} | Status: Complete | Brand: Compliant
- Brief overview (2-3 sentences) using the brand name from the system prompt
- What this phase covers (bullet list from script sections)
- File structure table (script.md, infographics, subtitles, compliance)
- Quick links: YouTube video (placeholder), full series
- Brand guidelines note
- Series table listing all phases

Keep it clean, structured, and developer-friendly."""
    return call_claude(client, system, user)


def write_outputs(out_base: Path, content: dict):
    mapping = {
        "youtube/description.txt": content.get("youtube_description", ""),
        "twitter/thread.txt": content.get("twitter_thread", ""),
        "linkedin/article.md": content.get("linkedin_article", ""),
        "blog/post.md": content.get("blog_post", ""),
        "instagram/caption.txt": content.get("instagram_caption", ""),
        "github/README.md": content.get("github_readme", ""),
    }
    for rel_path, text in mapping.items():
        if text:
            full_path = out_base / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(text, encoding="utf-8")
            print(f"  [ok] {rel_path}")


def process_phase(client, project: str, phase_num: int):
    print(f"\n{'='*50}")
    print(f"Generating text content for Phase {phase_num}...")

    brand = load_brand(project)
    spec = load_spec(project, phase_num)
    script = load_script(project, phase_num)
    brand_ctx = build_brand_context(brand)

    out_base = PROJECT_ROOT / project / "_output" / f"phase_{phase_num:02d}"

    content = {}

    print("  Generating YouTube description...")
    content["youtube_description"] = generate_youtube_description(client, brand_ctx, spec, script)

    print("  Generating Twitter thread...")
    content["twitter_thread"] = generate_twitter_thread(client, brand_ctx, spec, script)

    print("  Generating LinkedIn article...")
    content["linkedin_article"] = generate_linkedin_article(client, brand_ctx, spec, script)

    print("  Generating blog post...")
    content["blog_post"] = generate_blog_post(client, brand_ctx, spec, script)

    print("  Generating Instagram caption...")
    content["instagram_caption"] = generate_instagram_caption(client, brand_ctx, spec)

    print("  Generating GitHub README...")
    content["github_readme"] = generate_github_readme(client, brand_ctx, spec, script)

    write_outputs(out_base, content)

    # Write publish checklist
    checklist_path = out_base / "publish_checklist.md"
    checklist = f"""# Publish Checklist — Phase {phase_num}
## {spec['title']}

### Pre-publish
- [ ] Watch final video end-to-end
- [ ] Check all text overlays visible and correct
- [ ] Verify subtitles timing in YouTube Studio
- [ ] Run compliance_checker.py — all PASS

### YouTube
- [ ] Upload `youtube/final_1080p.mp4`
- [ ] Paste description from `youtube/description.txt`
- [ ] Add chapters from content_spec.json
- [ ] Set thumbnail (export from infographic card)
- [ ] Add tags: {', '.join(spec['tags'][:8])}
- [ ] Schedule or publish

### TikTok
- [ ] Upload `tiktok/clip_01_hook.mp4` (hook)
- [ ] Upload `tiktok/clip_02_main.mp4` (main cut)
- [ ] Paste caption from `tiktok/caption_hook.txt`

### Instagram
- [ ] Upload `instagram/reel_60s.mp4`
- [ ] Post carousel: infographic card PNGs
- [ ] Paste caption from `instagram/caption_reel.txt`

### Twitter
- [ ] Post thread from `twitter/thread.txt`
- [ ] Attach `twitter/card_clip.mp4` to first tweet

### LinkedIn
- [ ] Publish article from `linkedin/article.md`
- [ ] Attach `linkedin/clip.mp4` as native video

### Blog
- [ ] Publish post from `blog/post.md`
- [ ] Replace [YOUTUBE_EMBED] with actual embed code

### GitHub
- [ ] Update repo README with `github/README.md`
"""
    checklist_path.write_text(checklist, encoding="utf-8")
    print(f"  [ok] publish_checklist.md")
    print(f"\n[DONE] Phase {phase_num} text content complete -> {out_base}")


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    parser = argparse.ArgumentParser(description="Generate text platform content via Claude API")
    parser.add_argument("--project", default="chain_clarity")
    parser.add_argument("--phase", required=True, help="Phase number or 'all'")
    args = parser.parse_args()

    client = _anthropic_lib.Anthropic(api_key=api_key) if (api_key and _anthropic_lib) else None
    if not client and not _GEMINI_OK:
        print("[ERROR] No AI provider. Set ANTHROPIC_API_KEY or GEMINI_API_KEY in .env")
        sys.exit(1)
    if not client:
        print("  [INFO] Anthropic not available. Using Gemini.")
    phases = list(range(1, 6)) if args.phase == "all" else [int(args.phase)]

    for phase_num in phases:
        process_phase(client, args.project, phase_num)


if __name__ == "__main__":
    main()
