#!/usr/bin/env python3
"""
Bhrikuty Video Pipeline — Full Diagnostic Tool
Tests: FFmpeg, Remotion, Python deps, file paths, brand config, rendering
"""

import os
import sys
import json
import subprocess
import shutil
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ───────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
REQUIRED_PYTHON_DEPS = [
    "anthropic", "moviepy", "faster_whisper",
    "kokoro", "soundfile", "elevenlabs"
]
REQUIRED_NODE_MODULES = [
    "remotion", "@remotion/cli", "@remotion/renderer"
]
REQUIRED_FFMPEG_VERSION = 5  # minimum major version
REPORT_FILE = PROJECT_ROOT / "debug_report.md"

# ───────────────────────────────────────────────
# COLOR OUTPUT
# ───────────────────────────────────────────────
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

def ok(msg):   print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
def warn(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")
def fail(msg): print(f"{Colors.RED}❌ {msg}{Colors.END}")
def info(msg): print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")
def header(msg): print(f"\n{Colors.BOLD}{'='*60}\n{msg}\n{'='*60}{Colors.END}")

# ───────────────────────────────────────────────
# CHECK 1: SYSTEM ENVIRONMENT
# ───────────────────────────────────────────────
def check_system() -> Dict:
    header("CHECK 1: SYSTEM ENVIRONMENT")
    results = {}

    results['os'] = platform.system()
    results['os_version'] = platform.version()
    info(f"OS: {results['os']} {results['os_version']}")

    results['python'] = sys.version
    info(f"Python: {sys.version.split()[0]}")

    try:
        node = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        results['node'] = node.stdout.strip()
        ok(f"Node.js: {results['node']}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        results['node'] = None
        fail("Node.js not found in PATH")

    try:
        npm = subprocess.run(["npm", "--version"], capture_output=True, text=True, check=True)
        results['npm'] = npm.stdout.strip()
        ok(f"npm: {results['npm']}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        results['npm'] = None
        fail("npm not found in PATH")

    return results

# ───────────────────────────────────────────────
# CHECK 2: FFMPEG DEEP DIAGNOSTICS
# ───────────────────────────────────────────────
def check_ffmpeg() -> Dict:
    header("CHECK 2: FFMPEG DEEP DIAGNOSTICS")
    results = {'available': False, 'version': None, 'codecs': [], 'errors': []}

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        fail("FFmpeg binary not found in PATH")
        results['errors'].append("FFmpeg not in PATH")
        return results

    ok(f"FFmpeg found: {ffmpeg_path}")
    results['path'] = ffmpeg_path

    try:
        version_proc = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        version_line = version_proc.stdout.split('\n')[0]
        results['version'] = version_line
        info(f"Version: {version_line}")

        import re
        ver_match = re.search(r'version (\d+)\.', version_line)
        if ver_match:
            major = int(ver_match.group(1))
            results['major_version'] = major
            if major >= REQUIRED_FFMPEG_VERSION:
                ok(f"FFmpeg version {major} >= {REQUIRED_FFMPEG_VERSION} (OK)")
            else:
                fail(f"FFmpeg version {major} < {REQUIRED_FFMPEG_VERSION} (UPGRADE REQUIRED)")
                results['errors'].append(f"FFmpeg too old: {major}")
        else:
            warn("Could not parse FFmpeg version number")

    except Exception as e:
        fail(f"FFmpeg version check failed: {e}")
        results['errors'].append(str(e))
        return results

    results['available'] = True

    try:
        codecs_proc = subprocess.run(
            ["ffmpeg", "-codecs"],
            capture_output=True, text=True, timeout=10
        )
        codecs_output = codecs_proc.stdout

        required_codecs = ['libx264', 'aac', 'libopus', 'png']
        for codec in required_codecs:
            if codec in codecs_output:
                ok(f"Codec available: {codec}")
                results['codecs'].append(codec)
            else:
                warn(f"Codec missing: {codec}")
                results['errors'].append(f"Missing codec: {codec}")

    except Exception as e:
        fail(f"Codec check failed: {e}")
        results['errors'].append(str(e))

    test_dir = PROJECT_ROOT / "_debug_test"
    test_dir.mkdir(exist_ok=True)
    test_video = test_dir / "test_encode.mp4"

    try:
        encode_test = subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=30",
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            str(test_video)
        ], capture_output=True, text=True, timeout=15)

        if encode_test.returncode == 0 and test_video.exists():
            ok("FFmpeg test encode: SUCCESS")
            results['test_encode'] = True
            test_video.unlink()
        else:
            fail("FFmpeg test encode: FAILED")
            fail(f"stderr: {encode_test.stderr[:500]}")
            results['test_encode'] = False
            results['errors'].append(f"Test encode failed: {encode_test.stderr[:200]}")

    except Exception as e:
        fail(f"FFmpeg test encode exception: {e}")
        results['test_encode'] = False
        results['errors'].append(str(e))

    if test_dir.exists():
        shutil.rmtree(test_dir)

    return results

# ───────────────────────────────────────────────
# CHECK 3: PYTHON DEPENDENCIES
# ───────────────────────────────────────────────
def check_python_deps() -> Dict:
    header("CHECK 3: PYTHON DEPENDENCIES")
    results = {'installed': [], 'missing': [], 'versions': {}}

    for dep in REQUIRED_PYTHON_DEPS:
        try:
            module = __import__(dep.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            results['installed'].append(dep)
            results['versions'][dep] = version
            ok(f"{dep} == {version}")
        except ImportError:
            results['missing'].append(dep)
            fail(f"{dep} NOT INSTALLED")

    if 'moviepy' in results['installed']:
        try:
            import moviepy.config as mp_config
            if mp_config.IMAGEMAGICK_BINARY:
                info(f"MoviePy ImageMagick: {mp_config.IMAGEMAGICK_BINARY}")
            else:
                warn("MoviePy ImageMagick not configured")
        except Exception as e:
            warn(f"MoviePy config check failed: {e}")

    return results

# ───────────────────────────────────────────────
# CHECK 4: REMOTION ENVIRONMENT
# ───────────────────────────────────────────────
def check_remotion() -> Dict:
    header("CHECK 4: REMOTION ENVIRONMENT")
    results = {'remotion_dir': None, 'node_modules': False, 'cli_works': False, 'errors': []}

    remotion_dir = PROJECT_ROOT / "remotion"
    results['remotion_dir'] = str(remotion_dir)

    if not remotion_dir.exists():
        fail("remotion/ directory not found")
        results['errors'].append("Missing remotion/ directory")
        return results

    ok(f"remotion/ directory found: {remotion_dir}")

    node_modules = remotion_dir / "node_modules"
    if node_modules.exists():
        results['node_modules'] = True
        ok("node_modules/ exists")

        for pkg in REQUIRED_NODE_MODULES:
            pkg_path = node_modules / pkg
            if pkg_path.exists():
                ok(f"Package installed: {pkg}")
            else:
                warn(f"Package missing: {pkg}")
                results['errors'].append(f"Missing npm package: {pkg}")
    else:
        fail("node_modules/ missing — run: cd remotion && npm install")
        results['errors'].append("node_modules missing")

    config_file = remotion_dir / "remotion.config.ts"
    if config_file.exists():
        ok("remotion.config.ts found")
    else:
        warn("remotion.config.ts not found")

    try:
        cli_test = subprocess.run(
            ["node", "node_modules/.bin/remotion", "--version"],
            cwd=remotion_dir,
            capture_output=True, text=True, timeout=15
        )
        if cli_test.returncode == 0:
            results['cli_works'] = True
            ok(f"Remotion CLI works: v{cli_test.stdout.strip()}")
        else:
            fail(f"Remotion CLI failed: {cli_test.stderr[:300]}")
            results['errors'].append(f"CLI error: {cli_test.stderr[:200]}")
    except Exception as e:
        fail(f"Remotion CLI exception: {e}")
        results['errors'].append(str(e))

    return results

# ───────────────────────────────────────────────
# CHECK 5: PROJECT STRUCTURE & BRAND
# ───────────────────────────────────────────────
def check_project_structure(project: str = "chain_clarity") -> Dict:
    header(f"CHECK 5: PROJECT STRUCTURE ({project})")
    results = {'paths': {}, 'brand_exists': False, 'errors': []}

    paths = {
        'setup_dir':     PROJECT_ROOT / "youtube_scripts" / "setup" / "projects" / project,
        'brand_profile': PROJECT_ROOT / "youtube_scripts" / "setup" / "projects" / project / "brand_profile.json",
        'roadmap':       PROJECT_ROOT / "youtube_scripts" / "setup" / "projects" / project / "roadmap.json",
        'env':           PROJECT_ROOT / ".env",
        'remotion':      PROJECT_ROOT / "remotion",
    }

    for name, path in paths.items():
        exists = path.exists()
        results['paths'][name] = {'exists': exists, 'path': str(path)}
        if exists:
            ok(f"{name}: {path}")
        else:
            warn(f"{name}: NOT FOUND ({path})")

    brand_path = paths['brand_profile']
    if brand_path.exists():
        try:
            with open(brand_path) as f:
                brand = json.load(f)
            results['brand_exists'] = True
            ok("brand_profile.json is valid JSON")

            required = ['brand_name', 'slug', 'colors', 'fonts', 'tone']
            for field in required:
                if field in brand:
                    ok(f"Brand field: {field}")
                else:
                    warn(f"Brand missing field: {field}")
                    results['errors'].append(f"Missing brand field: {field}")

        except json.JSONDecodeError as e:
            fail(f"brand_profile.json is invalid JSON: {e}")
            results['errors'].append(f"Invalid JSON: {e}")
    else:
        results['errors'].append("No brand profile")

    env_path = paths['env']
    if env_path.exists():
        with open(env_path) as f:
            env_content = f.read()
        if 'ANTHROPIC_API_KEY' in env_content:
            ok("ANTHROPIC_API_KEY found in .env")
        else:
            warn("ANTHROPIC_API_KEY not found in .env")
    else:
        warn(".env file not found")

    return results

# ───────────────────────────────────────────────
# CHECK 6: RENDER PIPELINE TEST
# ───────────────────────────────────────────────
def test_render_pipeline(project: str = "chain_clarity", phase: int = 1) -> Dict:
    header(f"CHECK 6: RENDER PIPELINE TEST ({project}/phase_{phase})")
    results = {'phase_dir': None, 'infographics': [], 'can_render': False, 'errors': []}

    phase_dir = PROJECT_ROOT / "youtube_scripts" / "setup" / "projects" / project / f"phase_{phase}"
    results['phase_dir'] = str(phase_dir)

    if not phase_dir.exists():
        fail(f"Phase directory not found: {phase_dir}")
        results['errors'].append("Phase directory missing")
        return results

    ok(f"Phase directory: {phase_dir}")

    expected_files = [
        'script.md', 'script_short.md', 'voiceover_brief.md',
        'clip_brief.md', 'infographics.md', 'content_spec.json',
        'subtitles.srt', 'compliance_report_auto.md'
    ]

    for fname in expected_files:
        fpath = phase_dir / fname
        if fpath.exists():
            size = fpath.stat().st_size
            ok(f"{fname} ({size:,} bytes)")
        else:
            warn(f"{fname} missing")
            results['errors'].append(f"Missing: {fname}")

    assets_dir = phase_dir / "infographic_assets"
    if assets_dir.exists():
        html_files = list(assets_dir.glob("*.html"))
        results['infographics'] = [f.name for f in html_files]
        ok(f"Infographic assets: {len(html_files)} HTML files")
        for f in html_files:
            info(f"  - {f.name}")
    else:
        warn("infographic_assets/ directory missing")
        results['errors'].append("Missing infographic_assets")

    remotion_dir = PROJECT_ROOT / "remotion"
    if remotion_dir.exists() and (remotion_dir / "node_modules").exists():
        try:
            dry_run = subprocess.run(
                ["node", "node_modules/.bin/remotion", "bundle"],
                cwd=remotion_dir,
                capture_output=True, text=True, timeout=60
            )
            if dry_run.returncode == 0:
                ok("Remotion bundle: SUCCESS")
                results['can_render'] = True
            else:
                fail(f"Remotion bundle failed: {dry_run.stderr[:500]}")
                results['errors'].append(f"Bundle failed: {dry_run.stderr[:300]}")
        except Exception as e:
            fail(f"Remotion bundle exception: {e}")
            results['errors'].append(str(e))

    return results

# ───────────────────────────────────────────────
# CHECK 7: MOVIEPY VIDEO TEST
# ───────────────────────────────────────────────
def test_moviepy() -> Dict:
    header("CHECK 7: MOVIEPY VIDEO COMPOSITING TEST")
    results = {'success': False, 'output': None, 'errors': []}

    try:
        from moviepy.editor import ColorClip

        test_dir = PROJECT_ROOT / "_debug_test"
        test_dir.mkdir(exist_ok=True)
        output_path = test_dir / "moviepy_test.mp4"

        clip = ColorClip(size=(640, 480), color=(0, 255, 0), duration=2)
        clip.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            audio=False,
            verbose=False,
            logger=None
        )

        if output_path.exists():
            size = output_path.stat().st_size
            ok(f"MoviePy test render: SUCCESS ({size:,} bytes)")
            results['success'] = True
            results['output'] = str(output_path)
            output_path.unlink()

        if test_dir.exists():
            shutil.rmtree(test_dir)

    except ImportError:
        warn("moviepy not installed — skipping render test")
        results['errors'].append("moviepy not installed")
    except Exception as e:
        fail(f"MoviePy test failed: {e}")
        results['errors'].append(str(e))

    return results

# ───────────────────────────────────────────────
# REPORT GENERATION
# ───────────────────────────────────────────────
def generate_report(all_results: Dict):
    header("GENERATING DEBUG REPORT")

    lines = [
        "# Bhrikuty Pipeline Debug Report",
        f"Generated: {datetime.now().isoformat()}",
        f"Platform: {platform.system()} {platform.version()}",
        "",
        "## Summary",
        "",
    ]

    total_errors = sum(len(v.get('errors', [])) for v in all_results.values() if isinstance(v, dict))
    total_warnings = sum(len(v.get('missing', [])) for v in all_results.values() if isinstance(v, dict))

    lines.append(f"- **Errors Found:** {total_errors}")
    lines.append(f"- **Warnings:** {total_warnings}")
    lines.append(f"- **Status:** {'PASS' if total_errors == 0 else 'NEEDS ATTENTION'}")
    lines.append("")

    for section, data in all_results.items():
        lines.append(f"## {section}")
        lines.append("```json")
        lines.append(json.dumps(data, indent=2, default=str))
        lines.append("```")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")

    if not all_results.get('ffmpeg', {}).get('available'):
        lines.append("1. **Install FFmpeg:** `winget install --id Gyan.FFmpeg -e`")
    if not all_results.get('remotion', {}).get('node_modules'):
        lines.append("2. **Install Remotion deps:** `cd remotion && npm install`")
    missing_py = all_results.get('python_deps', {}).get('missing', [])
    if missing_py:
        lines.append(f"3. **Install Python packages:** `pip install {' '.join(missing_py)}`")

    report_text = "\n".join(lines)
    with open(REPORT_FILE, 'w') as f:
        f.write(report_text)

    ok(f"Report saved: {REPORT_FILE}")
    print(f"\n{Colors.BOLD}Quick Fix Commands:{Colors.END}")
    print(f"  pip install anthropic moviepy faster-whisper kokoro soundfile")
    print(f"  cd remotion && npm install")
    print(f"  winget install --id Gyan.FFmpeg -e  # Windows")

# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
def main():
    print(f"{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     BHRIKUTY VIDEO PIPELINE — FULL DIAGNOSTIC              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    all_results = {}
    all_results['system']      = check_system()
    all_results['ffmpeg']      = check_ffmpeg()
    all_results['python_deps'] = check_python_deps()
    all_results['remotion']    = check_remotion()
    all_results['project']     = check_project_structure()
    all_results['render']      = test_render_pipeline()
    all_results['moviepy']     = test_moviepy()

    generate_report(all_results)

    header("FINAL VERDICT")
    errors = sum(len(v.get('errors', [])) for v in all_results.values() if isinstance(v, dict))

    if errors == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED — Pipeline is ready!{Colors.END}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}FOUND {errors} ERROR(S) — Fix above before proceeding{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
