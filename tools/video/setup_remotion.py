"""
setup_remotion.py — Bridge between Python phase assets and Remotion
====================================================================
1. Screenshots each HTML card with Playwright (high-quality, with CSS animations)
2. Copies voiceover audio into remotion/public/
3. Parses subtitles.srt → JSON for Remotion
4. Writes remotion/public/phase_data.json with all metadata
5. Installs npm deps if needed
6. Runs `npx remotion render` to produce the final video

Usage:
  python tools/video/setup_remotion.py --project ecoWorld --phase 1
  python tools/video/setup_remotion.py --project ecoWorld --phase 1 --composition BhrikutyShorts
  python tools/video/setup_remotion.py --project ecoWorld --phase 1 --studio   (opens preview)

Requires:
  - Node.js 18+  (check: node --version)
  - FFmpeg        (check: ffmpeg -version)
  - pip install playwright && playwright install chromium  (for screenshots)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import io as _io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load .env
_env = Path(__file__).parent.parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

BASE_DIR     = Path(__file__).parent.parent.parent
PROJECT_ROOT = BASE_DIR / "youtube_scripts" / "setup" / "projects"
REMOTION_DIR = BASE_DIR / "remotion"
PUBLIC_DIR   = REMOTION_DIR / "public"


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_node() -> bool:
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def check_playwright() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False

def get_audio_duration(path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return 60.0


# ── Screenshot HTML card ──────────────────────────────────────────────────────

def screenshot_card_pw(html_path: Path, out_png: Path,
                        width: int = 1080, height: int = 1080):
    """Screenshot with Playwright — captures full CSS animations after settle."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        time.sleep(1.8)  # let entrance animations run
        page.screenshot(
            path=str(out_png),
            clip={"x": 0, "y": 0, "width": width, "height": height}
        )
        browser.close()


def screenshot_card_ffmpeg(card_index: int, brand: dict, out_png: Path,
                            width: int = 1920, height: int = 1080):
    """Fallback: generate a branded color slide with FFmpeg."""
    colors  = brand.get("colors", {})
    bg      = colors.get("background", {}).get("hex", "#0F1A14")
    accent  = colors.get("secondary",  {}).get("hex", "#F5A623")
    primary = colors.get("primary",    {}).get("hex", "#2D7D46")
    bname   = brand.get("brand_name", "Brand")
    topic   = f"Card {card_index}"

    def e(s): return s.replace("'","").replace(":","").replace("\\","")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={bg}:s={width}x{height}:r=1",
        "-frames:v", "1",
        "-vf", (
            f"drawtext=text='{e(bname)}':fontsize=52:fontcolor={primary}:"
            f"x=(w-text_w)/2:y=100,"
            f"drawtext=text='{e(topic)}':fontsize=80:fontcolor={accent}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2"
        ),
        str(out_png),
    ], capture_output=True, check=True)


# ── Parse SRT → JSON ──────────────────────────────────────────────────────────

def parse_srt(srt_path: Path) -> list:
    if not srt_path.exists():
        return []
    content = srt_path.read_text(encoding="utf-8", errors="replace")
    cues = []
    for block in content.strip().split("\n\n"):
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if len(lines) < 3:
            continue
        tc = next((l for l in lines if "-->" in l), None)
        if not tc:
            continue
        def to_sec(t):
            t = t.replace(",", ".")
            p = t.split(":")
            return float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2])
        parts = tc.split("-->")
        text  = " ".join(lines[2:])
        cues.append({
            "start": to_sec(parts[0].strip()),
            "end":   to_sec(parts[1].strip()),
            "text":  text,
        })
    return cues


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Set up Remotion and render video from phase assets"
    )
    parser.add_argument("--project",      default="chain_clarity")
    parser.add_argument("--phase",        type=int, required=True)
    parser.add_argument("--composition",  default="BhrikutyVideo",
                        choices=["BhrikutyVideo", "BhrikutyShorts"],
                        help="Which Remotion composition to render")
    parser.add_argument("--fps",          type=int, default=30)
    parser.add_argument("--studio",       action="store_true",
                        help="Open Remotion Studio (preview) instead of rendering")
    parser.add_argument("--no-screenshots", action="store_true",
                        help="Skip Playwright — use FFmpeg color slides instead")
    args = parser.parse_args()

    phase_dir  = PROJECT_ROOT / args.project / f"phase_{args.phase}"
    assets_dir = phase_dir / "infographic_assets"
    out_base   = PROJECT_ROOT / args.project / "_output" / f"phase_{args.phase:02d}"

    print(f"\n{'='*60}")
    print(f"  Remotion Video Setup — {args.project} Phase {args.phase}")
    print(f"  Composition: {args.composition}")
    print(f"{'='*60}\n")

    if not check_node():
        print("[ERROR] Node.js not found. Install from nodejs.org")
        sys.exit(1)

    # ── Load brand ────────────────────────────────────────────────────────────
    brand = {}
    bp = PROJECT_ROOT / args.project / "brand_profile.json"
    if bp.exists():
        brand = json.loads(bp.read_text(encoding="utf-8"))

    # ── Find cards ────────────────────────────────────────────────────────────
    cards = sorted(assets_dir.glob("card_*.html")) if assets_dir.exists() else []
    if not cards:
        print("[ERROR] No infographic cards found. Generate them first:")
        print(f"  python tools/generate_phase.py --project {args.project} "
              f"--phase {args.phase} --only infographics.md")
        sys.exit(1)

    # ── Find voiceover ────────────────────────────────────────────────────────
    vo_dir = phase_dir / "voiceover"
    audios = sorted([f for f in vo_dir.iterdir()
                     if f.suffix.lower() in (".mp3", ".wav", ".ogg")]) if vo_dir.exists() else []
    if not audios:
        print("[ERROR] No voiceover audio found. Generate it first:")
        print(f"  python tools/tts/edge_tts_voiceover.py "
              f"--project {args.project} --phase {args.phase}")
        sys.exit(1)
    audio_path = audios[0]
    duration   = get_audio_duration(audio_path)
    mins, secs = divmod(int(duration), 60)
    print(f"  Audio:    {audio_path.name}  ({mins}m {secs:02d}s)")
    print(f"  Cards:    {len(cards)} HTML cards")

    # ── Prepare remotion/public/ ──────────────────────────────────────────────
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    use_pw = not args.no_screenshots and check_playwright()
    print(f"\n[1/4] Preparing card images "
          f"({'Playwright screenshots' if use_pw else 'FFmpeg color slides'})...")

    card_pngs = []
    for i, card_html in enumerate(cards):
        out_png = PUBLIC_DIR / f"card_{i+1:02d}.png"
        if use_pw:
            print(f"  Screenshotting {card_html.name}...")
            try:
                screenshot_card_pw(card_html, out_png, 1080, 1080)
            except Exception as e:
                print(f"    [WARN] Playwright failed ({e}) — using color slide")
                screenshot_card_ffmpeg(i + 1, brand, out_png, 1080, 1080)
        else:
            screenshot_card_ffmpeg(i + 1, brand, out_png, 1080, 1080)
        card_pngs.append(f"card_{i+1:02d}.png")
        print(f"    -> {out_png.name}")

    # ── Copy audio ────────────────────────────────────────────────────────────
    print(f"\n[2/4] Copying audio...")
    dest_audio = PUBLIC_DIR / "audio" / audio_path.name
    dest_audio.parent.mkdir(exist_ok=True)
    shutil.copy2(str(audio_path), str(dest_audio))
    print(f"    -> public/audio/{audio_path.name}")

    # ── Parse subtitles ───────────────────────────────────────────────────────
    srt_path = phase_dir / "subtitles.srt"
    subtitles = parse_srt(srt_path)
    print(f"\n[3/4] Subtitles: {len(subtitles)} cues from {srt_path.name}")

    # ── Write phase_data.json ─────────────────────────────────────────────────
    colors = brand.get("colors", {})
    data = {
        "project":    args.project,
        "phase":      args.phase,
        "cards":      [f"card_{i+1:02d}.png" for i in range(len(cards))],
        "audioFile":  f"audio/{audio_path.name}",
        "durationSec": int(duration),
        "fps":        args.fps,
        "brandColors": {
            "bg":      colors.get("background", {}).get("hex", "#0F1A14"),
            "primary": colors.get("primary",    {}).get("hex", "#2D7D46"),
            "accent":  colors.get("secondary",  {}).get("hex", "#F5A623"),
        },
        "subtitles":  subtitles,
    }
    (PUBLIC_DIR / "phase_data.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"    -> public/phase_data.json  (cards={len(cards)}, subs={len(subtitles)})")

    # ── npm install (if needed) ───────────────────────────────────────────────
    if not (REMOTION_DIR / "node_modules").exists():
        print(f"\n[4/4] Installing npm dependencies (first time only)...")
        subprocess.run(["npm", "install"], cwd=str(REMOTION_DIR), check=True)
    else:
        print(f"\n[4/4] npm dependencies already installed")

    # ── Render or open Studio ────────────────────────────────────────────────
    if args.composition == "BhrikutyShorts":
        shorts_dur = min(60, int(duration))
        duration   = shorts_dur
        print(f"\n  Shorts mode: capped at {shorts_dur}s")

    suffix = "shorts" if args.composition == "BhrikutyShorts" else "1080p"
    plat   = "youtube_shorts" if args.composition == "BhrikutyShorts" else "youtube"
    out_dir = out_base / plat
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / f"final_{suffix}.mp4"

    if args.studio:
        print("\nOpening Remotion Studio (preview)...")
        print("Press Ctrl+C to stop.\n")
        subprocess.run(["npx", "remotion", "studio"], cwd=str(REMOTION_DIR))
    else:
        total_frames = int(duration) * args.fps
        print(f"\nRendering {args.composition} → {out_mp4.name}")
        print(f"  Frames: {total_frames}  ({duration}s @ {args.fps}fps)")
        print(f"  This may take {max(1, int(total_frames/200))}–{max(2, int(total_frames/60))} minutes...\n")
        subprocess.run([
            "npx", "remotion", "render",
            args.composition,
            str(out_mp4),
            "--props", str(PUBLIC_DIR / "phase_data.json"),
        ], cwd=str(REMOTION_DIR), check=True)

        size_mb = round(out_mp4.stat().st_size / 1024 / 1024, 2)
        print(f"\n{'='*60}")
        print(f"  DONE!  {out_mp4.name}  ({size_mb} MB)")
        print(f"  Path:  {out_mp4}")
        print(f"  View in dashboard: Audio/Video tab or Outputs tab")
        print(f"{'='*60}\n")

        # Run platform cuts if main video
        if args.composition == "BhrikutyVideo":
            print("Next step — platform cuts:")
            print(f"  python tools/platform_cutter.py "
                  f"--project {args.project} --phase {args.phase} "
                  f"--video {out_mp4}")


if __name__ == "__main__":
    main()
