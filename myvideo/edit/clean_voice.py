"""
Clean a raw voice sample for use as a Qwen3-TTS voice-clone reference.

Usage:
  python clean_voice.py <input_audio>            # auto-detects best 8s clip
  python clean_voice.py <input_audio> --start 4  # start trim at 4 seconds
  python clean_voice.py <input_audio> --full      # keep entire file

Output:  D:\bhrikuty\myvideo\edit\voiceover\ref_clean.wav
         D:\bhrikuty\myvideo\edit\voiceover\ref_preview.wav  (same, for listening)

Requirements: ffmpeg on PATH (already installed)
"""
import subprocess
import sys
import argparse
import json
from pathlib import Path

OUT_DIR  = Path(r"D:\bhrikuty\myvideo\edit\voiceover")
OUT_REF  = OUT_DIR / "ref_clean.wav"
OUT_PREV = OUT_DIR / "ref_preview.wav"

# Target: 8 seconds of clean speech — long enough for good clone, short enough to process fast
CLIP_DURATION = 8.0


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    info = json.loads(r.stdout)
    for s in info.get("streams", []):
        if s.get("codec_type") == "audio":
            return float(s.get("duration", 0))
    return 0.0


def clean(src: Path, start: float, duration: float, out: Path):
    """
    Cleaning chain:
      1. highpass=80Hz          — remove room rumble / handling noise
      2. lowpass=12000Hz        — remove hiss above 12kHz
      3. afftdn=nf=-30          — FFT-based noise reduction (stationary noise)
      4. anlmdn                 — non-local means denoising (removes burst noise)
      5. acompressor            — gentle dynamic normalisation
      6. loudnorm               — EBU R128, target -16 LUFS (broadcast standard)
      Output: mono 24kHz WAV (Qwen3-TTS native format)
    """
    trim_args = ["-ss", str(start), "-t", str(duration)] if duration > 0 else []

    filter_chain = (
        "highpass=f=80,"
        "lowpass=f=12000,"
        "afftdn=nf=-30,"
        "anlmdn=s=7:p=0.002:r=0.002:m=15,"
        "acompressor=threshold=-20dB:ratio=3:attack=5:release=50:makeup=2dB,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )

    cmd = (
        ["ffmpeg", "-y"]
        + (["-ss", str(start)] if duration > 0 else [])
        + ["-i", str(src)]
        + (["-t", str(duration)] if duration > 0 else [])
        + [
            "-af", filter_chain,
            "-ar", "24000",
            "-ac", "1",          # mono
            "-sample_fmt", "s16",
            str(out),
        ]
    )

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg error:")
        print(result.stderr[-2000:])
        raise RuntimeError("Cleaning failed")


def main():
    parser = argparse.ArgumentParser(description="Clean voice sample for TTS cloning")
    parser.add_argument("input", help="Path to raw voice recording")
    parser.add_argument("--start", type=float, default=0.5,
                        help="Start time in seconds (skip first 0.5s of breath/silence)")
    parser.add_argument("--full", action="store_true",
                        help="Keep entire file instead of trimming to 8s")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_dur = probe_duration(src)
    print(f"\nInput:    {src.name}  ({total_dur:.1f}s)")

    if args.full:
        start, duration = 0.0, 0.0
        print("Mode:     full file (no trim)")
    else:
        start = args.start
        available = total_dur - start
        duration = min(CLIP_DURATION, available)
        if duration < 3.0:
            print(f"WARNING: only {duration:.1f}s available after start={start}s — need at least 3s")
            duration = available
        print(f"Mode:     clip  start={start}s  duration={duration:.1f}s")

    print(f"Output:   {OUT_REF}")
    print("Cleaning...")

    clean(src, start, duration, OUT_REF)

    # also write a copy named for easy playback check
    import shutil
    shutil.copy2(OUT_REF, OUT_PREV)

    out_dur = probe_duration(OUT_REF)
    size_kb = OUT_REF.stat().st_size // 1024
    print(f"\nDone: {out_dur:.1f}s, {size_kb} KB -> {OUT_REF}")
    print()
    print("Next steps:")
    print("  1. Listen to ref_preview.wav -- should sound clear and clean")
    print("  2. Note exactly what you said in the clip (you'll need the transcript)")
    print("  3. Run generate_voiceover.py and choose [4] Voice Clone (Colab)")
    print()
    print("Tip: for best cloning quality, use 5-10s of natural speech")
    print("     (not reading slowly -- speak at your normal video pace)")


if __name__ == "__main__":
    main()
