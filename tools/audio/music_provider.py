"""
music_provider.py — Free-tier MusicProvider: closes the "music_brief.md is
generated and never consumed" gap (see B2V2Docs/architecture.md, AUDIOVIS /
MusicProvider; B2V2Docs/roadmap.md Phase 1, item 7).

Fetches/uses a royalty-free track matching the already-generated
music_brief.md's mood/search terms, trims/loops it to the phase's voiceover
duration, and applies a loop-safe fade-in/out — producing an actual audio
file where today there is none.

TWO tiers, both supported side by side (per B2V2Docs/coding-rules.md's
"extend, never silently replace" rule — see that file for why this exists):

  Tier A — MANUAL (Pixabay or any other source you download yourself).
    Pixabay's own catalog is a real, good free-music source, but Pixabay's
    PUBLIC API (https://pixabay.com/api/docs/) only documents Images/Videos
    search — there is no programmatic Music/Audio search endpoint to call.
    So: download a track from https://pixabay.com/music/ (or any source you
    have rights to) yourself, drop the file into
    youtube_scripts/setup/projects/{project}/phase_{N}/music/manual/, and
    this script uses it automatically — no API call, no key needed. This
    tier is checked FIRST and always wins if a file is present.

  Tier B — AUTOMATED (Jamendo, https://developer.jamendo.com/v3.0/docs).
    A real, documented, free tracks-search API — used only when no manual
    file is present in music/manual/. Requires JAMENDO_CLIENT_ID.

Usage:
  python tools/audio/music_provider.py --project ecoWorld --phase 1
  JAMENDO_CLIENT_ID=... python tools/audio/music_provider.py --project X --phase N

Requires: ffmpeg on PATH (for trim/loop/fade — same hard dependency the rest
          of the pipeline already has). JAMENDO_CLIENT_ID is only needed if
          you are not supplying a manual file (Tier A above).

Exits 0 (skip, not fail) if neither tier has anything usable, music_brief.md
is missing, or ffmpeg is unavailable — matches the existing TTS-step pattern
in pipeline.py of degrading gracefully rather than failing the whole run.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.config import load_dotenv

load_dotenv()
import os  # noqa: E402  (after load_dotenv so os.environ is populated first)

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"

JAMENDO_API = "https://api.jamendo.com/v3.0/tracks/"
DEFAULT_TARGET_DURATION_S = 60.0
FADE_IN_S = 2.0
FADE_OUT_S = 3.0


def extract_search_terms(brief_text: str) -> list[str]:
    """Pull royalty-free search-term phrases out of the freeform
    music_brief.md markdown. generate_phase.py's music-brief prompt
    consistently renders each search term as its own backtick-quoted bullet
    (e.g. "- `cinematic tech tension lo-fi`") — that's a much more reliable
    signal than trying to delimit a "search terms" section by heading text,
    since the brief has one such section per script segment. Falls back to
    mood words, then a generic default, if no backtick bullets are found at
    all (e.g. a differently-formatted or hand-edited brief)."""
    terms = [m.strip() for m in re.findall(r"^-\s*`([^`]+)`", brief_text, re.MULTILINE)]
    terms = list(dict.fromkeys(terms))  # dedupe, preserve order
    if not terms:
        m2 = re.search(r"(?im)^.*mood.*$([\s\S]{0,300})", brief_text)
        if m2:
            terms = re.findall(r"[a-zA-Z]{4,}", m2.group(1))[:5]
    return terms[:8] or ["cinematic", "corporate", "inspiring"]


def find_target_duration(phase_dir: Path) -> float:
    """Determine how long the background track should be. Priority order:
    1. An existing voiceover file's REAL measured duration (ffprobe) — this is
       the actual media duration and always wins when it exists, since it's
       the true length the music needs to sit under.
    2. content_spec.json's `duration_min` — generated in Step 1 (topic+outline
       -> planning docs), before any audio/video exists, so it's available
       even when voiceover hasn't been generated yet (e.g. --skip-voiceover,
       or this step running before Step 4). Far better than a fixed guess.
    3. A fixed constant, only if neither of the above is available at all."""
    vo_dir = phase_dir / "voiceover"
    if vo_dir.exists():
        audio_files = sorted(
            [p for p in vo_dir.glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg")]
        )
        if audio_files:
            duration = _probe_duration_s(audio_files[0])
            if duration is not None:
                return duration

    spec_path = phase_dir / "content_spec.json"
    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            duration_min = spec.get("duration_min")
            if duration_min:
                return float(duration_min) * 60.0
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    return DEFAULT_TARGET_DURATION_S


def _probe_duration_s(audio_path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.SubprocessError):
        return None


AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")


def find_manual_source(phase_dir: Path) -> Path:
    """Tier A: an operator-supplied track (e.g. downloaded by hand from
    Pixabay Music, or any other source) dropped into phase_N/music/manual/.
    Returns the first audio file found, or None. Checked before any
    automated/API tier — see module docstring."""
    manual_dir = phase_dir / "music" / "manual"
    if not manual_dir.exists():
        return None
    candidates = sorted(p for p in manual_dir.glob("*") if p.suffix.lower() in AUDIO_EXTS)
    return candidates[0] if candidates else None


def search_jamendo_track(client_id: str, terms: list[str]) -> dict:
    query = urllib.parse.urlencode({
        "client_id": client_id,
        "format": "json",
        "limit": "5",
        "search": " ".join(terms),
        "audioformat": "mp32",
        "include": "musicinfo",
        "order": "relevance",
    })
    url = f"{JAMENDO_API}?{query}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.load(resp)
    results = data.get("results", [])
    downloadable = [t for t in results if t.get("audiodownload_allowed") and t.get("audio")]
    return (downloadable or results or [{}])[0]


def build_background_track(raw_path: Path, out_path: Path, target_duration_s: float) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("  [SKIP] ffmpeg not found — cannot trim/loop/fade the fetched track")
        return False

    fade_out_start = max(target_duration_s - FADE_OUT_S, 0)
    filter_chain = (
        f"afade=t=in:st=0:d={FADE_IN_S},"
        f"afade=t=out:st={fade_out_start}:d={FADE_OUT_S}"
    )
    cmd = [
        ffmpeg, "-y",
        "-stream_loop", "-1", "-i", str(raw_path),
        "-t", str(target_duration_s),
        "-af", filter_chain,
        "-ac", "2", "-b:a", "192k",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] ffmpeg failed to build background track:\n{result.stderr[-800:]}")
        return False
    return True


def run(project: str, phase: int) -> bool:
    phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
    brief_path = phase_dir / "music_brief.md"

    if not brief_path.exists():
        print(f"  [SKIP] No music_brief.md found at {brief_path} — run Step 1 (generate) first")
        return True

    music_dir = phase_dir / "music"
    music_dir.mkdir(exist_ok=True)
    out_path = music_dir / "background_music.mp3"
    manifest_path = music_dir / "music_manifest.json"
    target_duration = find_target_duration(phase_dir)

    # ── Tier A: manual/operator-supplied file (e.g. downloaded from Pixabay) ──
    manual_source = find_manual_source(phase_dir)
    if manual_source is not None:
        print(f"  [INFO] Using manually-supplied track: {manual_source.name}")
        ok = build_background_track(manual_source, out_path, target_duration)
        if not ok:
            return True
        manifest = {
            "provider": "manual",
            "tier": "manual (operator-supplied, e.g. Pixabay)",
            "source_file": manual_source.name,
            "target_duration_s": target_duration,
            "output_file": str(out_path),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"  [OK] Background music -> {out_path}")
        print(f"       Source: {manual_source.name} (manual tier)")
        return True

    # ── Tier B: automated fetch (Jamendo) ──
    client_id = os.environ.get("JAMENDO_CLIENT_ID", "")
    if not client_id:
        print("  [SKIP] No manual track in phase_N/music/manual/, and JAMENDO_CLIENT_ID not set")
        print("         Either drop a downloaded track (e.g. from pixabay.com/music/) into")
        print(f"         {music_dir / 'manual'}")
        print("         or register a free Jamendo client_id at https://developer.jamendo.com/")
        return True

    terms = extract_search_terms(brief_path.read_text(encoding="utf-8"))
    print(f"  [INFO] Searching Jamendo for: {', '.join(terms)}")

    try:
        track = search_jamendo_track(client_id, terms)
    except Exception as e:
        print(f"  [SKIP] Jamendo search failed ({e}) — continuing without background music")
        return True

    audio_url = track.get("audio")
    if not audio_url:
        print("  [SKIP] No matching Jamendo track found for this brief's search terms")
        return True

    raw_path = music_dir / "track_raw.mp3"
    try:
        urllib.request.urlretrieve(audio_url, raw_path)
    except Exception as e:
        print(f"  [SKIP] Failed to download track ({e})")
        return True

    ok = build_background_track(raw_path, out_path, target_duration)
    if not ok:
        return True  # degrade gracefully — raw track remains on disk for manual use

    manifest = {
        "provider": "jamendo",
        "tier": "automated (free)",
        "track_name": track.get("name"),
        "artist_name": track.get("artist_name"),
        "jamendo_track_id": track.get("id"),
        "jamendo_page_url": track.get("shareurl"),
        "license_ccurl": track.get("license_ccurl"),
        "search_terms_used": terms,
        "target_duration_s": target_duration,
        "output_file": str(out_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"  [OK] Background music -> {out_path}")
    print(f"       Track: {manifest['track_name']} by {manifest['artist_name']} (Jamendo, automated tier)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch free-tier background music matching music_brief.md")
    parser.add_argument("--project", required=True)
    parser.add_argument("--phase", type=int, required=True)
    args = parser.parse_args()
    ok = run(args.project, args.phase)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
