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

# ── Recommended voices ───────────────────────────────────────────────────────
# South Asian / Nepali male  (best match for bold Asian male narrator)
SOUTH_ASIAN_MALE = [
    ("en-IN-PrabhatNeural",  "en-IN Male  — Indian English, bold professional narrator ⭐"),
    ("ne-NP-SagarNeural",    "ne-NP Male  — Native Nepali male voice (for Nepali scripts)"),
    ("hi-IN-MadhurNeural",   "hi-IN Male  — Hindi male narrator (for Hindi scripts)"),
]

# All recommended voices
RECOMMENDED_VOICES = [
    ("en-IN-PrabhatNeural",  "IN Male  ⭐ — Indian English, bold male narrator (default)"),
    ("ne-NP-SagarNeural",    "NP Male     — Native Nepali male (for Nepali scripts)"),
    ("hi-IN-MadhurNeural",   "IN Male     — Hindi male narrator (for Hindi scripts)"),
    ("en-US-GuyNeural",      "US Male     — professional American narrator"),
    ("en-GB-RyanNeural",     "UK Male     — deep documentary-style male"),
    ("en-US-JennyNeural",    "US Female   — warm, clear, education-style"),
    ("en-GB-SoniaNeural",    "UK Female   — polished, authoritative"),
    ("en-AU-NatashaNeural",  "AUS Female  — friendly, conversational"),
]

# Default: Indian English male — bold, professional, 30-35 age range
DEFAULT_VOICE = "en-IN-PrabhatNeural"


def extract_from_srt(srt_path: Path) -> tuple:
    """Parse subtitles.srt and return (full_text, segments_list).

    Returns:
        full_text  : single string with all subtitle lines joined — fed to TTS
        segments   : list of {'index': int, 'ts': str, 'text': str}
                     shown in the dashboard "Input Segments" preview
    """
    raw = srt_path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r'\n{2,}', raw.strip())
    segments, text_lines = [], []

    for block in blocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if not lines:
            continue
        # First line: index (integer)
        idx_line = lines[0]
        if not idx_line.isdigit():
            continue
        idx = int(idx_line)
        # Second line: timestamp
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        ts = lines[1]
        # Remaining lines: subtitle text
        subtitle_text = " ".join(lines[2:])
        if not subtitle_text:
            continue
        segments.append({"index": idx, "ts": ts, "text": subtitle_text})
        text_lines.append(subtitle_text)

    full_text = " ".join(text_lines)
    return full_text, segments


def extract_spoken_text(script_path: Path) -> str:
    """Extract all NARRATION:/SPOKEN: sections from script.md as one string."""
    text = script_path.read_text(encoding="utf-8")
    lines_out, in_spoken = [], False
    for line in text.split("\n"):
        s = line.strip()
        if re.match(r'^(?:\*{0,2})(NARRATION|SPOKEN)(?:\*{0,2})\s*:', s, re.IGNORECASE):
            in_spoken = True
            remainder = re.sub(r'^(?:\*{0,2})[A-Z]+(?:\*{0,2})\s*:\s*', '', s, flags=re.IGNORECASE)
            remainder = remainder.strip(" *")
            if remainder and len(remainder) > 10:
                lines_out.append(remainder)
            continue
        if re.match(r'^#{1,4}\s', s) or s.startswith("[") or \
                s.startswith("ON-SCREEN") or (s.startswith("**") and ":" in s):
            in_spoken = False
            continue
        if in_spoken and s and not s.startswith("**"):
            lines_out.append(s)
    result = " ".join(lines_out)
    if not result.strip():
        cleaned = re.sub(r'\[.*?\]|\*\*.*?\*\*|`.*?`|#{1,6}\s.*', '', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        result = cleaned[:8000]
    return result


def pick_source(phase_dir: Path, source_flag: str) -> tuple:
    """Choose input source and return (text, segments, source_label).

    source_flag: 'auto' | 'srt' | 'script'
    auto → prefer subtitles.srt if it exists and has content, else script.md
    """
    srt_path    = phase_dir / "subtitles.srt"
    script_path = phase_dir / "script.md"

    use_srt = (
        source_flag == "srt"
        or (source_flag == "auto" and srt_path.exists())
    )

    if use_srt and srt_path.exists():
        text, segments = extract_from_srt(srt_path)
        if text.strip():
            return text, segments, f"subtitles.srt ({len(segments)} segments)"

    # Fallback to script.md
    if not script_path.exists():
        return "", [], "none"
    text = extract_spoken_text(script_path)
    return text, [], f"script.md (NARRATION blocks)"


async def _synthesize(text: str, voice: str, out_path: Path):
    """Async core: stream TTS and write to file."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def synthesize(text: str, voice: str, out_path: Path):
    asyncio.run(_synthesize(text, voice, out_path))


async def _list_voices():
    voices = await edge_tts.list_voices()
    # Show South Asian + all English voices
    sa_locales = {"en-IN", "ne-NP", "hi-IN", "en-SG", "en-PH"}
    sa_voices  = [v for v in voices if v["Locale"] in sa_locales]
    en_voices  = [v for v in voices if v["Locale"].startswith("en-")]

    print(f"\n{'='*65}")
    print("  ⭐ South Asian / Nepali / Hindi Male Voices (recommended)")
    print(f"{'='*65}")
    for v in sorted(sa_voices, key=lambda x: x["Locale"]):
        marker = " ← DEFAULT" if v["ShortName"] == DEFAULT_VOICE else ""
        print(f"  {v['ShortName']:<40} {v['Gender']:<8} {v['Locale']}{marker}")

    print(f"\n{'='*65}")
    print("  All English voices available (edge-tts)")
    print(f"{'='*65}")
    for v in sorted(en_voices, key=lambda x: x["Locale"]):
        print(f"  {v['ShortName']:<40} {v['Gender']:<8} {v['Locale']}")
    print(f"\nTotal English voices: {len(en_voices)}")
    print(f"\nUsage: --voice en-IN-PrabhatNeural")


def main():
    parser = argparse.ArgumentParser(
        description="Generate voiceover with Microsoft Edge TTS (free, no API key)"
    )
    parser.add_argument("--project",     required=True)
    parser.add_argument("--phase",       type=int, default=0)
    parser.add_argument("--voice",       default=DEFAULT_VOICE,
                        help=f"Voice name (default: {DEFAULT_VOICE}). Use --list-voices to see all.")
    parser.add_argument("--source",      default="auto",
                        choices=["auto", "srt", "script"],
                        help="Input source: auto (default—prefer subtitles.srt), srt, or script")
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

    phase_dir = PROJECT_ROOT / args.project / f"phase_{args.phase}"

    print(f"\n{'='*58}")
    print(f"  Edge TTS Voiceover — {args.project}  Phase {args.phase}")
    print(f"  Voice : {args.voice}")
    print(f"  Source: {args.source}")
    print(f"{'='*58}\n")

    print("[1/3] Selecting input source...")
    text, segments, source_label = pick_source(phase_dir, args.source)

    if not text.strip():
        print(f"[ERROR] No text found. Expected:")
        print(f"  subtitles.srt : {phase_dir / 'subtitles.srt'}")
        print(f"  script.md     : {phase_dir / 'script.md'}")
        sys.exit(1)

    word_count = len(text.split())
    print(f"       Source    : {source_label}")
    print(f"       Words     : {word_count}")
    if segments:
        print(f"       Segments  : {len(segments)}")
        # Preview first 5 segments
        print(f"\n       Input segments (first 5 of {len(segments)}):")
        for seg in segments[:5]:
            preview = seg['text'][:70] + ('…' if len(seg['text']) > 70 else '')
            print(f"         [{seg['index']:03d}] {seg['ts'][:20]}  {preview}")
        if len(segments) > 5:
            print(f"         … and {len(segments)-5} more segments")
    print()

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
    print("\n━━ South Asian / male voices to try ━━━━━━━━━━━━━━━━━━━")
    for name, note in SOUTH_ASIAN_MALE:
        if name != args.voice:
            print(f"  python tools/tts/edge_tts_voiceover.py "
                  f"--project {args.project} --phase {args.phase} --voice {name}")
            print(f"    # {note}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
