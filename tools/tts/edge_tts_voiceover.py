"""
edge_tts_voiceover.py — Generate voiceover using Microsoft Edge TTS (free, no API key)
========================================================================================
Uses Microsoft's neural TTS voices (same as Edge browser's "Read Aloud").
300+ high-quality voices. No GPU, no API key, works on Python 3.14+.

Install: pip install edge-tts
Usage:
  python tools/tts/edge_tts_voiceover.py --project ecoWorld --phase 1
  python tools/tts/edge_tts_voiceover.py --project ecoWorld --phase 1 --voice en-US-AriaNeural
  python tools/tts/edge_tts_voiceover.py --list-voices   (show all English voices)
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

import io as _io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import edge_tts
except ImportError:
    print("[ERROR] edge-tts not installed.")
    print("  Install with: pip install edge-tts")
    print()
    print("  edge-tts is free, uses Microsoft's neural voices,")
    print("  no API key needed, works on Python 3.14+")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"

# High-quality English voices — pick your preference
RECOMMENDED_VOICES = [
    ("en-US-JennyNeural",   "US Female   — warm, clear, great for education"),
    ("en-US-GuyNeural",     "US Male     — professional, calm narrator"),
    ("en-US-AriaNeural",    "US Female   — expressive, natural"),
    ("en-GB-SoniaNeural",   "UK Female   — polished, authoritative"),
    ("en-GB-RyanNeural",    "UK Male     — deep, documentary-style"),
    ("en-AU-NatashaNeural", "AUS Female  — friendly, conversational"),
]
DEFAULT_VOICE = "en-US-JennyNeural"


def extract_spoken_text(script_path: Path) -> str:
    """Extract all NARRATION:/SPOKEN: sections from script.md as one string."""
    text = script_path.read_text(encoding="utf-8")
    lines_out, in_spoken = [], False
    for line in text.split("\n"):
        s = line.strip()
        if re.match(r'^(NARRATION|SPOKEN)\s*:', s, re.IGNORECASE):
            in_spoken = True
            remainder = re.sub(r'^(NARRATION|SPOKEN)\s*:\s*', '', s, flags=re.IGNORECASE)
            if remainder:
                lines_out.append(remainder)
            continue
        if re.match(r'^#{1,4}\s', s) or s.startswith("[") or \
                s.startswith("ON-SCREEN") or (s.startswith("**") and ":" in s):
            in_spoken = False
            continue
        if in_spoken and s:
            lines_out.append(s)
    result = " ".join(lines_out)
    if not result.strip():
        # Fallback: strip all markdown and use everything
        cleaned = re.sub(r'\[.*?\]|\*\*.*?\*\*|`.*?`|#{1,6}\s.*', '', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        result = cleaned[:5000]
    return result


async def _synthesize(text: str, voice: str, out_path: Path):
    """Async core: stream TTS and write to file."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def synthesize(text: str, voice: str, out_path: Path):
    asyncio.run(_synthesize(text, voice, out_path))


async def _list_voices():
    voices = await edge_tts.list_voices()
    en_voices = [v for v in voices if v["Locale"].startswith("en-")]
    print(f"\n{'='*65}")
    print("  English voices available (edge-tts)")
    print(f"{'='*65}")
    for v in sorted(en_voices, key=lambda x: x["Locale"]):
        print(f"  {v['ShortName']:<35} {v['Gender']:<7} {v['Locale']}")
    print(f"\nTotal English voices: {len(en_voices)}")
    print("\nUsage: --voice en-US-JennyNeural")


def main():
    parser = argparse.ArgumentParser(
        description="Generate voiceover with Microsoft Edge TTS (free, no API key)"
    )
    parser.add_argument("--project",     default="chain_clarity")
    parser.add_argument("--phase",       type=int, default=0)
    parser.add_argument("--voice",       default=DEFAULT_VOICE,
                        help=f"Voice name (default: {DEFAULT_VOICE}). Use --list-voices to see all.")
    parser.add_argument("--output",      default="",
                        help="Output filename (default: phase_N.mp3)")
    parser.add_argument("--list-voices", action="store_true",
                        help="List all available English voices and exit")
    args = parser.parse_args()

    if args.list_voices:
        asyncio.run(_list_voices())
        print("\nRecommended voices:")
        for name, note in RECOMMENDED_VOICES:
            print(f"  {name:<35} {note}")
        return

    if not args.phase:
        print("[ERROR] --phase is required")
        sys.exit(1)

    phase_dir   = PROJECT_ROOT / args.project / f"phase_{args.phase}"
    script_path = phase_dir / "script.md"

    if not script_path.exists():
        print(f"[ERROR] script.md not found: {script_path}")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  Edge TTS Voiceover — {args.project} Phase {args.phase}")
    print(f"  Voice: {args.voice}")
    print(f"{'='*55}\n")

    print("[1/3] Extracting spoken text from script.md...")
    text = extract_spoken_text(script_path)
    word_count = len(text.split())
    print(f"       {word_count} words extracted\n")

    vo_dir   = phase_dir / "voiceover"
    vo_dir.mkdir(parents=True, exist_ok=True)
    out_name = args.output or f"phase_{args.phase}.mp3"
    out_path = vo_dir / out_name

    print(f"[2/3] Synthesizing with {args.voice}...")
    print("      (Microsoft Edge neural TTS — streaming...)\n")
    synthesize(text, args.voice, out_path)

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"[3/3] Saved: {out_path}")
    print(f"      Size:  {size_mb:.2f} MB")
    print(f"      URL:   http://localhost:8080/media/{args.project}/{args.phase}/voiceover/{out_name}")
    print(f"\n[DONE] Listen in dashboard:")
    print(f"  http://localhost:8080/phase/{args.project}/{args.phase}  -> Audio tab")
    print()
    print("Other voices to try:")
    for name, note in RECOMMENDED_VOICES[:4]:
        if name != args.voice:
            print(f"  python tools/tts/edge_tts_voiceover.py "
                  f"--project {args.project} --phase {args.phase} --voice {name}")
            print(f"    # {note}")


if __name__ == "__main__":
    main()
