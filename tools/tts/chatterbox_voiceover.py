"""
chatterbox_voiceover.py — Generate voiceover using Chatterbox TTS (free, MIT)
Best open-source voice cloning. Beats ElevenLabs in 63.75% of blind tests.
Requires CUDA GPU (8GB+ VRAM recommended).

Install: pip install chatterbox-tts torch torchaudio
Usage:   python tools/tts/chatterbox_voiceover.py --phase 4 --reference voice.wav
"""

import argparse
import sys
import time
import re
from pathlib import Path

try:
    import torch
    from chatterbox.tts import ChatterboxTTS
    import torchaudio
except ImportError:
    print("[ERROR] Chatterbox not installed. Run: pip install chatterbox-tts torch torchaudio")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"


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


def generate_voiceover(project: str, phase: int, reference_wav: str = None,
                       exaggeration: float = 0.5, cfg_weight: float = 0.5) -> Path:

    if not torch.cuda.is_available():
        print("[WARN] CUDA not found. Chatterbox will be slow on CPU.")
        print("       For CPU-only, use kokoro_voiceover.py instead.")

    script_path = PROJECT_ROOT / project / f"phase_{phase}" / "script.md"
    out_dir = PROJECT_ROOT / project / f"phase_{phase}" / "voiceover"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"phase_{phase:02d}_chatterbox.wav"

    print("Loading Chatterbox model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)

    paragraphs = extract_spoken_text(script_path)
    print(f"  {len(paragraphs)} paragraphs | exaggeration={exaggeration} | device={device}")

    all_audio = []
    sr = model.sr
    silence = torch.zeros(1, int(0.5 * sr))

    start = time.time()
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
        try:
            kwargs = {
                "text": para,
                "exaggeration": exaggeration,
                "cfg_weight": cfg_weight,
            }
            if reference_wav and Path(reference_wav).exists():
                kwargs["audio_prompt_path"] = reference_wav

            wav = model.generate(**kwargs)
            all_audio.append(wav)
            all_audio.append(silence)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(paragraphs)}")

        except Exception as e:
            print(f"  [WARN] Paragraph {i+1} failed: {e}")

    if not all_audio:
        print("[ERROR] No audio generated")
        sys.exit(1)

    combined = torch.cat(all_audio, dim=1)
    torchaudio.save(str(out_path), combined, sr)

    duration_min = combined.shape[1] / sr / 60
    elapsed = time.time() - start
    print(f"\nOutput: {out_path}")
    print(f"Duration: {duration_min:.1f} min | Generated in {elapsed:.0f}s ({duration_min*60/elapsed:.1f}x real-time)")
    print("Note: Chatterbox embeds an imperceptible Perth watermark for provenance.")

    return out_path


def main():
    parser = argparse.ArgumentParser(description="Chatterbox TTS voiceover generator")
    parser.add_argument("--project", default="chain_clarity")
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--reference", help="Path to 5–10 second WAV reference clip for voice cloning")
    parser.add_argument("--exaggeration", type=float, default=0.5,
                        help="Emotion exaggeration (0.25=subtle, 0.5=default, 0.75=expressive)")
    parser.add_argument("--cfg_weight", type=float, default=0.5,
                        help="CFG weight (0=more creative, 1=more faithful to reference)")
    args = parser.parse_args()

    if args.reference:
        print(f"Voice cloning from: {args.reference}")
    else:
        print("No reference clip provided — using default voice")

    generate_voiceover(args.project, args.phase, args.reference,
                       args.exaggeration, args.cfg_weight)


if __name__ == "__main__":
    main()
