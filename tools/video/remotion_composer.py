"""
remotion_composer.py - Stitch Remotion scene videos + voiceover -> final_1080p.mp4
==================================================================================
Reads pre-rendered MP4 scene files from a Remotion output directory, concatenates
them in scene order, replaces the audio track with the project voiceover, optionally
burns SRT subtitles, and exports:
  - _output/phase_NN/youtube/final_1080p.mp4  (1920x1080)
  - _output/phase_NN/youtube_shorts/short_1080x1920.mp4  (9:16, if --shorts)

Usage:
  python tools/video/remotion_composer.py --project ecoWorld --phase 1
  python tools/video/remotion_composer.py --project ecoWorld --phase 1 --shorts
  python tools/video/remotion_composer.py --project ecoWorld --phase 1 \\
      --remotion-out "D:/claude_project/LearnRemotion/out" --burn-subs
  python tools/video/remotion_composer.py --project ecoWorld --phase 1 --keep-audio

Default Remotion output dir: D:/claude_project/LearnRemotion/out
Override via env var:         REMOTION_OUT_DIR=<path>
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError for box-drawing chars)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# -- Path setup ----------------------------------------------------------------

_ROOT = Path(__file__).parent.parent.parent
_ENV  = _ROOT / ".env"
if _ENV.exists():
    for _l in _ENV.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

PROJECT_ROOT = _ROOT / "youtube_scripts" / "setup" / "projects"

DEFAULT_REMOTION_OUT = Path(
    os.environ.get("REMOTION_OUT_DIR", r"D:\claude_project\LearnRemotion\out")
)


# -- FFmpeg helpers ------------------------------------------------------------

def _ffmpeg(cmd: list, label: str, timeout: int = 900):
    print(f"  [ffmpeg] {label}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        err_lines = [l for l in result.stderr.splitlines() if l.strip()
                     and not l.startswith("frame=") and not l.startswith("fps=")]
        print(f"\n{'='*60}")
        print(f"[FFMPEG ERROR] {label}")
        print(f"  cmd: {' '.join(cmd[:5])} ...")
        print("  " + "\n  ".join(err_lines[-20:]))
        print(f"{'='*60}\n")
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


def _probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _probe_has_audio(path: Path) -> bool:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-select_streams", "a",
         "-show_entries", "stream=codec_type",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=15,
    )
    return bool(r.stdout.strip())


# -- Scene discovery -----------------------------------------------------------

def _scene_sort_key(p: Path) -> int:
    """Extract Scene number from filename for sorting."""
    m = re.search(r'[Ss]cene[-_]?(\d+)', p.stem)
    return int(m.group(1)) if m else 9999


def find_scenes(remotion_out: Path) -> list[Path]:
    """Return MP4 files in remotion_out sorted by scene number."""
    if not remotion_out.exists():
        raise FileNotFoundError(f"Remotion output dir not found: {remotion_out}")
    scenes = sorted(
        [p for p in remotion_out.iterdir() if p.suffix.lower() == ".mp4"],
        key=_scene_sort_key,
    )
    if not scenes:
        raise FileNotFoundError(f"No MP4 files found in {remotion_out}")
    return scenes


# -- Core pipeline -------------------------------------------------------------

def compose(
    project: str,
    phase: int,
    remotion_out: Path,
    burn_subs: bool = False,
    make_shorts: bool = False,
    keep_scene_audio: bool = False,
):
    phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
    out_dir   = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}"
    yt_dir    = out_dir / "youtube"
    yt_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  REMOTION COMPOSER -- {project} / phase {phase}")
    print(f"  Remotion out : {remotion_out}")
    print(f"{'='*60}\n")

    # -- 1. Discover scenes ---------------------------------------------------
    scenes = find_scenes(remotion_out)
    print(f"  Found {len(scenes)} scene(s):")
    total_video_dur = 0.0
    for s in scenes:
        d = _probe_duration(s)
        total_video_dur += d
        print(f"    {s.name}  ({d:.1f}s)")
    print(f"  Total video duration: {total_video_dur:.1f}s\n")

    # -- 2. Concatenate scenes ------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        concat_list = tmp / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{str(s).replace(chr(92), '/')}'" for s in scenes),
            encoding="utf-8",
        )

        concat_mp4 = tmp / "concat_raw.mp4"
        _ffmpeg([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(concat_mp4),
        ], "Concatenate scenes")

        # -- 3. Audio: voiceover or keep scene audio --------------------------
        final_nosub = tmp / "final_nosub.mp4"

        if keep_scene_audio:
            # Just copy the concatenated file as-is
            print("  [AUDIO] Keeping original scene audio")
            concat_mp4.rename(final_nosub)
        else:
            # Find voiceover
            vo_dir   = phase_dir / "voiceover"
            vo_files = sorted(
                [f for f in vo_dir.iterdir()
                 if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".m4a", ".flac")]
            ) if vo_dir.exists() else []

            if not vo_files:
                print("  [AUDIO] No voiceover found - keeping scene audio")
                concat_mp4.rename(final_nosub)
            else:
                vo = vo_files[0]
                vo_dur = _probe_duration(vo)
                print(f"  [AUDIO] Voiceover: {vo.name}  ({vo_dur:.1f}s)")

                # Mix: video stream from concat, audio from voiceover.
                # Trim video to voiceover length OR loop video if voiceover is longer.
                target_dur = max(total_video_dur, vo_dur)
                _ffmpeg([
                    "ffmpeg", "-y",
                    "-i", str(concat_mp4),
                    "-i", str(vo),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",          # clip to whichever ends first
                    str(final_nosub),
                ], "Mix voiceover audio")

        # -- 4. Subtitles -----------------------------------------------------
        srt_path = phase_dir / "subtitles.srt"
        final_1080p = tmp / "final_1080p.mp4"

        if burn_subs and srt_path.exists():
            srt_esc = str(srt_path).replace("\\", "/").replace(":", "\\:")
            _ffmpeg([
                "ffmpeg", "-y",
                "-i", str(final_nosub),
                "-vf", (
                    f"subtitles='{srt_esc}':"
                    "force_style='FontName=Arial,FontSize=16,"
                    "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                    "BorderStyle=3,Outline=2,Shadow=1,Alignment=2'"
                ),
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-c:a", "copy",
                str(final_1080p),
            ], "Burn subtitles")
        else:
            # Re-encode for consistent codec (in case concat was copy)
            _ffmpeg([
                "ffmpeg", "-y",
                "-i", str(final_nosub),
                "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                str(final_1080p),
            ], "Final encode 1080p")

        # -- 5. Copy to output -------------------------------------------------
        out_mp4 = yt_dir / "final_1080p.mp4"
        import shutil
        shutil.copy2(str(final_1080p), str(out_mp4))
        size_mb = round(out_mp4.stat().st_size / 1024 / 1024, 1)
        print(f"\n  [OK] YouTube 1080p -> {out_mp4}  ({size_mb} MB)")

        # -- 6. Shorts (9:16 centre-crop) --------------------------------------
        if make_shorts:
            shorts_dir = out_dir / "youtube_shorts"
            shorts_dir.mkdir(parents=True, exist_ok=True)
            shorts_mp4 = shorts_dir / "short_1080x1920.mp4"

            _ffmpeg([
                "ffmpeg", "-y",
                "-i", str(out_mp4),
                "-vf", (
                    "crop=608:1080:(iw-608)/2:0,"
                    "scale=1080:1920:flags=lanczos"
                ),
                "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                "-c:a", "aac", "-b:a", "160k",
                "-t", "60",                # Shorts max 60s
                "-movflags", "+faststart",
                str(shorts_mp4),
            ], "Export Shorts 9:16 (60s)")
            size_mb_s = round(shorts_mp4.stat().st_size / 1024 / 1024, 1)
            print(f"  [OK] YouTube Shorts -> {shorts_mp4}  ({size_mb_s} MB)")

    print(f"\n{'='*60}")
    print(f"  COMPOSE COMPLETE")
    print(f"  Output: {yt_dir}")
    print(f"{'='*60}\n")
    return str(out_mp4)


# -- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Stitch Remotion scene videos + voiceover into final_1080p.mp4"
    )
    parser.add_argument("--project",     required=True,  help="Brand slug")
    parser.add_argument("--phase",       type=int, required=True)
    parser.add_argument("--remotion-out", default=str(DEFAULT_REMOTION_OUT),
                        help=f"Path to Remotion output dir (default: {DEFAULT_REMOTION_OUT})")
    parser.add_argument("--burn-subs",   action="store_true", help="Burn subtitles.srt into video")
    parser.add_argument("--shorts",      action="store_true", help="Also export 9:16 Shorts version")
    parser.add_argument("--keep-audio",  action="store_true",
                        help="Keep scene audio instead of replacing with voiceover")
    args = parser.parse_args()

    compose(
        project=args.project,
        phase=args.phase,
        remotion_out=Path(args.remotion_out),
        burn_subs=args.burn_subs,
        make_shorts=args.shorts,
        keep_scene_audio=args.keep_audio,
    )


if __name__ == "__main__":
    main()
