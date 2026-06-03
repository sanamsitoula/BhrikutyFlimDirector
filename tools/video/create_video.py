"""
create_video.py — Seamless video from infographic cards + voiceover + subtitles
================================================================================
Creates a complete YouTube/Shorts video without needing raw screen recordings.

Pipeline:
  1. Screenshot each HTML card with Playwright (or generate colored FFmpeg slides)
  2. Build per-card clips with fade-in / fade-out transitions
  3. Mix in voiceover audio (full duration)
  4. Optionally burn .srt subtitles
  5. Export: YouTube 1920x1080  +  Shorts 1080x1920

Install (optional — needed for HTML card screenshots):
  pip install playwright
  playwright install chromium

Usage:
  python tools/video/create_video.py --project ecoWorld --phase 1
  python tools/video/create_video.py --project ecoWorld --phase 1 --no-screenshots
  python tools/video/create_video.py --project ecoWorld --phase 1 --shorts
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
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

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"
TOOLS_DIR    = Path(__file__).parent.parent.parent / "tools"

# Check FFmpeg
def _check_ffmpeg():
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

# Check Playwright
def _check_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


# ── Audio helpers ─────────────────────────────────────────────────────────────

def get_audio_duration(path: Path) -> float:
    """Return audio duration in seconds using ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 120.0  # fallback 2 minutes


# ── Screenshot via Playwright ─────────────────────────────────────────────────

def screenshot_card(html_path: Path, out_png: Path, width: int = 1080, height: int = 1080):
    """Render HTML card to PNG via headless Chromium (Playwright)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        time.sleep(1.5)  # let CSS animations start
        page.screenshot(path=str(out_png), clip={"x": 0, "y": 0, "width": width, "height": height})
        browser.close()
    print(f"    [screenshot] {html_path.name} -> {out_png.name}")


# ── FFmpeg colored-slide fallback ─────────────────────────────────────────────

def make_color_slide(index: int, title: str, brand: dict, out_png: Path,
                     width: int = 1920, height: int = 1080):
    """Generate a colored slide image with FFmpeg lavfi when Playwright is not available."""
    colors = brand.get("colors", {})
    bg   = colors.get("background", {}).get("hex", "#0F1A14")
    fg   = colors.get("secondary",  {}).get("hex", "#F5A623")
    acc  = colors.get("primary",    {}).get("hex", "#2D7D46")
    bname = brand.get("brand_name", "Brand")

    # Sanitise text for ffmpeg drawtext (escape special chars)
    def _esc(s): return s.replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")

    safe_title = _esc(title[:50])
    safe_brand = _esc(bname)
    card_label = _esc(f"Card {index}")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg}:s={width}x{height}:r=1",
        "-frames:v", "1",
        "-vf", (
            f"drawtext=text='{safe_brand}':fontsize=48:fontcolor={acc}:"
            f"x=(w-text_w)/2:y=80:fontfile=C\\:/Windows/Fonts/arial.ttf,"
            f"drawtext=text='{safe_title}':fontsize=72:fontcolor={fg}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-40:fontfile=C\\:/Windows/Fonts/arial.ttf,"
            f"drawtext=text='{card_label}':fontsize=36:fontcolor=#888888:"
            f"x=(w-text_w)/2:y=h-80:fontfile=C\\:/Windows/Fonts/arial.ttf"
        ),
        str(out_png),
    ], capture_output=True, check=True)
    print(f"    [slide] {out_png.name} (colored FFmpeg slide)")


# ── Build per-card video clips ────────────────────────────────────────────────

def image_to_clip(img: Path, duration: float, out_mp4: Path,
                  width: int = 1920, height: int = 1080, fps: int = 30):
    """Convert a static image to a video clip with ken-burns zoom + fade in/out."""
    fade_dur = min(0.4, duration / 4)
    # Ken-Burns: slow zoom 1.0 → 1.06 over the clip duration
    # zoompan filter: zoom increases by 0.0008 per frame (≈ 2% over 25 frames/sec for 3s)
    zoom_speed = 0.001   # zoom increment per frame
    total_frames = int(duration * fps)
    # Use scale2ref + zoompan for smooth animated zoom
    vf = (
        f"scale={width*2}:{height*2}:force_original_aspect_ratio=decrease,"
        f"pad={width*2}:{height*2}:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='min(zoom+{zoom_speed:.4f},1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s={width}x{height}:fps={fps},"
        f"fade=t=in:st=0:d={fade_dur:.2f},"
        f"fade=t=out:st={duration - fade_dur:.2f}:d={fade_dur:.2f}"
    )
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", str(fps), str(out_mp4),
    ], check=True, capture_output=True)


# ── Concatenate clips ─────────────────────────────────────────────────────────

def concat_clips(clips: list[Path], concat_txt: Path, out_mp4: Path):
    """Concatenate video clips using FFmpeg concat demuxer."""
    lines = [f"file '{c.as_posix()}'\n" for c in clips]
    concat_txt.write_text("".join(lines), encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(out_mp4),
    ], check=True, capture_output=True)


# ── Mix audio ────────────────────────────────────────────────────────────────

def mix_audio(video: Path, audio: Path, out_mp4: Path, burn_srt: Path = None):
    """Mix voiceover into video. Optionally burn subtitles."""
    vf_filter = ""
    if burn_srt and burn_srt.exists():
        safe_srt = str(burn_srt).replace("\\", "/").replace(":", "\\:")
        vf_filter = f"subtitles='{safe_srt}':force_style='FontSize=28,PrimaryColour=&Hffffff&'"

    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(audio)]
    if vf_filter:
        cmd += ["-vf", vf_filter]
    cmd += [
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest",  # trim to shortest stream
        "-map", "0:v:0", "-map", "1:a:0",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


# ── Shorts crop ───────────────────────────────────────────────────────────────

def make_shorts(src: Path, out: Path):
    """Crop 1920x1080 to 1080x1920 (centre crop for Shorts / Reels)."""
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", "crop=1080:1920:420:0",
        "-c:v", "libx264", "-c:a", "aac",
        str(out),
    ], check=True, capture_output=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Create seamless video from phase assets")
    parser.add_argument("--project",        default="chain_clarity")
    parser.add_argument("--phase",          type=int, required=True)
    parser.add_argument("--no-screenshots", action="store_true",
                        help="Skip Playwright; use FFmpeg color slides instead")
    parser.add_argument("--shorts",         action="store_true",
                        help="Also export 1080x1920 YouTube Shorts version")
    parser.add_argument("--burn-subs",      action="store_true",
                        help="Burn subtitles.srt into the video")
    parser.add_argument("--fps",            type=int, default=30)
    args = parser.parse_args()

    if not _check_ffmpeg():
        print("[ERROR] FFmpeg not found. Install with: winget install ffmpeg")
        sys.exit(1)

    phase_dir  = PROJECT_ROOT / args.project / f"phase_{args.phase}"
    assets_dir = phase_dir / "infographic_assets"
    out_base   = PROJECT_ROOT / args.project / "_output" / f"phase_{args.phase:02d}"
    out_base.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*58}")
    print(f"  Video Assembly — {args.project} Phase {args.phase}")
    print(f"{'='*58}\n")

    # ── Load brand colors ────────────────────────────────────────────────────
    brand = {}
    bp = PROJECT_ROOT / args.project / "brand_profile.json"
    if bp.exists():
        brand = json.loads(bp.read_text(encoding="utf-8"))

    # ── Find assets ──────────────────────────────────────────────────────────
    cards = sorted(assets_dir.glob("card_*.html")) if assets_dir.exists() else []
    if not cards:
        print("[ERROR] No infographic cards found (card_*.html in infographic_assets/)")
        print("  Generate with: python tools/generate_phase.py --only card_01.html ...")
        sys.exit(1)

    vo_dir = phase_dir / "voiceover"
    audio_files = sorted([f for f in vo_dir.iterdir()
                           if f.suffix.lower() in (".wav", ".mp3", ".ogg")])  if vo_dir.exists() else []
    if not audio_files:
        print("[WARN] No voiceover audio found. Video will be silent.")
        print("  Generate with: python tools/tts/edge_tts_voiceover.py --project "
              f"{args.project} --phase {args.phase}")
    audio_path = audio_files[0] if audio_files else None

    srt_path   = phase_dir / "subtitles.srt"
    spec_path  = phase_dir / "content_spec.json"
    topic = f"Phase {args.phase}"
    if spec_path.exists():
        try:
            topic = json.loads(spec_path.read_text(encoding="utf-8")).get("title", topic)
        except Exception:
            pass

    print(f"  Cards:    {len(cards)} HTML cards")
    print(f"  Audio:    {audio_path.name if audio_path else 'none (silent)'}")
    print(f"  Subtitles:{' yes' if srt_path.exists() and args.burn_subs else ' no'}")
    print(f"  Topic:    {topic}\n")

    # ── Audio duration ───────────────────────────────────────────────────────
    if audio_path:
        total_sec = get_audio_duration(audio_path)
        print(f"[1/5] Audio duration: {total_sec:.1f}s ({total_sec/60:.1f} min)")
    else:
        total_sec = len(cards) * 8.0  # 8 seconds per card fallback
        print(f"[1/5] No audio — using {total_sec:.0f}s ({len(cards)} cards × 8s)")

    duration_per_card = total_sec / len(cards)
    print(f"       Duration per card: {duration_per_card:.1f}s\n")

    # ── Screenshots / slides ────────────────────────────────────────────────
    use_playwright = not args.no_screenshots and _check_playwright()
    print(f"[2/5] Generating card images "
          f"({'Playwright screenshots' if use_playwright else 'FFmpeg color slides'})...")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        slide_imgs, card_clips = [], []

        for i, card_html in enumerate(cards):
            img_path  = tmp / f"slide_{i:02d}.png"
            clip_path = tmp / f"clip_{i:02d}.mp4"

            # ── Image ──────────────────────────────────────────────────────
            if use_playwright:
                try:
                    screenshot_card(card_html, img_path, 1920, 1080)
                except Exception as e:
                    print(f"    [WARN] Playwright failed: {e} — using color slide")
                    make_color_slide(i + 1, topic, brand, img_path, 1920, 1080)
            else:
                make_color_slide(i + 1, topic, brand, img_path, 1920, 1080)

            slide_imgs.append(img_path)

            # ── Clip ──────────────────────────────────────────────────────
            print(f"    clip {i+1}/{len(cards)} ({duration_per_card:.1f}s)...")
            image_to_clip(img_path, duration_per_card, clip_path, 1920, 1080, args.fps)
            card_clips.append(clip_path)

        # ── Concatenate ────────────────────────────────────────────────────
        print(f"\n[3/5] Concatenating {len(card_clips)} clips...")
        concat_vid = tmp / "concat.mp4"
        concat_txt = tmp / "concat.txt"
        concat_clips(card_clips, concat_txt, concat_vid)

        # ── Mix audio ──────────────────────────────────────────────────────
        final_out = out_base / "youtube" / "final_1080p.mp4"
        final_out.parent.mkdir(parents=True, exist_ok=True)

        print(f"[4/5] Mixing audio{' + burning subtitles' if srt_path.exists() and args.burn_subs else ''}...")
        if audio_path:
            mix_audio(concat_vid, audio_path, final_out,
                      srt_path if args.burn_subs else None)
        else:
            import shutil
            shutil.copy(str(concat_vid), str(final_out))

        size_mb = round(final_out.stat().st_size / 1024 / 1024, 2)
        print(f"  -> {final_out}  ({size_mb} MB)")

        # ── Shorts ─────────────────────────────────────────────────────────
        if args.shorts:
            print(f"\n[5/5] Creating YouTube Shorts (1080x1920)...")
            shorts_out = out_base / "youtube_shorts" / "short_1080x1920.mp4"
            shorts_out.parent.mkdir(parents=True, exist_ok=True)
            make_shorts(final_out, shorts_out)
            print(f"  -> {shorts_out}")
        else:
            print(f"[5/5] Skipped Shorts (use --shorts to generate)")

    print(f"\n{'='*58}")
    print(f"  DONE — Video ready!")
    print(f"  YouTube:  _output/phase_{args.phase:02d}/youtube/final_1080p.mp4")
    if args.shorts:
        print(f"  Shorts:   _output/phase_{args.phase:02d}/youtube_shorts/short_1080x1920.mp4")
    print(f"\n  Improve card rendering:")
    print(f"  pip install playwright && playwright install chromium")
    print(f"  (then re-run — cards will be screenshotted with full CSS animations)")
    print(f"{'='*58}\n")


if __name__ == "__main__":
    main()
