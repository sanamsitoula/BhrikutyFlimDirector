"""
dashscope_voiceover.py — Generate voiceover using DashScope Qwen-TTS
=====================================================================
Works with both standard and workspace (sk-ws-*) API keys.
Uses the native DashScope speech-synthesis endpoint.

Usage:
  python tools/tts/dashscope_voiceover.py --project ecoWorld --phase 1
  python tools/tts/dashscope_voiceover.py --project ecoWorld --phase 1 --voice longxiaochun
  python tools/tts/dashscope_voiceover.py --project ecoWorld --phase 1 --chunk-size 200

Requires: pip install requests
Keys in .env:
  DASHSCOPE_API_KEY      primary workspace key
  DASHSCOPE_API_URL      workspace DashScope endpoint  (e.g. https://ws-xxx.ap-southeast-1.maas.aliyuncs.com/api/v1)
  DASHSCOPE_API_KEY_2    secondary key (auto-fallback)
  DASHSCOPE_BASE_URL_2   secondary workspace endpoint
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load .env
_env = Path(__file__).parent.parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

try:
    import requests
except ImportError:
    print("[ERROR] requests not installed: pip install requests")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"

# Default English voice — clear, neutral narrator style
DEFAULT_VOICE = "longxiaochun"
# Model — cosyvoice-v1 for multilingual, sambert-zhichu-v1 for Chinese
DEFAULT_MODEL = "cosyvoice-v1"


# ── API credentials (primary + secondary) ─────────────────────────────────────
def _get_configs():
    """Return list of (api_key, api_url) to try in order."""
    configs = []
    k1  = os.environ.get("DASHSCOPE_API_KEY", "")
    u1  = os.environ.get("DASHSCOPE_API_URL",
          "https://dashscope.aliyuncs.com/api/v1")        # default non-workspace
    k2  = os.environ.get("DASHSCOPE_API_KEY_2", "")
    u2  = os.environ.get("DASHSCOPE_BASE_URL_2", u1).replace(
          "/compatible-mode/v1", "/api/v1")               # strip OpenAI compat path
    if k1 and "PASTE" not in k1: configs.append((k1, u1, "primary"))
    if k2 and "PASTE" not in k2: configs.append((k2, u2, "secondary"))
    return configs


# ── Text extraction ────────────────────────────────────────────────────────────
def extract_spoken_text(script_path: Path) -> list[str]:
    """Extract NARRATION: / SPOKEN: paragraphs from script.md."""
    text = script_path.read_text(encoding="utf-8")
    paragraphs, in_spoken = [], False
    for line in text.split("\n"):
        s = line.strip()
        if re.match(r'^(NARRATION|SPOKEN)\s*:', s, re.IGNORECASE):
            in_spoken = True
            # Capture same-line text after the colon
            remainder = re.sub(r'^(NARRATION|SPOKEN)\s*:\s*', '', s, flags=re.IGNORECASE)
            if remainder:
                paragraphs.append(remainder)
            continue
        if re.match(r'^#{1,4}\s', s) or s.startswith("[") or s.startswith("ON-SCREEN") \
                or s.startswith("**") and ":" in s:
            in_spoken = False
            continue
        if in_spoken and s:
            paragraphs.append(s)
    return paragraphs


def chunk_text(paragraphs: list[str], max_chars: int = 300) -> list[str]:
    """Split into chunks small enough for the TTS API (max ~500 chars per call)."""
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
            current = p
        else:
            current = current + " " + p if current else p
    if current:
        chunks.append(current.strip())
    return chunks


# ── TTS API call ──────────────────────────────────────────────────────────────
def synthesize_chunk(text: str, api_key: str, api_url: str,
                     voice: str, model: str) -> bytes:
    """Call DashScope speech-synthesis API. Returns raw audio bytes (mp3)."""
    url = api_url.rstrip("/") + "/services/aigc/text-2-speech/text-synthesis"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": model,
        "input": {"text": text},
        "parameters": {
            "voice":        voice,
            "format":       "mp3",
            "sample_rate":  44100,
            "volume":       50,
            "speech_rate":  0,   # 0 = normal speed
            "pitch_rate":   0,
        },
    }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if r.status_code == 200:
        return r.content
    raise RuntimeError(f"TTS API {r.status_code}: {r.text[:300]}")


def synthesize_with_fallback(text: str, voice: str, model: str) -> bytes:
    """Try primary key, then secondary key automatically."""
    configs = _get_configs()
    if not configs:
        raise RuntimeError(
            "No DashScope API key found.\n"
            "Add DASHSCOPE_API_KEY and DASHSCOPE_API_URL to .env"
        )
    last_err = None
    for key, url, label in configs:
        try:
            data = synthesize_chunk(text, key, url, voice, model)
            if label != "primary":
                print(f"    [OK] {label} succeeded")
            return data
        except Exception as e:
            print(f"    [WARN] DashScope {label} failed: {str(e)[:80]}"
                  + (" — trying secondary..." if configs.index((key, url, label)) < len(configs)-1 else ""))
            last_err = e
    raise last_err


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate voiceover with DashScope Qwen-TTS")
    parser.add_argument("--project",    default="chain_clarity")
    parser.add_argument("--phase",      type=int, required=True)
    parser.add_argument("--voice",      default=DEFAULT_VOICE,
                        help=f"Voice ID (default: {DEFAULT_VOICE}). "
                             "English: longxiaochun, longyuan. Chinese: zhitian, zhiya")
    parser.add_argument("--model",      default=DEFAULT_MODEL,
                        help=f"Model (default: {DEFAULT_MODEL}). "
                             "Options: cosyvoice-v1, sambert-zhichu-v1")
    parser.add_argument("--chunk-size", type=int, default=300,
                        help="Max chars per TTS chunk (default: 300)")
    parser.add_argument("--output",     default="",
                        help="Output filename (default: phase_N.mp3)")
    args = parser.parse_args()

    phase_dir = PROJECT_ROOT / args.project / f"phase_{args.phase}"
    script_path = phase_dir / "script.md"

    if not script_path.exists():
        print(f"[ERROR] script.md not found: {script_path}")
        print("  Generate it first: python tools/generate_phase.py --project "
              f"{args.project} --phase {args.phase} --topic '...' --only script.md")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  DashScope Voiceover — {args.project} Phase {args.phase}")
    print(f"  Voice: {args.voice}   Model: {args.model}")
    print(f"{'='*55}\n")

    print("[1/3] Extracting spoken text from script.md...")
    paragraphs = extract_spoken_text(script_path)
    if not paragraphs:
        print("[WARN] No NARRATION:/SPOKEN: sections found in script.md")
        print("       Falling back to full script text (first 3000 chars)...")
        paragraphs = [script_path.read_text(encoding="utf-8")[:3000]]

    chunks = chunk_text(paragraphs, max_chars=args.chunk_size)
    total_chars = sum(len(c) for c in chunks)
    print(f"       {len(paragraphs)} paragraphs → {len(chunks)} chunks · {total_chars:,} chars total\n")

    print(f"[2/3] Synthesizing {len(chunks)} chunk(s) via DashScope TTS...")
    audio_parts = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}/{len(chunks)} ({len(chunk)} chars): {chunk[:60]}...")
        for attempt in range(3):
            try:
                audio_data = synthesize_with_fallback(chunk, args.voice, args.model)
                audio_parts.append(audio_data)
                print(f"    -> {len(audio_data):,} bytes")
                break
            except Exception as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    print(f"    [RETRY] {str(e)[:80]} — waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"    [FAIL] Could not synthesize chunk {i}: {e}")
                    raise

    print(f"\n[3/3] Saving audio file...")
    vo_dir = phase_dir / "voiceover"
    vo_dir.mkdir(parents=True, exist_ok=True)

    out_name = args.output or f"phase_{args.phase}.mp3"
    out_path = vo_dir / out_name

    # Concatenate raw MP3 bytes (works for sequential chunks)
    combined = b"".join(audio_parts)
    out_path.write_bytes(combined)

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"  [OK] Saved: {out_path}")
    print(f"       Size:  {size_mb:.2f} MB")
    print(f"       URL:   http://localhost:8080/media/{args.project}/{args.phase}/voiceover/{out_name}")

    print(f"\n[DONE] Voiceover ready.")
    print(f"  Listen in dashboard: http://localhost:8080/phase/{args.project}/{args.phase} -> Audio tab")


if __name__ == "__main__":
    main()
