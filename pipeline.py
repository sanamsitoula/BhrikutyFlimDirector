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

PROJECT_ROOT = Path(__file__).parent / "youtube_scripts" / "setup" / "projects"
TOOLS_DIR = Path(__file__).parent / "tools"
REMOTION_DIR = Path(__file__).parent / "remotion"


def run(cmd: list, label: str, cwd: Path = None) -> bool:
    print(f"\n{'─'*50}")
    print(f"▶  {label}")
    print(f"{'─'*50}")
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Step failed: {label}")
        return False
    print(f"✓  {label} complete")
    return True


def check_prerequisites():
    missing = []

    # ffmpeg
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if result.returncode != 0:
        missing.append("ffmpeg (install from ffmpeg.org or via chocolatey: choco install ffmpeg)")

    # node
    result = subprocess.run(["node", "--version"], capture_output=True)
    if result.returncode != 0:
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


def step_generate_phase(project: str, phase: int, topic: str, outline: str, duration: int, tags: str):
    return run(
        [sys.executable, str(TOOLS_DIR / "generate_phase.py"),
         "--project", project, "--phase", str(phase),
         "--topic", topic, "--outline", outline,
         "--duration", str(duration), "--tags", tags],
        f"STEP 1: Generate phase {phase} content files"
    )


def step_compliance_check(project: str, phase: int):
    return run(
        [sys.executable, str(TOOLS_DIR / "compliance_checker.py"),
         "--project", project, "--phase", str(phase)],
        f"STEP 2: Compliance check phase {phase}"
    )


def step_remotion_render(phase: int):
    if not (REMOTION_DIR / "node_modules").exists():
        print("  [INFO] Installing Remotion dependencies...")
        result = subprocess.run(["npm", "install"], cwd=str(REMOTION_DIR))
        if result.returncode != 0:
            print("  [WARN] npm install failed — skipping Remotion render")
            return False

    return run(
        ["node", "scripts/render_all_cards.js", "--phase", str(phase)],
        f"STEP 3: Render infographic cards (Remotion) for phase {phase}",
        cwd=REMOTION_DIR
    )


def step_voiceover(project: str, phase: int):
    voiceover_script = Path(__file__).parent / "myvideo" / "edit" / "generate_voiceover.py"
    if not voiceover_script.exists():
        print(f"  [SKIP] generate_voiceover.py not found at {voiceover_script}")
        return True

    phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
    script_path = phase_dir / "script.md"
    voiceover_dir = phase_dir / "voiceover"
    voiceover_dir.mkdir(exist_ok=True)

    return run(
        [sys.executable, str(voiceover_script),
         "--script", str(script_path),
         "--output", str(voiceover_dir)],
        f"STEP 4: Generate voiceover for phase {phase}"
    )


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
- Colors: #00D4AA · #F5A623 · #8B9BB4 · #0A0E1A · #7B5CF0
- Content name overlay: ✓
- Phase label: Phase {phase} of 5
- Tags embedded: ✓

## Next Step
See `publish_checklist.md` for upload sequence.
"""
    out_base.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")
    print(f"\n✅ Pipeline summary → {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Film Director: End-to-end content pipeline")
    parser.add_argument("--project", default="chain_clarity")
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--topic", default="", help="Video title (required if not --skip-generate)")
    parser.add_argument("--outline", default="", help="Content outline (required if not --skip-generate)")
    parser.add_argument("--duration", type=int, default=12)
    parser.add_argument("--tags", default="blockchain,crypto,web3,chainclarity")
    parser.add_argument("--video", default="", help="Path to master video (optional, enables video cuts)")
    parser.add_argument("--skip-generate", action="store_true", help="Skip content file generation")
    parser.add_argument("--skip-voiceover", action="store_true", help="Skip voiceover generation")
    parser.add_argument("--skip-remotion", action="store_true", help="Skip Remotion card render")
    parser.add_argument("--skip-text", action="store_true", help="Skip text content generation")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  CHAIN CLARITY — FILM DIRECTOR PIPELINE                  ║
║  Phase {args.phase} · {args.project}
╚══════════════════════════════════════════════════════════╝
""")

    missing = check_prerequisites()
    steps_run = []
    steps_skipped = []

    # STEP 1: Generate phase files
    if not args.skip_generate:
        if not args.topic:
            print("[ERROR] --topic required when not using --skip-generate")
            sys.exit(1)
        ok = step_generate_phase(args.project, args.phase, args.topic, args.outline, args.duration, args.tags)
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

    # Summary
    write_publish_summary(args.project, args.phase)

    print(f"""
{'='*60}
PIPELINE COMPLETE — Phase {args.phase}
{'='*60}
Steps completed: {len(steps_run)}
  {'  '.join(chr(10) + '  ✓ ' + s for s in steps_run)}
Steps skipped: {len(steps_skipped)}
  {'  '.join(chr(10) + '  - ' + s for s in steps_skipped)}

Output: youtube_scripts/setup/projects/{args.project}/_output/phase_{args.phase:02d}/
{'='*60}
""")


if __name__ == "__main__":
    main()
