"""
elevenlabs_voiceover.py — Generate voiceover using ElevenLabs (paid, industry standard)
Lowest latency, best multilingual quality, voice cloning on Creator+ plan.

Install: pip install elevenlabs
Usage:   python tools/tts/elevenlabs_voiceover.py --phase 4 --voice_id YOUR_ID
         ELEVENLABS_API_KEY=... python tools/tts/elevenlabs_voiceover.py --phase 4
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
except ImportError:
    print("[ERROR] ElevenLabs not installed. Run: pip install elevenlabs")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"

# Default voice — good for educational blockchain content
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam — clear, authoritative

# Model options
MODELS = {
    "flash":   "eleven_flash_v2_5",   # 75ms latency, lowest cost
    "turbo":   "eleven_turbo_v2_5",   # balanced
    "v3":      "eleven_multilingual_v2",  # best quality, multilingual
}


def extract_spoken_text(script_path: Path) -> list[str]:
    text = script_path.read_text(encoding="utf-8")
    paragraphs = []
    in_spoken = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.upper().startswith("SPOKEN"):
            in_spoken = True
            continue
        if stripped.startswith("[") or stripped.startswith("ON-SCREEN") or \
           re.match(r'^#{1,4}\s', stripped):
            in_spoken = False
            continue
        if in_spoken and stripped:
            paragraphs.append(stripped)
    return paragraphs


def generate_voiceover(project: str, phase: int, voice_id: str = DEFAULT_VOICE_ID,
                       model_key: str = "turbo") -> Path:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("[ERROR] ELEVENLABS_API_KEY not set. Export it before running.")
        sys.exit(1)

    script_path = PROJECT_ROOT / project / f"phase_{phase}" / "script.md"
    out_dir = PROJECT_ROOT / project / f"phase_{phase}" / "voiceover"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"phase_{phase:02d}_elevenlabs.mp3"

    client = ElevenLabs(api_key=api_key)
    model_id = MODELS.get(model_key, MODELS["turbo"])

    paragraphs = extract_spoken_text(script_path)
    total_chars = sum(len(p) for p in paragraphs)
    print(f"Voice ID: {voice_id} | Model: {model_id}")
    print(f"Total chars: {total_chars:,} | Estimated cost: ${total_chars * 0.00003:.3f}")

    voice_settings = VoiceSettings(
        stability=0.65,          # 0=varied, 1=stable
        similarity_boost=0.80,   # voice fidelity
        style=0.25,              # expressiveness
        use_speaker_boost=True,
    )

    # Generate full script as one request (better prosody than paragraph-by-paragraph)
    full_text = "\n\n".join(paragraphs)

    print("Generating audio...")
    start = time.time()
    audio_gen = client.text_to_speech.convert(
        text=full_text,
        voice_id=voice_id,
        model_id=model_id,
        voice_settings=voice_settings,
        output_format="mp3_44100_128",
    )

    with open(out_path, "wb") as f:
        for chunk in audio_gen:
            if chunk:
                f.write(chunk)

    elapsed = time.time() - start
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\nOutput: {out_path} ({size_mb:.1f} MB)")
    print(f"Generated in {elapsed:.1f}s")

    return out_path


def list_voices(api_key: str):
    client = ElevenLabs(api_key=api_key)
    voices = client.voices.get_all()
    print("\nAvailable voices:")
    for v in voices.voices[:20]:
        print(f"  {v.voice_id}: {v.name} — {v.labels}")


def main():
    parser = argparse.ArgumentParser(description="ElevenLabs voiceover generator")
    parser.add_argument("--project", default="chain_clarity")
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--voice_id", default=DEFAULT_VOICE_ID)
    parser.add_argument("--model", default="turbo", choices=["flash", "turbo", "v3"])
    parser.add_argument("--list_voices", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("[ERROR] ELEVENLABS_API_KEY not set")
        sys.exit(1)

    if args.list_voices:
        list_voices(api_key)
        return

    generate_voiceover(args.project, args.phase, args.voice_id, args.model)


if __name__ == "__main__":
    main()
