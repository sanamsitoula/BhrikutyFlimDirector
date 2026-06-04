"""
platform_cutter.py — Export platform-specific clips from a master video
Usage:
  python tools/platform_cutter.py --project ecoWorld --phase 1
  python tools/platform_cutter.py --project ecoWorld --phase 1 --video path/to/final.mp4
  python tools/platform_cutter.py --project ecoWorld --phase all
"""

import json
import subprocess
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"

BRAND_TEAL  = "#00D4AA"
BRAND_SLATE = "#8B9BB4"
BRAND_GOLD  = "#F5A623"
BRAND_NAVY  = "#0A0E1A"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_brand(project: str) -> dict:
    """Load brand_profile.json for the given project slug."""
    bp = PROJECT_ROOT / project / "brand_profile.json"
    if bp.exists():
        try:
            return json.loads(bp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"brand_name": project, "tagline": "", "platforms": [], "social": {}}


def count_phases(project: str) -> int:
    """Return how many phase_N directories exist."""
    proj_dir = PROJECT_ROOT / project
    phases = [d for d in proj_dir.iterdir() if d.is_dir() and d.name.startswith("phase_")]
    return len(phases) if phases else 5


def _safe_font():
    """Return a font path that exists on this machine, or empty string."""
    candidates = [
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return ""


def _safe_font_bold():
    candidates = [
        r"C:\Windows\Fonts\Arialbd.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return _safe_font()


def _font_arg(path: str) -> str:
    """Convert font path to FFmpeg drawtext fontfile argument."""
    if not path:
        return ""
    # On Windows, FFmpeg needs forward-slashes and escaped colon in drive letter
    p = path.replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = p[0] + "\\:" + p[2:]
    return f":fontfile='{p}'"


def time_to_seconds(t: str) -> float:
    parts = t.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(t)


def run_ffmpeg(cmd: list, label: str) -> bool:
    print(f"  -> {label}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr_lines = [l for l in result.stderr.splitlines()
                        if l.strip() and not l.startswith("frame=")
                        and not l.startswith("size=") and "Press [q]" not in l]
        print(f"    [ERROR] FFmpeg failed (exit {result.returncode})")
        print(f"    Command : {' '.join(cmd[:5])} …")
        print(f"    Details : {chr(10).join(stderr_lines[-10:])}")
        return False
    return True


# ── Video filters ─────────────────────────────────────────────────────────────

def crop_to_vertical(input_path: str, output_path: str,
                     start: float, duration: float,
                     title: str, hashtags: str, phase_label: str,
                     brand_name: str) -> bool:
    """Crop 16:9 → 9:16 with brand watermark. No hardcoded brand names."""
    font     = _safe_font()
    font_b   = _safe_font_bold()
    ff       = _font_arg(font)
    ffb      = _font_arg(font_b)
    safe_brand = brand_name.replace("'", "\\'")[:30]
    safe_phase = phase_label.replace("'", "\\'")
    safe_tags  = hashtags.replace("'", "\\'")[:60]
    safe_title = title[:50].replace("'", "\\'")

    # centre-crop 9:16 from 16:9 (608×1080 from 1920×1080) then scale to 1080×1920
    filters = [
        "crop=608:1080:656:0",
        "scale=1080:1920",
        f"drawtext=text='{safe_brand}':fontcolor=#FFFFFF:fontsize=42{ffb}:x=40:y=50:alpha=0.85",
        f"drawtext=text='{safe_phase}':fontcolor={BRAND_SLATE}:fontsize=32{ff}:x=w-tw-40:y=50:alpha=0.85",
        f"drawtext=text='{safe_tags}':fontcolor={BRAND_SLATE}:fontsize=30{ff}:x=40:y=h-90:alpha=0.75",
        f"drawtext=text='{safe_title}':fontcolor={BRAND_TEAL}:fontsize=38{ffb}:x=(w-tw)/2:y=h-160:alpha=0.9",
    ]

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", input_path,
        "-t", str(duration),
        "-vf", ",".join(filters),
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    return run_ffmpeg(cmd, f"Crop to 9:16 → {Path(output_path).name}")


def cut_horizontal(input_path: str, output_path: str,
                   start: float, duration: float,
                   title: str, hashtags: str, phase_label: str,
                   brand_name: str) -> bool:
    """Cut 16:9 clip with brand overlays."""
    font   = _safe_font()
    font_b = _safe_font_bold()
    ff     = _font_arg(font)
    ffb    = _font_arg(font_b)
    safe_brand = brand_name.replace("'", "\\'")[:30]
    safe_phase = phase_label.replace("'", "\\'")
    safe_title = title[:60].replace("'", "\\'")
    safe_tags  = hashtags.replace("'", "\\'")[:60]

    vf = (
        f"drawtext=text='{safe_brand}':fontcolor=#FFFFFF:fontsize=38{ffb}:x=40:y=40:alpha=0.85,"
        f"drawtext=text='{safe_phase}':fontcolor={BRAND_SLATE}:fontsize=30{ff}:x=w-tw-40:y=40:alpha=0.8,"
        f"drawtext=text='{safe_title}':fontcolor={BRAND_TEAL}:fontsize=36{ffb}:x=40:y=h-100:alpha=0.9,"
        f"drawtext=text='{safe_tags}':fontcolor={BRAND_SLATE}:fontsize=26{ff}:x=40:y=h-55:alpha=0.75"
    )
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", input_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    return run_ffmpeg(cmd, f"Cut 16:9 → {Path(output_path).name}")


def write_caption_file(output_dir: Path, platform: str, caption: str, hashtags: list):
    caption_path = output_dir / f"caption_{platform}.txt"
    caption_path.write_text(caption + "\n\n" + " ".join(hashtags), encoding="utf-8")
    print(f"  -> caption_{platform}.txt written")


# ── Main phase processor ──────────────────────────────────────────────────────

def process_phase(project: str, phase_num: int, video_path: str = None):
    spec_path = PROJECT_ROOT / project / f"phase_{phase_num}" / "content_spec.json"
    if not spec_path.exists():
        print(f"[ERROR] content_spec.json not found: {spec_path}")
        return

    spec  = json.loads(spec_path.read_text(encoding="utf-8"))
    brand = load_brand(project)

    brand_name  = brand.get("brand_name", project)
    tagline     = brand.get("tagline", "")
    social      = brand.get("social", {}) or {}
    yt_handle   = social.get("youtube", "").split("/")[-1] or f"@{project}"
    num_phases  = count_phases(project)
    phase_label = f"Phase {phase_num} of {num_phases}"

    print(f"\n{'='*58}")
    print(f"  Platform Cuts — {project}  Phase {phase_num}")
    print(f"{'='*58}")
    print(f"  Brand     : {brand_name}")
    print(f"  Phase dir : {PROJECT_ROOT / project / f'phase_{phase_num}'}")

    # ── Locate master video ──────────────────────────────────────────────────
    if not video_path:
        candidate = PROJECT_ROOT / project / f"_output/phase_{phase_num:02d}/youtube/final_1080p.mp4"
        if candidate.exists():
            video_path = str(candidate)
            print(f"  Source    : {video_path}  (auto-detected)")
        else:
            print(f"[WARN] No master video found: {candidate}")
            print(f"       Run create_video.py first, or pass --video path/to/file.mp4")
            video_path = None
    else:
        if not Path(video_path).exists():
            print(f"[ERROR] Video file not found: {video_path}")
            video_path = None
        else:
            print(f"  Source    : {video_path}")

    # ── Output directories ───────────────────────────────────────────────────
    out_base = PROJECT_ROOT / project / "_output" / f"phase_{phase_num:02d}"
    for p in ["youtube", "youtube_shorts", "tiktok", "instagram", "twitter", "linkedin", "blog", "github"]:
        (out_base / p).mkdir(parents=True, exist_ok=True)
    print(f"  Output    : {out_base}\n")

    title    = spec.get("title", f"Phase {phase_num}")
    hashtags = spec.get("hashtags", spec.get("tags", []))
    cuts     = spec.get("platform_cuts", {})

    print(f"Processing Phase {phase_num}: {title}")

    # ── YouTube description ──────────────────────────────────────────────────
    yt       = spec.get("youtube", {})
    chapters = "\n".join(
        f"{c['timestamp']} {c['title']}" for c in yt.get("chapters", [])
    )
    yt_tags   = ", ".join(spec.get("tags", hashtags[:10]))
    yt_desc   = (
        f"{yt.get('description_hook', title)}\n\n"
        f"{'━'*25}\nCHAPTERS\n{'━'*25}\n{chapters}\n\n"
        f"{'━'*25}\n{brand_name} — {tagline}\n"
        f"Subscribe: {yt_handle}\n\n"
        f"{'━'*25}\nTAGS\n{yt_tags}\n"
    )
    (out_base / "youtube" / "description.txt").write_text(yt_desc, encoding="utf-8")
    print("  -> youtube/description.txt")

    # ── Caption files ────────────────────────────────────────────────────────
    ht = hashtags[:10]
    if "tiktok_hook"     in cuts: write_caption_file(out_base / "tiktok",    "hook",  cuts["tiktok_hook"].get("caption",    title), ht[:5])
    if "tiktok_main"     in cuts: write_caption_file(out_base / "tiktok",    "main",  cuts["tiktok_main"].get("caption",    title), ht[:5])
    if "instagram_reel"  in cuts: write_caption_file(out_base / "instagram", "reel",  cuts["instagram_reel"].get("caption", title), ht[:10])
    if "twitter_clip"    in cuts: write_caption_file(out_base / "twitter",   "clip",  cuts["twitter_clip"].get("caption",   title), ht[:4])
    if "linkedin_clip"   in cuts: write_caption_file(out_base / "linkedin",  "clip",  cuts["linkedin_clip"].get("caption",  title), ht[:4])

    # ── Video clips ──────────────────────────────────────────────────────────
    if video_path:
        tags_str = " ".join(f"#{t.strip('#')}" for t in hashtags[:4])
        for key, cut in cuts.items():
            start    = time_to_seconds(cut["start"])
            end      = time_to_seconds(cut["end"])
            duration = end - start
            caption  = cut.get("caption", title)

            if key == "tiktok_hook":
                crop_to_vertical(video_path, str(out_base / "tiktok" / "clip_01_hook.mp4"),
                                 start, duration, title, tags_str, phase_label, brand_name)
            elif key == "tiktok_main":
                crop_to_vertical(video_path, str(out_base / "tiktok" / "clip_02_main.mp4"),
                                 start, duration, title, tags_str, phase_label, brand_name)
            elif key == "instagram_reel":
                crop_to_vertical(video_path, str(out_base / "instagram" / "reel_60s.mp4"),
                                 start, duration, title, tags_str, phase_label, brand_name)
            elif key == "twitter_clip":
                cut_horizontal(video_path, str(out_base / "twitter" / "card_clip.mp4"),
                               start, duration, title, tags_str, phase_label, brand_name)
            elif key == "linkedin_clip":
                cut_horizontal(video_path, str(out_base / "linkedin" / "clip.mp4"),
                               start, duration, title, tags_str, phase_label, brand_name)
    else:
        print("  [SKIP] No master video — text outputs only (captions, description)")

    print(f"\n  [OK] Phase {phase_num} outputs → {out_base}")


def main():
    parser = argparse.ArgumentParser(description="Export platform clips from master video")
    parser.add_argument("--project", required=True, help="Brand project slug (e.g. ecoWorld)")
    parser.add_argument("--phase",   required=True, help="Phase number or 'all'")
    parser.add_argument("--video",   default="",    help="Path to master 1080p MP4")
    args = parser.parse_args()

    phases = list(range(1, count_phases(args.project) + 1)) if args.phase == "all" \
             else [int(args.phase)]
    for phase_num in phases:
        process_phase(args.project, phase_num, args.video or None)


if __name__ == "__main__":
    main()
