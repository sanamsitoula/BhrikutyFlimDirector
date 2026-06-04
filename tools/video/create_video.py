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

# ── FFmpeg / Playwright availability ─────────────────────────────────────────

def _check_ffmpeg():
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def _check_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


# ── Safe FFmpeg runner with detailed stderr on failure ────────────────────────

def _ffmpeg(cmd: list, step_label: str, timeout: int = 600):
    """Run an FFmpeg command; print the last 20 lines of stderr on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        stderr_lines = [l for l in result.stderr.splitlines() if l.strip()]
        # Filter out progress/banner lines to show only real errors
        error_lines = [
            l for l in stderr_lines
            if not l.startswith("frame=") and not l.startswith("fps=")
            and not l.startswith("size=") and "Press [q]" not in l
        ]
        last_errors = "\n    ".join(error_lines[-20:]) if error_lines else result.stderr[-600:]
        print(f"\n{'='*60}")
        print(f"[FFMPEG ERROR] Step: {step_label}")
        print(f"  Exit code : {result.returncode}")
        print(f"  Command   : {' '.join(cmd[:4])} … {cmd[-1]}")
        print(f"  FFmpeg log:")
        print(f"    {last_errors}")
        print(f"{'='*60}\n")
        raise subprocess.CalledProcessError(
            result.returncode, cmd,
            output=result.stdout.encode() if isinstance(result.stdout, str) else result.stdout,
            stderr=result.stderr.encode() if isinstance(result.stderr, str) else result.stderr,
        )
    return result


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


# ── Pillow slide generator (cross-platform, no font-path issues) ──────────────

def _hex_to_rgb(h: str) -> tuple:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _find_font(size: int):
    """Return a PIL ImageFont — tries common system paths, falls back to built-in."""
    from PIL import ImageFont
    candidates = [
        # Windows
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    # PIL built-in (always works, small but readable)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _draw_centered(draw, y: int, text: str, font, fill: str, width: int):
    """Draw text horizontally centred at y."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw = len(text) * (font.size if hasattr(font, 'size') else 10)
    x = max(0, (width - tw) // 2)
    draw.text((x, y), text, fill=fill, font=font)


def make_color_slide(index: int, title: str, brand: dict, out_png: Path,
                     width: int = 1920, height: int = 1080):
    """Generate a branded slide image using Pillow (reliable on all platforms)."""
    from PIL import Image, ImageDraw

    colors = brand.get("colors", {})
    bg_hex  = colors.get("background", {}).get("hex", "#0F1A14")
    fg_hex  = colors.get("secondary",  {}).get("hex", "#F5A623")
    acc_hex = colors.get("primary",    {}).get("hex", "#00D4AA")
    bname   = brand.get("brand_name", "Brand")[:40]

    img  = Image.new("RGB", (width, height), _hex_to_rgb(bg_hex))
    draw = ImageDraw.Draw(img)

    # ── Accent bar at top ──────────────────────────────────────────────────────
    bar_h = max(6, height // 180)
    draw.rectangle([(0, 0), (width, bar_h)], fill=_hex_to_rgb(acc_hex))

    # ── Card index badge (top-left) ────────────────────────────────────────────
    badge_font = _find_font(32)
    draw.text((48, 48), f"CARD {index:02d}", fill=_hex_to_rgb(acc_hex), font=badge_font)

    # ── Brand name ────────────────────────────────────────────────────────────
    brand_font = _find_font(52)
    _draw_centered(draw, 80, bname, brand_font, _hex_to_rgb(acc_hex), width)

    # ── Horizontal rule ───────────────────────────────────────────────────────
    rule_y = 160
    draw.line([(width//4, rule_y), (3*width//4, rule_y)],
              fill=(*_hex_to_rgb(acc_hex), 80), width=2)

    # ── Main title (word-wrapped at ~40 chars per line) ────────────────────────
    import textwrap
    title_lines = textwrap.wrap(title[:120], width=38)
    title_font  = _find_font(82)
    line_h      = 100
    start_y     = height // 2 - (len(title_lines) * line_h) // 2 - 40
    for i, line in enumerate(title_lines[:3]):
        _draw_centered(draw, start_y + i * line_h, line, title_font,
                       _hex_to_rgb(fg_hex), width)

    # ── Bottom caption ────────────────────────────────────────────────────────
    cap_font = _find_font(36)
    _draw_centered(draw, height - 90, f"Phase {index} of Content", cap_font,
                   "#666688", width)

    img.save(str(out_png), "PNG")
    print(f"    [slide] {out_png.name} (Pillow)")


# ── Build per-card video clips ────────────────────────────────────────────────

def image_to_clip(img: Path, duration: float, out_mp4: Path,
                  width: int = 1920, height: int = 1080, fps: int = 30):
    """Convert a static image to a video clip with ken-burns zoom + fade in/out."""
    fade_dur = min(0.4, duration / 4)
    zoom_speed = 0.001
    total_frames = int(duration * fps)
    vf = (
        f"scale={width*2}:{height*2}:force_original_aspect_ratio=decrease,"
        f"pad={width*2}:{height*2}:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='min(zoom+{zoom_speed:.4f},1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s={width}x{height}:fps={fps},"
        f"fade=t=in:st=0:d={fade_dur:.2f},"
        f"fade=t=out:st={duration - fade_dur:.2f}:d={fade_dur:.2f}"
    )
    _ffmpeg([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", str(fps), str(out_mp4),
    ], f"image→clip  {img.name} ({duration:.0f}s → {out_mp4.name})")


# ── Concatenate clips ─────────────────────────────────────────────────────────

def concat_clips(clips: list, concat_txt: Path, out_mp4: Path):
    """Concatenate video clips using FFmpeg concat demuxer."""
    lines = [f"file '{c.as_posix()}'\n" for c in clips]
    concat_txt.write_text("".join(lines), encoding="utf-8")
    _ffmpeg([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(out_mp4),
    ], f"concat  {len(clips)} clips → {out_mp4.name}")


# ── Mix audio ────────────────────────────────────────────────────────────────

def mix_audio(video: Path, audio: Path, out_mp4: Path, burn_srt: Path = None):
    """Mix voiceover into video. Optionally burn subtitles."""
    vf_filter = ""
    if burn_srt and burn_srt.exists():
        # On Windows paths need forward-slashes; colon in drive letter must be escaped
        safe_srt = str(burn_srt).replace("\\", "/")
        # Escape the colon in Windows drive letter e.g. C:/... → C\:/...
        if len(safe_srt) > 1 and safe_srt[1] == ":":
            safe_srt = safe_srt[0] + "\\:" + safe_srt[2:]
        vf_filter = f"subtitles='{safe_srt}':force_style='FontSize=28,PrimaryColour=&Hffffff&'"

    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(audio)]
    if vf_filter:
        cmd += ["-vf", vf_filter]
    cmd += [
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest",
        "-map", "0:v:0", "-map", "1:a:0",
        str(out_mp4),
    ]
    label = "mix audio" + (" + burn subtitles" if vf_filter else "")
    _ffmpeg(cmd, f"{label}  → {out_mp4.name}")


# ── Shorts crop ───────────────────────────────────────────────────────────────

def make_shorts(src: Path, out: Path):
    """Convert 1920×1080 (16:9) → 1080×1920 (9:16) for YouTube Shorts / Reels.

    Approach: take the centre 9:16 crop from the 16:9 source (608×1080),
    then scale up to the target 1080×1920.
      crop_w = round_even(1080 * 9/16) = 608
      x_off  = (1920 - 608) / 2       = 656
    """
    crop_w = 608   # even number closest to 1080 * 9/16 = 607.5
    x_off  = (1920 - crop_w) // 2     # = 656
    vf = f"crop={crop_w}:1080:{x_off}:0,scale=1080:1920:flags=lanczos"
    _ffmpeg([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-c:a", "aac",
        str(out),
    ], f"shorts crop+scale  {src.name} → {out.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Create seamless video from phase assets")
    parser.add_argument("--project",        required=True)
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
    print(f"  Video Assembly — {args.project}  Phase {args.phase}")
    print(f"{'='*58}")
    print(f"  Phase dir : {phase_dir}")
    print(f"  Output    : {out_base}\n")

    # ── Load brand ───────────────────────────────────────────────────────────
    brand = {}
    bp = PROJECT_ROOT / args.project / "brand_profile.json"
    if bp.exists():
        brand = json.loads(bp.read_text(encoding="utf-8"))
    else:
        print(f"[WARN] brand_profile.json not found at {bp}")

    # ── Find assets ──────────────────────────────────────────────────────────
    cards = sorted(assets_dir.glob("card_*.html")) if assets_dir.exists() else []
    if not cards:
        print(f"[ERROR] No infographic cards found")
        print(f"  Expected: {assets_dir}/card_*.html")
        print(f"  Generate: python tools/generate_phase.py --project {args.project} --phase {args.phase} --only card_01.html")
        sys.exit(1)

    vo_dir = phase_dir / "voiceover"
    audio_files = sorted(
        [f for f in vo_dir.iterdir() if f.suffix.lower() in (".wav", ".mp3", ".ogg")]
    ) if vo_dir.exists() else []
    if not audio_files:
        print("[WARN] No voiceover audio found — video will be silent.")
        print(f"  Expected: {vo_dir}/phase_{args.phase}.mp3")
        print(f"  Generate: python tools/tts/edge_tts_voiceover.py --project {args.project} --phase {args.phase}")
    audio_path = audio_files[0] if audio_files else None

    srt_path  = phase_dir / "subtitles.srt"
    spec_path = phase_dir / "content_spec.json"
    topic = f"Phase {args.phase}"
    if spec_path.exists():
        try:
            topic = json.loads(spec_path.read_text(encoding="utf-8")).get("title", topic)
        except Exception:
            pass

    print(f"  Project   : {args.project}")
    print(f"  Cards     : {len(cards)} HTML cards  ({assets_dir})")
    print(f"  Audio     : {audio_path.name if audio_path else 'NONE — will be silent'}  ({audio_path or 'N/A'})")
    print(f"  Subtitles : {'YES — will be burned in' if srt_path.exists() and args.burn_subs else 'no'}")
    print(f"  Topic     : {topic}\n")

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
