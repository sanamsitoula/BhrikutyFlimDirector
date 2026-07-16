"""
platform_cutter.py -- Export platform-specific clips from a master video

Per-platform specs
  YouTube         : 1920x1080  16:9   full video  (description only)
  YouTube Shorts  : 1080x1920   9:16  max 60s
  TikTok hook     : 1080x1920   9:16  max 15s
  TikTok main     : 1080x1920   9:16  max 60s
  Instagram Reel  : 1080x1920   9:16  max 90s
  Instagram Post  : 1080x1080   1:1   max 60s
  Twitter / X     : 1280x720   16:9  max 2:20
  LinkedIn        : 1920x1080  16:9  max 10 min  (high quality)

Visual styles  (--video-style, or brand_profile.json > visual_style.video)
  classic | whiteboard | kawaii | anime | watercolor | retroprint | heritage | papercraft

Infographic styles  (content_spec.json > infographic_style)
  animal | sketchnote | anime | editorial | kawaii | instructional |
  bento_grid | bricks | professional

Usage
  python tools/platform_cutter.py --project ecoWorld --phase 1
  python tools/platform_cutter.py --project ecoWorld --phase 1 --video path/to/final.mp4
  python tools/platform_cutter.py --project ecoWorld --phase all
  python tools/platform_cutter.py --project ecoWorld --phase 1 --video-style anime
  python tools/platform_cutter.py --list-styles
"""

import json
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"

# ── Visual style palettes ─────────────────────────────────────────────────────
# text=primary label color, accent=secondary/hashtag color,
# shadow=drop shadow color, opacity=base text alpha

VIDEO_STYLES = {
    "classic": {
        "text":    "#FFFFFF",
        "accent":  "#F5A623",
        "shadow":  "#000000",
        "opacity": 0.88,
        "desc":    "Clean white + gold -- timeless broadcast look",
    },
    "whiteboard": {
        "text":    "#1A1A1A",
        "accent":  "#0066CC",
        "shadow":  "#CCCCCC",
        "opacity": 0.92,
        "desc":    "Dark ink on light-feel background -- educational chalk style",
    },
    "kawaii": {
        "text":    "#FF4B8B",
        "accent":  "#FFCC00",
        "shadow":  "#FF99BB",
        "opacity": 0.90,
        "desc":    "Pastel pink + yellow -- cute, playful, soft",
    },
    "anime": {
        "text":    "#00CFFF",
        "accent":  "#FF2D55",
        "shadow":  "#001A33",
        "opacity": 0.92,
        "desc":    "Electric cyan + red -- high-contrast anime drama",
    },
    "watercolor": {
        "text":    "#5C3D8F",
        "accent":  "#E8A87C",
        "shadow":  "#D4C5E2",
        "opacity": 0.80,
        "desc":    "Soft purples + peach -- painterly, dreamy, light",
    },
    "retroprint": {
        "text":    "#E8D5B7",
        "accent":  "#FF6B35",
        "shadow":  "#3D2B1F",
        "opacity": 0.88,
        "desc":    "Warm sepia + bold orange -- vintage print energy",
    },
    "heritage": {
        "text":    "#C8A97B",
        "accent":  "#8B2E00",
        "shadow":  "#1A0F08",
        "opacity": 0.85,
        "desc":    "Bronze + burgundy -- timeless, authoritative, documentary",
    },
    "papercraft": {
        "text":    "#2C1810",
        "accent":  "#E85D04",
        "shadow":  "#F5E6C8",
        "opacity": 0.82,
        "desc":    "Kraft paper tones + burnt orange -- tactile, handmade feel",
    },
}

# Infographic styles: orientation + native size determine which HTML card template to use
# and which platform they are sized for natively.
INFOGRAPHIC_STYLES = {
    "animal":        {"orientation": "square",    "size": "1080x1080",  "desc": "Illustrated animal mascots -- friendly, memorable, educational"},
    "sketchnote":    {"orientation": "landscape", "size": "1920x1080",  "desc": "Hand-drawn icons + arrows -- visual note-taking, informal"},
    "anime":         {"orientation": "portrait",  "size": "1080x1920",  "desc": "Manga-style panels -- bold outlines, dynamic character poses"},
    "editorial":     {"orientation": "landscape", "size": "1920x1080",  "desc": "Magazine grid -- clean columns, typographic hierarchy"},
    "kawaii":        {"orientation": "square",    "size": "1080x1080",  "desc": "Cute pastel doodles -- round shapes, soft colors, emoji-friendly"},
    "instructional": {"orientation": "portrait",  "size": "1080x1920",  "desc": "Step-by-step numbered diagrams -- arrows, callouts, clear flow"},
    "bento_grid":    {"orientation": "square",    "size": "1080x1080",  "desc": "Modular card boxes -- sections with icons + stats (bento layout)"},
    "bricks":        {"orientation": "landscape", "size": "1920x1080",  "desc": "Bold rectangular color blocks -- graphic, modern, high-contrast"},
    "professional":  {"orientation": "landscape", "size": "1920x1080",  "desc": "Corporate minimal -- white space, data tables, serif headers"},
}


# ── Font helpers ──────────────────────────────────────────────────────────────

def _safe_font():
    for p in [
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if Path(p).exists():
            return p
    return ""


def _safe_font_bold():
    for p in [
        r"C:\Windows\Fonts\Arialbd.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if Path(p).exists():
            return p
    return _safe_font()


def _font_arg(path: str) -> str:
    if not path:
        return ""
    p = path.replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = p[0] + "\\:" + p[2:]
    return f":fontfile='{p}'"


# ── Utilities ─────────────────────────────────────────────────────────────────

def load_brand(project: str) -> dict:
    bp = PROJECT_ROOT / project / "brand_profile.json"
    if bp.exists():
        try:
            return json.loads(bp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"brand_name": project, "tagline": "", "platforms": [], "social": {}}


def count_phases(project: str) -> int:
    proj_dir = PROJECT_ROOT / project
    phases = [d for d in proj_dir.iterdir() if d.is_dir() and d.name.startswith("phase_")]
    return len(phases) if phases else 5


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
        stderr_lines = [ln for ln in result.stderr.splitlines()
                        if ln.strip() and not ln.startswith("frame=")
                        and not ln.startswith("size=") and "Press [q]" not in ln]
        print(f"    [ERROR] FFmpeg failed (exit {result.returncode})")
        print(f"    Command : {' '.join(cmd[:6])} ...")
        print(f"    Details : {chr(10).join(stderr_lines[-10:])}")
        return False
    return True


def _dt(text: str, x: str, y: str, size: int, color: str,
        shadow: str, ff: str, alpha: float) -> str:
    """Build a drawtext filter fragment."""
    sh = f":shadowcolor={shadow}:shadowx=2:shadowy=2" if shadow else ""
    return f"drawtext=text='{text}':fontcolor={color}:fontsize={size}{ff}:x={x}:y={y}:alpha={alpha}{sh}"


def _safe(text: str, max_len: int = 50) -> str:
    return text[:max_len].replace("'", "\\'")


# ── Platform video producers ──────────────────────────────────────────────────

def _base_cmd(input_path, start, duration, vf, crf=20, preset="fast",
              audio_br="128k", output_path="") -> list:
    return [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", input_path,
        "-t", str(min(duration, duration)),  # duration already clamped by caller
        "-vf", vf,
        "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
        "-c:a", "aac", "-b:a", audio_br,
        "-movflags", "+faststart",
        output_path,
    ]


def crop_vertical(input_path, output_path, start, duration,
                  title, hashtags, phase_label, brand_name,
                  style, max_dur=60.0, label="9:16"):
    """Centre-crop 1920x1080 -> 1080x1920 (608px wide strip, scaled up)."""
    dur = min(duration, max_dur)
    ff, ffb = _font_arg(_safe_font()), _font_arg(_safe_font_bold())
    tc, ac, sh, op = style["text"], style["accent"], style["shadow"], style["opacity"]

    filters = [
        "crop=608:1080:656:0",
        "scale=1080:1920",
        _dt(_safe(brand_name, 30), "40", "50",      42, tc, sh, ffb, op),
        _dt(_safe(phase_label),    "w-tw-40", "50", 30, ac, sh, ff,  op * 0.9),
        _dt(_safe(hashtags, 60),   "40", "h-90",    30, ac, sh, ff,  op * 0.8),
        _dt(_safe(title, 50),      "(w-tw)/2", "h-160", 38, tc, sh, ffb, op),
    ]
    cmd = _base_cmd(input_path, start, dur, ",".join(filters),
                    crf=20, preset="fast", audio_br="128k",
                    output_path=output_path)
    return run_ffmpeg(cmd, f"{label} -> {Path(output_path).name}")


def crop_square(input_path, output_path, start, duration,
                title, hashtags, phase_label, brand_name,
                style, max_dur=60.0):
    """Centre-crop 1920x1080 -> 1080x1080 (420px offset from left)."""
    dur = min(duration, max_dur)
    ff, ffb = _font_arg(_safe_font()), _font_arg(_safe_font_bold())
    tc, ac, sh, op = style["text"], style["accent"], style["shadow"], style["opacity"]

    filters = [
        "crop=1080:1080:420:0",
        _dt(_safe(brand_name, 30), "30", "30",         36, tc, sh, ffb, op),
        _dt(_safe(title, 50),      "(w-tw)/2", "h-120", 34, ac, sh, ffb, op),
        _dt(_safe(hashtags, 60),   "30", "h-60",        24, tc, sh, ff,  op * 0.75),
    ]
    cmd = _base_cmd(input_path, start, dur, ",".join(filters),
                    crf=20, preset="fast", audio_br="128k",
                    output_path=output_path)
    return run_ffmpeg(cmd, f"1:1 square -> {Path(output_path).name}")


def cut_twitter(input_path, output_path, start, duration,
                title, hashtags, phase_label, brand_name, style):
    """Scale to 1280x720, hard-cap at 2:20."""
    dur = min(duration, 140.0)
    ff, ffb = _font_arg(_safe_font()), _font_arg(_safe_font_bold())
    tc, ac, sh, op = style["text"], style["accent"], style["shadow"], style["opacity"]

    filters = [
        "scale=1280:720",
        _dt(_safe(brand_name, 30), "30", "22",        32, tc, sh, ffb, op),
        _dt(_safe(phase_label),    "w-tw-30", "22",   24, ac, sh, ff,  op * 0.85),
        _dt(_safe(title, 60),      "30", "h-72",      28, tc, sh, ffb, op),
        _dt(_safe(hashtags, 60),   "30", "h-36",      20, ac, sh, ff,  op * 0.75),
    ]
    cmd = _base_cmd(input_path, start, dur, ",".join(filters),
                    crf=22, preset="fast", audio_br="128k",
                    output_path=output_path)
    return run_ffmpeg(cmd, f"1280x720 (Twitter) -> {Path(output_path).name}")


def cut_linkedin(input_path, output_path, start, duration,
                 title, hashtags, phase_label, brand_name, style):
    """Native 1920x1080, higher quality, cap at 10 min."""
    dur = min(duration, 600.0)
    ff, ffb = _font_arg(_safe_font()), _font_arg(_safe_font_bold())
    tc, ac, sh, op = style["text"], style["accent"], style["shadow"], style["opacity"]

    filters = [
        _dt(_safe(brand_name, 30), "40", "40",       38, tc, sh, ffb, op),
        _dt(_safe(phase_label),    "w-tw-40", "40",  30, ac, sh, ff,  op * 0.85),
        _dt(_safe(title, 60),      "40", "h-100",    36, tc, sh, ffb, op),
        _dt(_safe(hashtags, 60),   "40", "h-55",     26, ac, sh, ff,  op * 0.75),
    ]
    cmd = _base_cmd(input_path, start, dur, ",".join(filters),
                    crf=18, preset="slow", audio_br="192k",
                    output_path=output_path)
    return run_ffmpeg(cmd, f"1920x1080 native (LinkedIn) -> {Path(output_path).name}")


def write_caption_file(output_dir: Path, platform: str, caption: str, hashtags: list):
    p = output_dir / f"caption_{platform}.txt"
    p.write_text(caption + "\n\n" + " ".join(hashtags), encoding="utf-8")
    print(f"  -> caption_{platform}.txt written")


# ── Style resolver ────────────────────────────────────────────────────────────

def resolve_video_style(brand: dict, override: str) -> tuple:
    """Return (name, style_dict). Priority: CLI > brand_profile > 'classic'."""
    name = override or brand.get("visual_style", {}).get("video", "classic")
    style = VIDEO_STYLES.get(name)
    if not style:
        print(f"  [WARN] Unknown video style '{name}', falling back to 'classic'")
        name, style = "classic", VIDEO_STYLES["classic"]
    return name, style


# ── Main processor ────────────────────────────────────────────────────────────

def process_phase(project: str, phase_num: int,
                  video_path: str = None, style_override: str = ""):
    spec_path = PROJECT_ROOT / project / f"phase_{phase_num}" / "content_spec.json"
    if not spec_path.exists():
        print(f"[ERROR] content_spec.json not found: {spec_path}")
        return

    spec  = json.loads(spec_path.read_text(encoding="utf-8"))
    brand = load_brand(project)

    brand_name = brand.get("brand_name", project)
    tagline    = brand.get("tagline", "")
    social     = brand.get("social", {}) or {}
    yt_handle  = social.get("youtube", "").split("/")[-1] or f"@{project}"
    num_phases = count_phases(project)
    phase_label = f"Phase {phase_num} of {num_phases}"

    vstyle_name, vstyle = resolve_video_style(brand, style_override)

    # Infographic style from spec, then brand, then default
    istyle_name = (spec.get("infographic_style")
                   or brand.get("visual_style", {}).get("infographic", "professional"))
    istyle = INFOGRAPHIC_STYLES.get(istyle_name, INFOGRAPHIC_STYLES["professional"])

    print(f"\n{'='*60}")
    print(f"  Platform Cuts -- {project}  Phase {phase_num}")
    print(f"{'='*60}")
    print(f"  Brand             : {brand_name}")
    print(f"  Video style       : {vstyle_name} -- {vstyle['desc']}")
    print(f"  Infographic style : {istyle_name} ({istyle['size']}, {istyle['orientation']}) -- {istyle['desc']}")

    # Locate master video
    if not video_path:
        candidate = PROJECT_ROOT / project / f"_output/phase_{phase_num:02d}/youtube/final_1080p.mp4"
        if candidate.exists():
            video_path = str(candidate)
            print(f"  Source            : {video_path}")
        else:
            print(f"  [WARN] No master video: {candidate}")
            print(f"         Run create_video.py first, or pass --video path/to/file.mp4")
            video_path = None
    else:
        if not Path(video_path).exists():
            print(f"  [ERROR] Video not found: {video_path}")
            video_path = None
        else:
            print(f"  Source            : {video_path}")

    out_base = PROJECT_ROOT / project / "_output" / f"phase_{phase_num:02d}"
    for d in ["youtube", "youtube_shorts", "tiktok", "instagram", "twitter", "linkedin", "blog", "github"]:
        (out_base / d).mkdir(parents=True, exist_ok=True)
    print(f"  Output            : {out_base}\n")

    title    = spec.get("title", f"Phase {phase_num}")
    hashtags = spec.get("hashtags", spec.get("tags", []))
    cuts     = spec.get("platform_cuts", {})

    print(f"Processing: {title}")

    # YouTube description
    yt       = spec.get("youtube", {})
    chapters = "\n".join(f"{c['timestamp']} {c['title']}" for c in yt.get("chapters", []))
    yt_tags  = ", ".join(spec.get("tags", hashtags[:10]))
    yt_desc  = (
        f"{yt.get('description_hook', title)}\n\n"
        f"{'-'*25}\nCHAPTERS\n{'-'*25}\n{chapters}\n\n"
        f"{'-'*25}\n{brand_name} -- {tagline}\n"
        f"Subscribe: {yt_handle}\n\n"
        f"{'-'*25}\nTAGS\n{yt_tags}\n"
    )
    (out_base / "youtube" / "description.txt").write_text(yt_desc, encoding="utf-8")
    print("  -> youtube/description.txt")

    # Caption files
    ht = hashtags[:10]
    cap_map = {
        "tiktok_hook":    (out_base / "tiktok",         "hook",   ht[:5]),
        "tiktok_main":    (out_base / "tiktok",         "main",   ht[:5]),
        "youtube_shorts": (out_base / "youtube_shorts", "shorts", ht[:5]),
        "instagram_reel": (out_base / "instagram",      "reel",   ht[:10]),
        "instagram_post": (out_base / "instagram",      "post",   ht[:10]),
        "twitter_clip":   (out_base / "twitter",        "clip",   ht[:4]),
        "linkedin_clip":  (out_base / "linkedin",       "clip",   ht[:4]),
    }
    for key, (d, plat, tags) in cap_map.items():
        if key in cuts:
            write_caption_file(d, plat, cuts[key].get("caption", title), tags)

    # Video clips
    if not video_path:
        print("  [SKIP] No master video -- text outputs only")
        print(f"\n  [OK] Phase {phase_num} outputs (text only) -> {out_base}")
        return

    tags_str = " ".join(f"#{t.strip('#')}" for t in hashtags[:4])

    # Shared kwargs minus output_path and duration-cap
    def kw(cut):
        s = time_to_seconds(cut["start"])
        d = time_to_seconds(cut["end"]) - s
        return dict(input_path=video_path, start=s, duration=d,
                    title=title, hashtags=tags_str,
                    phase_label=phase_label, brand_name=brand_name,
                    style=vstyle)

    dispatch = {
        # key:  (function, output_path, extra_kwargs)
        "tiktok_hook":    lambda c: crop_vertical(**kw(c),
                              output_path=str(out_base / "tiktok" / "clip_01_hook.mp4"),
                              max_dur=15.0, label="TikTok hook 9:16"),
        "tiktok_main":    lambda c: crop_vertical(**kw(c),
                              output_path=str(out_base / "tiktok" / "clip_02_main.mp4"),
                              max_dur=60.0, label="TikTok main 9:16"),
        "youtube_shorts": lambda c: crop_vertical(**kw(c),
                              output_path=str(out_base / "youtube_shorts" / "short_1080x1920.mp4"),
                              max_dur=60.0, label="YT Shorts 9:16"),
        "instagram_reel": lambda c: crop_vertical(**kw(c),
                              output_path=str(out_base / "instagram" / "reel_60s.mp4"),
                              max_dur=90.0, label="Instagram Reel 9:16"),
        "instagram_post": lambda c: crop_square(**kw(c),
                              output_path=str(out_base / "instagram" / "post_1080x1080.mp4"),
                              max_dur=60.0),
        "twitter_clip":   lambda c: cut_twitter(**kw(c),
                              output_path=str(out_base / "twitter" / "card_clip.mp4")),
        "linkedin_clip":  lambda c: cut_linkedin(**kw(c),
                              output_path=str(out_base / "linkedin" / "clip.mp4")),
    }

    for key, cut in cuts.items():
        if key in dispatch:
            dispatch[key](cut)
        else:
            print(f"  [SKIP] Unknown cut key '{key}'")

    print(f"\n  [OK] Phase {phase_num} outputs -> {out_base}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def list_styles():
    print("\nVideo styles  (--video-style  or  brand_profile.json > visual_style.video)")
    print(f"  {'Name':<14}  Description")
    print(f"  {'-'*14}  {'-'*55}")
    for name, s in VIDEO_STYLES.items():
        print(f"  {name:<14}  {s['desc']}")

    print("\nInfographic styles  (content_spec.json > infographic_style)")
    print(f"  {'Name':<14}  {'Size':<12}  {'Orient':<10}  Description")
    print(f"  {'-'*14}  {'-'*12}  {'-'*10}  {'-'*45}")
    for name, s in INFOGRAPHIC_STYLES.items():
        print(f"  {name:<14}  {s['size']:<12}  {s['orientation']:<10}  {s['desc']}")

    print("\nPlatform cut keys (platform_cuts in content_spec.json):")
    rows = [
        ("tiktok_hook",    "1080x1920", "9:16",  "max 15s"),
        ("tiktok_main",    "1080x1920", "9:16",  "max 60s"),
        ("youtube_shorts", "1080x1920", "9:16",  "max 60s"),
        ("instagram_reel", "1080x1920", "9:16",  "max 90s"),
        ("instagram_post", "1080x1080", "1:1",   "max 60s"),
        ("twitter_clip",   "1280x720",  "16:9",  "max 2:20"),
        ("linkedin_clip",  "1920x1080", "16:9",  "max 10 min, high quality"),
    ]
    print(f"  {'Key':<20}  {'Output':<12}  {'AR':<6}  Limit")
    print(f"  {'-'*20}  {'-'*12}  {'-'*6}  {'-'*25}")
    for r in rows:
        print(f"  {r[0]:<20}  {r[1]:<12}  {r[2]:<6}  {r[3]}")


def main():
    parser = argparse.ArgumentParser(
        description="Export platform-specific clips from a master 1080p video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project",     help="Project slug (e.g. ecoWorld)")
    parser.add_argument("--phase",       help="Phase number or 'all'")
    parser.add_argument("--video",       default="", help="Override master video path")
    parser.add_argument("--video-style", default="", dest="video_style",
                        help="Visual style: classic|whiteboard|kawaii|anime|watercolor|retroprint|heritage|papercraft")
    parser.add_argument("--list-styles", action="store_true", dest="list_styles",
                        help="Print all visual styles and platform specs, then exit")
    args = parser.parse_args()

    if args.list_styles:
        list_styles()
        return

    if not args.project or not args.phase:
        parser.error("--project and --phase are required (or use --list-styles)")

    phases = (list(range(1, count_phases(args.project) + 1))
              if args.phase == "all" else [int(args.phase)])
    for phase_num in phases:
        process_phase(args.project, phase_num,
                      args.video or None, args.video_style)


if __name__ == "__main__":
    main()
