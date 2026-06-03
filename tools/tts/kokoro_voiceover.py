"""
kokoro_voiceover.py — Generate voiceover using Kokoro-TTS (free, CPU-capable)
#1 on TTS Arena leaderboard. Apache 2.0 license. No GPU required.

Install: pip install kokoro soundfile
Usage:   python tools/tts/kokoro_voiceover.py --phase 4 --voice af_heart
"""

import argparse
import re
import sys
import time
from pathlib import Path

try:
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np
except ImportError:
    print("[ERROR] Kokoro not installed. Run: pip install kokoro soundfile")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"

VOICES = {
    "af_heart":   "American Female — warm, clear, educational (recommended)",
    "af_bella":   "American Female — expressive, dynamic",
    "am_adam":    "American Male — authoritative, clear",
    "am_michael": "American Male — calm, measured",
    "bf_emma":    "British Female — professional",
    "bm_george":  "British Male — formal",
}


def extract_spoken_text(script_path: Path) -> list[str]:
    """Extract SPOKEN sections from script.md, return as list of paragraphs."""
    text = script_path.read_text(encoding="utf-8")
    paragraphs = []
    in_spoken = False

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.upper().startswith("SPOKEN"):
            in_spoken = True
            continue
        if stripped.startswith("[") or stripped.startswith("ON-SCREEN") or \
           re.match(r'^#{1,4}\s', stripped) or stripped.startswith("**"):
            in_spoken = False
            continue
        if in_spoken and stripped:
            paragraphs.append(stripped)

    return paragraphs


def generate_voiceover(project: str, phase: int, voice: str = "af_heart",
                       speed: float = 1.0, lang: str = "en-us") -> Path:
    script_path = PROJECT_ROOT / project / f"phase_{phase}" / "script.md"
    if not script_path.exists():
        print(f"[ERROR] script.md not found: {script_path}")
        sys.exit(1)

    out_dir = PROJECT_ROOT / project / f"phase_{phase}" / "voiceover"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"phase_{phase:02d}_kokoro.wav"

    print(f"Voice: {voice} — {VOICES.get(voice, 'custom')}")
    print(f"Extracting spoken text from {script_path.name}...")

    paragraphs = extract_spoken_text(script_path)
    print(f"  {len(paragraphs)} spoken paragraphs found")

    print("Loading Kokoro pipeline...")
    pipeline = KPipeline(lang_code=lang)

    all_audio = []
    silence_500ms = np.zeros(int(0.5 * 24000), dtype=np.float32)
    silence_300ms = np.zeros(int(0.3 * 24000), dtype=np.float32)

    start = time.time()
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
        try:
            generator = pipeline(para, voice=voice, speed=speed)
            for _, _, audio in generator:
                all_audio.append(audio)
            # Add natural pause between paragraphs
            all_audio.append(silence_500ms)
        except Exception as e:
            print(f"  [WARN] Paragraph {i+1} failed: {e}")
            all_audio.append(silence_300ms)

    if not all_audio:
        print("[ERROR] No audio generated")
        sys.exit(1)

    combined = np.concatenate(all_audio)
    sf.write(str(out_path), combined, samplerate=24000)

    duration_min = len(combined) / 24000 / 60
    elapsed = time.time() - start
    print(f"\nOutput: {out_path}")
    print(f"Duration: {duration_min:.1f} min | Generated in {elapsed:.0f}s ({duration_min*60/elapsed:.1f}x real-time)")

    return out_path


def main():
    print("\nAvailable voices:")
    for k, v in VOICES.items():
        print(f"  {k}: {v}")
    print()

    parser = argparse.ArgumentParser(description="Kokoro-TTS voiceover generator")
    parser.add_argument("--project", default="chain_clarity")
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--voice", default="af_heart", choices=list(VOICES.keys()))
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed (0.5–2.0)")
    parser.add_argument("--lang", default="en-us")
    args = parser.parse_args()

    generate_voiceover(args.project, args.phase, args.voice, args.speed, args.lang)


if __name__ == "__main__":
    main()
