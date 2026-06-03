"""
platform_cutter.py — Export platform-specific clips from a master video
Usage: python tools/platform_cutter.py --project chain_clarity --phase 4
       python tools/platform_cutter.py --project chain_clarity --phase all --video path/to/final.mp4
"""

import json
import subprocess
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"
OUTPUT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"

# Brand watermark colors (for drawtext overlay)
BRAND_TEAL = "#00D4AA"
BRAND_SLATE = "#8B9BB4"
BRAND_GOLD = "#F5A623"
BRAND_NAVY = "#0A0E1A"


def time_to_seconds(t: str) -> float:
    """Convert '1:30' or '0:15' to seconds float."""
    parts = t.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(t)


def run_ffmpeg(cmd: list, label: str) -> bool:
    print(f"  -> {label}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [ERROR] ffmpeg failed: {result.stderr[-300:]}")
        return False
    return True


def crop_to_vertical(input_path: str, output_path: str, start: float, duration: float,
                     title: str, hashtags: str, phase_label: str, srt_path: str = None) -> bool:
    """Crop 16:9 to 9:16, add brand overlays, optionally burn subtitles."""
    filters = []

    # Crop center of 1920x1080 to 608x1080, then scale to 1080x1920
    filters.append("crop=608:1080:656:0")
    filters.append("scale=1080:1920")

    # Brand watermark: channel name top-left
    filters.append(
        f"drawtext=text='Chain Clarity':fontcolor=#FFFFFF:fontsize=42:"
        f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        f"x=40:y=50:alpha=0.85"
    )

    # Phase label top-right
    safe_phase = phase_label.replace("'", "\\'")
    filters.append(
        f"drawtext=text='{safe_phase}':fontcolor={BRAND_SLATE}:fontsize=32:"
        f"fontfile='C\\:/Windows/Fonts/arial.ttf':"
        f"x=w-tw-40:y=50:alpha=0.85"
    )

    # Hashtag strip bottom-left
    safe_tags = hashtags.replace("'", "\\'")[:60]
    filters.append(
        f"drawtext=text='{safe_tags}':fontcolor={BRAND_SLATE}:fontsize=30:"
        f"fontfile='C\\:/Windows/Fonts/arial.ttf':"
        f"x=40:y=h-90:alpha=0.75"
    )

    # Title lower-third (bottom center)
    safe_title = title[:50].replace("'", "\\'")
    filters.append(
        f"drawtext=text='{safe_title}':fontcolor={BRAND_TEAL}:fontsize=38:"
        f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        f"x=(w-tw)/2:y=h-160:alpha=0.9"
    )

    vf_str = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-vf", vf_str,
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]
    return run_ffmpeg(cmd, f"Crop to 9:16 -> {Path(output_path).name}")


def cut_horizontal(input_path: str, output_path: str, start: float, duration: float,
                   title: str, hashtags: str, phase_label: str) -> bool:
    """Cut 16:9 clip with brand overlays."""
    safe_title = title[:60].replace("'", "\\'")
    safe_phase = phase_label.replace("'", "\\'")
    safe_tags = hashtags.replace("'", "\\'")[:60]

    vf = (
        f"drawtext=text='Chain Clarity':fontcolor=#FFFFFF:fontsize=38:"
        f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':x=40:y=40:alpha=0.85,"
        f"drawtext=text='{safe_phase}':fontcolor={BRAND_SLATE}:fontsize=30:"
        f"fontfile='C\\:/Windows/Fonts/arial.ttf':x=w-tw-40:y=40:alpha=0.8,"
        f"drawtext=text='{safe_title}':fontcolor={BRAND_TEAL}:fontsize=36:"
        f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':x=40:y=h-100:alpha=0.9,"
        f"drawtext=text='{safe_tags}':fontcolor={BRAND_SLATE}:fontsize=26:"
        f"fontfile='C\\:/Windows/Fonts/arial.ttf':x=40:y=h-55:alpha=0.75"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]
    return run_ffmpeg(cmd, f"Cut 16:9 -> {Path(output_path).name}")


def write_caption_file(output_dir: Path, platform: str, caption: str, hashtags: list):
    caption_path = output_dir / f"caption_{platform}.txt"
    full_caption = caption + "\n\n" + " ".join(hashtags)
    caption_path.write_text(full_caption, encoding="utf-8")
    print(f"  -> caption_{platform}.txt written")


def process_phase(project: str, phase_num: int, video_path: str = None):
    spec_path = PROJECT_ROOT / project / f"phase_{phase_num}" / "content_spec.json"
    if not spec_path.exists():
        print(f"[ERROR] content_spec.json not found for phase {phase_num}")
        return

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    # Locate master video
    if not video_path:
        # Try common locations
        candidates = [
            PROJECT_ROOT / project / f"_output/phase_{phase_num:02d}/youtube/final_1080p.mp4",
            Path(__file__).parent.parent / "myvideo" / "edit" / "final.mp4",
        ]
        video_path = next((str(c) for c in candidates if c.exists()), None)

    if not video_path or not Path(video_path).exists():
        print(f"[WARN] No master video found for phase {phase_num}. Skipping video cuts.")
        print("       Run: python tools/platform_cutter.py --phase 4 --video path/to/final.mp4")
        video_path = None

    # Output directory
    out_base = PROJECT_ROOT / project / f"_output" / f"phase_{phase_num:02d}"
    platforms = ["youtube", "tiktok", "instagram", "twitter", "linkedin", "blog", "github"]
    for p in platforms:
        (out_base / p).mkdir(parents=True, exist_ok=True)

    title = spec["title"]
    phase_label = f"Phase {phase_num} of 5"
    hashtags = spec.get("hashtags", [])
    cuts = spec.get("platform_cuts", {})

    print(f"\nProcessing Phase {phase_num}: {title}")

    # Write YouTube description
    yt = spec.get("youtube", {})
    chapters_text = "\n".join(
        f"{c['timestamp']} {c['title']}" for c in yt.get("chapters", [])
    )
    youtube_tags = ", ".join(spec.get("tags", []))
    yt_desc = f"""{yt.get('description_hook', title)}

━━━━━━━━━━━━━━━━━━━━━━━━━
CHAPTERS
━━━━━━━━━━━━━━━━━━━━━━━━━
{chapters_text}

━━━━━━━━━━━━━━━━━━━━━━━━━
Chain Clarity — Blockchain without the noise.
Subscribe for weekly breakdowns: @chainclarity
Website: chainclarity.io

━━━━━━━━━━━━━━━━━━━━━━━━━
TAGS
{youtube_tags}
"""
    (out_base / "youtube" / "description.txt").write_text(yt_desc, encoding="utf-8")
    print("  -> youtube/description.txt")

    # Write captions for each platform
    if "tiktok_hook" in cuts:
        write_caption_file(out_base / "tiktok", "hook", cuts["tiktok_hook"].get("caption", title), hashtags[:5])
    if "tiktok_main" in cuts:
        write_caption_file(out_base / "tiktok", "main", cuts["tiktok_main"].get("caption", title), hashtags[:5])
    if "instagram_reel" in cuts:
        write_caption_file(out_base / "instagram", "reel", cuts["instagram_reel"].get("caption", title), hashtags[:10])
    if "twitter_clip" in cuts:
        write_caption_file(out_base / "twitter", "clip", cuts["twitter_clip"].get("caption", title), hashtags[:4])
    if "linkedin_clip" in cuts:
        write_caption_file(out_base / "linkedin", "clip", cuts["linkedin_clip"].get("caption", title), hashtags[:4])

    # Export video clips if master video is available
    if video_path:
        srt_path = PROJECT_ROOT / project / f"phase_{phase_num}" / "subtitles.srt"
        srt_str = str(srt_path) if srt_path.exists() else None
        tags_str = " ".join(hashtags[:4])

        for platform_key, cut in cuts.items():
            start = time_to_seconds(cut["start"])
            end = time_to_seconds(cut["end"])
            duration = end - start
            aspect = cut.get("aspect", "16:9")
            caption = cut.get("caption", title)

            if platform_key == "tiktok_hook":
                out = str(out_base / "tiktok" / "clip_01_hook.mp4")
                crop_to_vertical(video_path, out, start, duration, title, tags_str, phase_label, srt_str)

            elif platform_key == "tiktok_main":
                out = str(out_base / "tiktok" / "clip_02_main.mp4")
                crop_to_vertical(video_path, out, start, duration, title, tags_str, phase_label, srt_str)

            elif platform_key == "instagram_reel":
                out = str(out_base / "instagram" / "reel_60s.mp4")
                crop_to_vertical(video_path, out, start, duration, title, tags_str, phase_label, srt_str)

            elif platform_key == "twitter_clip":
                out = str(out_base / "twitter" / "card_clip.mp4")
                cut_horizontal(video_path, out, start, duration, title, tags_str, phase_label)

            elif platform_key == "linkedin_clip":
                out = str(out_base / "linkedin" / "clip.mp4")
                cut_horizontal(video_path, out, start, duration, title, tags_str, phase_label)

    print(f"  [ok] Phase {phase_num} platform outputs written to {out_base}")


def main():
    parser = argparse.ArgumentParser(description="Export platform-specific clips from master video")
    parser.add_argument("--project", default="chain_clarity")
    parser.add_argument("--phase", required=True, help="Phase number or 'all'")
    parser.add_argument("--video", help="Path to master 1080p video file")
    args = parser.parse_args()

    phases = list(range(1, 6)) if args.phase == "all" else [int(args.phase)]
    for phase_num in phases:
        process_phase(args.project, phase_num, args.video)


if __name__ == "__main__":
    main()
