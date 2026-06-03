"""
pipeline.py — Film Director: End-to-end content production pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage (generate new phase from scratch):
  python pipeline.py \\
    --project chain_clarity \\
    --phase 6 \\
    --topic "NFTs and Digital Ownership" \\
    --outline "ERC-721 standard, real use cases, risks, resale royalties"

Usage (process existing phase — skip generation):
  python pipeline.py --project chain_clarity --phase 4 --skip-generate

Usage (only produce platform outputs):
  python pipeline.py --project chain_clarity --phase 4 --skip-generate --skip-voiceover --video path/to/final.mp4

Requires: ANTHROPIC_API_KEY  (for generate + text content steps)
          ffmpeg on PATH      (for platform cuts)
          Node.js             (for Remotion card renders)
"""

import subprocess
import sys
import os
import json
import argparse
import time
from pathlib import Path

# Load .env file if present
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

PROJECT_ROOT = Path(__file__).parent / "youtube_scripts" / "setup" / "projects"
TOOLS_DIR    = Path(__file__).parent / "tools"
REMOTION_DIR = Path(__file__).parent / "remotion"

# DB (optional)
try:
    from db.db import create_run, finish_run, update_phase_status, is_available as _db_ok
    _DB = True
except Exception:
    _DB = False
    def create_run(*_):          return False
    def finish_run(*_):          return False
    def update_phase_status(*_): return False
    def _db_ok():                return False


def run(cmd: list, label: str, cwd: Path = None) -> bool:
    print(f"\n{'-'*50}")
    print(f">>  {label}")
    print(f"{'-'*50}")
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Step failed: {label}")
        return False
    print(f"[OK]  {label} complete")
    return True


def check_prerequisites():
    missing = []

    # ffmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
        if result.returncode != 0:
            missing.append("ffmpeg (install from ffmpeg.org or via chocolatey: choco install ffmpeg)")
    except FileNotFoundError:
        missing.append("ffmpeg (install from ffmpeg.org or via chocolatey: choco install ffmpeg)")

    # node
    try:
        result = subprocess.run(["node", "--version"], capture_output=True)
        if result.returncode != 0:
            missing.append("Node.js (install from nodejs.org)")
    except FileNotFoundError:
        missing.append("Node.js (install from nodejs.org)")

    # anthropic
    try:
        import anthropic
    except ImportError:
        missing.append("anthropic (run: pip install anthropic)")

    if missing:
        print("[WARN] Some prerequisites missing:")
        for m in missing:
            print(f"  - {m}")
        print("Some pipeline steps will be skipped.\n")
    return missing


def step_generate_phase(project: str, phase: int, topic: str, outline: str, duration: int, tags: str, provider: str = "auto"):
    cmd = [sys.executable, str(TOOLS_DIR / "generate_phase.py"),
           "--project", project, "--phase", str(phase),
           "--topic", topic, "--outline", outline,
           "--duration", str(duration), "--tags", tags]
    if provider and provider != "auto":
        cmd += ["--provider", provider]
    return run(cmd, f"STEP 1: Generate phase {phase} content files")


def step_compliance_check(project: str, phase: int):
    return run(
        [sys.executable, str(TOOLS_DIR / "compliance_checker.py"),
         "--project", project, "--phase", str(phase)],
        f"STEP 2: Compliance check phase {phase}"
    )


def step_remotion_render(phase: int):
    if not (REMOTION_DIR / "node_modules").exists():
        print("  [INFO] Installing Remotion dependencies...")
        try:
            result = subprocess.run(["npm", "install"], cwd=str(REMOTION_DIR))
            if result.returncode != 0:
                print("  [WARN] npm install failed — skipping Remotion render")
                return False
        except FileNotFoundError:
            print("  [WARN] npm not found — skipping Remotion render (install Node.js to enable)")
            return False

    try:
        return run(
            ["node", "scripts/render_all_cards.js", "--phase", str(phase)],
            f"STEP 3: Render infographic cards (Remotion) for phase {phase}",
            cwd=REMOTION_DIR
        )
    except FileNotFoundError:
        print("  [WARN] node not found — skipping Remotion render")
        return False


def step_voiceover(project: str, phase: int):
    """Try TTS engines in priority order: Kokoro -> ElevenLabs -> DashScope -> skip."""
    tts_dir = TOOLS_DIR / "tts"
    phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
    voiceover_dir = phase_dir / "voiceover"
    voiceover_dir.mkdir(exist_ok=True)

    # Priority 1: Kokoro (free, CPU)
    kokoro = tts_dir / "kokoro_voiceover.py"
    try:
        import kokoro as _k  # noqa: F401
        if kokoro.exists():
            return run(
                [sys.executable, str(kokoro), "--phase", str(phase), "--project", project],
                f"STEP 4: Generate voiceover (Kokoro)"
            )
    except ImportError:
        pass

    # Priority 2: ElevenLabs (paid)
    el_script = tts_dir / "elevenlabs_voiceover.py"
    try:
        import elevenlabs as _el  # noqa: F401
        el_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if el_key and el_script.exists():
            return run(
                [sys.executable, str(el_script), "--phase", str(phase), "--project", project],
                f"STEP 4: Generate voiceover (ElevenLabs)"
            )
        elif not el_key:
            print("  [INFO] ElevenLabs installed but ELEVENLABS_API_KEY not set")
    except ImportError:
        pass

    # Priority 3: DashScope / Qwen3-TTS (freemium)
    ds_key = os.environ.get("DASHSCOPE_API_KEY", "")
    try:
        import dashscope as _ds  # noqa: F401
        if ds_key:
            print("  [INFO] DashScope TTS available — run manually:")
            print(f"         python tools/tts/dashscope_voiceover.py --phase {phase} --project {project}")
        else:
            print("  [INFO] DashScope installed but DASHSCOPE_API_KEY not set")
    except ImportError:
        pass

    print("  [SKIP] No TTS engine available. Options:")
    print("         pip install elevenlabs   (+ set ELEVENLABS_API_KEY in .env)")
    print("         pip install dashscope    (+ set DASHSCOPE_API_KEY in .env)")
    print("         Run with --skip-voiceover to bypass this step")
    return True


def step_text_content(project: str, phase: int):
    return run(
        [sys.executable, str(TOOLS_DIR / "text_content_generator.py"),
         "--project", project, "--phase", str(phase)],
        f"STEP 5: Generate text platform content for phase {phase}"
    )


def step_platform_cuts(project: str, phase: int, video_path: str = None):
    cmd = [sys.executable, str(TOOLS_DIR / "platform_cutter.py"),
           "--project", project, "--phase", str(phase)]
    if video_path:
        cmd += ["--video", video_path]
    return run(cmd, f"STEP 6: Export platform clips for phase {phase}")


def write_publish_summary(project: str, phase: int):
    out_base = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}"
    spec_path = PROJECT_ROOT / project / f"phase_{phase}" / "content_spec.json"

    title = f"Phase {phase}"
    if spec_path.exists():
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)
        title = spec.get("title", title)

    summary_path = out_base / "PIPELINE_SUMMARY.md"
    summary = f"""# Pipeline Complete — Phase {phase}
## {title}

**Run date:** {time.strftime('%Y-%m-%d %H:%M')}

## Output Files

### Master Content (Production Sources)
| File | Location |
|------|---------|
| script.md | phase_{phase}/script.md |
| script_short.md | phase_{phase}/script_short.md |
| subtitles.srt | phase_{phase}/subtitles.srt |
| infographic cards | phase_{phase}/infographic_assets/ |
| compliance report | phase_{phase}/compliance_report_auto.md |

### Platform Outputs
| Platform | Folder | Files |
|----------|--------|-------|
| YouTube | _output/phase_{phase:02d}/youtube/ | final_1080p.mp4, description.txt |
| TikTok | _output/phase_{phase:02d}/tiktok/ | clip_01_hook.mp4, clip_02_main.mp4 |
| Instagram | _output/phase_{phase:02d}/instagram/ | reel_60s.mp4, carousel_1-3.png |
| Twitter | _output/phase_{phase:02d}/twitter/ | card_clip.mp4, thread.txt |
| LinkedIn | _output/phase_{phase:02d}/linkedin/ | clip.mp4, article.md |
| Blog | _output/phase_{phase:02d}/blog/ | post.md |
| GitHub | _output/phase_{phase:02d}/github/ | README.md |

### Branding (all outputs verified)
- Colors: #00D4AA / #F5A623 / #8B9BB4 / #0A0E1A / #7B5CF0
- Content name overlay: YES
- Phase label: Phase {phase} of 5
- Tags embedded: YES

## Next Step
See `publish_checklist.md` for upload sequence.
"""
    out_base.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")
    print(f"\n[DONE] Pipeline summary -> {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Film Director: End-to-end content pipeline")
    parser.add_argument("--project", default="chain_clarity")
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--topic", default="", help="Video title (required if not --skip-generate)")
    parser.add_argument("--outline", default="", help="Content outline (required if not --skip-generate)")
    parser.add_argument("--duration", type=int, default=12)
    parser.add_argument("--tags", default="blockchain,crypto,web3,chainclarity")
    parser.add_argument("--video", default="", help="Path to master video (optional, enables video cuts)")
    parser.add_argument("--provider", choices=["auto","anthropic","gemini","openai","dashscope"],
                        default="auto", help="Script AI provider (default: auto = Anthropic then Gemini)")
    parser.add_argument("--skip-generate", action="store_true", help="Skip content file generation")
    parser.add_argument("--skip-voiceover", action="store_true", help="Skip voiceover generation")
    parser.add_argument("--skip-remotion", action="store_true", help="Skip Remotion card render")
    parser.add_argument("--skip-text", action="store_true", help="Skip text content generation")
    args = parser.parse_args()

    print(f"""
{'='*60}
  BHRIKUTY FILM DIRECTOR PIPELINE
  Phase {args.phase} / {args.project}
{'='*60}
""")

    import uuid
    run_id = uuid.uuid4().hex[:16]
    create_run(run_id, args.project, args.phase, vars(args))
    update_phase_status(args.project, args.phase, "in_progress")

    # Ensure phase directory exists
    phase_dir = PROJECT_ROOT / args.project / f"phase_{args.phase}"
    phase_dir.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / args.project / "_output" / f"phase_{args.phase:02d}").mkdir(parents=True, exist_ok=True)

    missing = check_prerequisites()
    steps_run = []
    steps_skipped = []

    # STEP 1: Generate phase files
    if not args.skip_generate:
        if not args.topic:
            print("[ERROR] --topic required when not using --skip-generate")
            sys.exit(1)
        ok = step_generate_phase(args.project, args.phase, args.topic, args.outline, args.duration, args.tags, args.provider)
        (steps_run if ok else steps_skipped).append("1: Generate content files")
    else:
        steps_skipped.append("1: Generate content files (--skip-generate)")

    # STEP 2: Compliance check
    ok = step_compliance_check(args.project, args.phase)
    (steps_run if ok else steps_skipped).append("2: Compliance check")

    # STEP 3: Remotion card render
    if not args.skip_remotion and "Node.js" not in str(missing):
        ok = step_remotion_render(args.phase)
        (steps_run if ok else steps_skipped).append("3: Remotion card render")
    else:
        steps_skipped.append("3: Remotion card render (--skip-remotion or Node.js missing)")

    # STEP 4: Voiceover
    if not args.skip_voiceover:
        ok = step_voiceover(args.project, args.phase)
        (steps_run if ok else steps_skipped).append("4: Voiceover generation")
    else:
        steps_skipped.append("4: Voiceover generation (--skip-voiceover)")

    # STEP 5: Text content
    if not args.skip_text and "ANTHROPIC_API_KEY" in os.environ:
        ok = step_text_content(args.project, args.phase)
        (steps_run if ok else steps_skipped).append("5: Text platform content")
    else:
        steps_skipped.append("5: Text content (--skip-text or ANTHROPIC_API_KEY not set)")

    # STEP 6: Platform cuts
    video = args.video if args.video else None
    ok = step_platform_cuts(args.project, args.phase, video)
    (steps_run if ok else steps_skipped).append("6: Platform cuts")

    # Summary + DB finalise
    write_publish_summary(args.project, args.phase)
    final_ok = len(steps_skipped) == 0 or len(steps_run) > 0
    finish_run(run_id, "done" if final_ok else "failed")
    update_phase_status(args.project, args.phase, "done" if final_ok else "partial")

    print(f"""
{'='*60}
PIPELINE COMPLETE — Phase {args.phase}
{'='*60}
Steps completed: {len(steps_run)}
  {'  '.join(chr(10) + '  [OK] ' + s for s in steps_run)}
Steps skipped: {len(steps_skipped)}
  {'  '.join(chr(10) + '  - ' + s for s in steps_skipped)}

Output: youtube_scripts/setup/projects/{args.project}/_output/phase_{args.phase:02d}/
{'='*60}
""")


if __name__ == "__main__":
    main()
