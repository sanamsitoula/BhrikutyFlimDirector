#!/usr/bin/env python3
"""
install.py — One-time global setup for Bhrikuty Film Director
=============================================================
Run ONCE after cloning. Installs all Python packages, sets up
Node.js (Remotion), and verifies system tools (ffmpeg, psql).

Everything installed here is global and shared across ALL brands,
projects, and phases — you never need to re-install per project.

Usage:
    python install.py              # Install everything
    python install.py --check      # Check what is/isn't installed
    python install.py --tts        # Install TTS engines only
    python install.py --node       # Set up Remotion (Node.js) only
    python install.py --db         # Apply DB schema only
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
PY = sys.executable

# ── colour-free status markers ────────────────────────────────────────────────
OK   = "[OK]  "
WARN = "[WARN]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
INFO = "[INFO]"

def banner(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def run_pip(packages: list, label: str, extra_flags: list = None) -> bool:
    """Install packages via pip. Returns True on success."""
    flags = ["--only-binary", ":all:", "--quiet"] + (extra_flags or [])
    cmd = [PY, "-m", "pip", "install"] + flags + packages
    print(f"  Installing {label}...", end=" ", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print("done")
        return True
    # Retry without --only-binary (allows source builds)
    cmd2 = [PY, "-m", "pip", "install", "--quiet"] + (extra_flags or []) + packages
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    if r2.returncode == 0:
        print("done (built from source)")
        return True
    print(f"FAILED\n    {r2.stderr.strip()[-200:]}")
    return False

def check_import(module: str) -> bool:
    r = subprocess.run([PY, "-c", f"import {module}"], capture_output=True)
    return r.returncode == 0

def check_cmd(cmd: str) -> bool:
    try:
        r = subprocess.run([cmd, "--version"], capture_output=True)
        return r.returncode == 0
    except (FileNotFoundError, OSError):
        return False

def pip_version(package: str) -> str:
    r = subprocess.run([PY, "-m", "pip", "show", package], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return ""


# ═════════════════════════════════════════════════════════════════════════════
# Package groups
# ═════════════════════════════════════════════════════════════════════════════

def install_core():
    banner("Core packages (required)")

    # numpy — try pre-built wheel first; kokoro / soundfile need it
    if check_import("numpy"):
        print(f"  {OK} numpy already installed ({pip_version('numpy')})")
    else:
        run_pip(["numpy>=2.0"], "numpy (pre-built wheel)", [])

    pkgs = {
        "anthropic>=0.40.0":     ("anthropic",   "Anthropic Claude SDK (primary AI)"),
        "google-genai>=0.8.0":   ("google.genai","Google Gemini SDK (fallback AI)"),
        "psycopg2-binary>=2.9":  ("psycopg2",    "PostgreSQL driver"),
    }
    for pkg, (module, label) in pkgs.items():
        if check_import(module):
            print(f"  {OK} {label} already installed")
        else:
            run_pip([pkg], label)


def install_tts():
    banner("TTS / Voiceover engines (pick at least one)")

    engines = [
        {
            "name": "Kokoro (free, CPU) — NOTE: requires Python <=3.12 on Windows",
            "packages": ["kokoro", "soundfile"],
            "check_module": "kokoro",
            "extra_flags": ["--no-build-isolation"],
            "skip_if": sys.version_info >= (3, 13) and sys.platform == "win32",
            "skip_msg": "Kokoro requires Python <=3.12 on Windows (build tools unavailable). Use ElevenLabs or DashScope instead.",
        },
        {
            "name": "ElevenLabs (paid, best quality)",
            "packages": ["elevenlabs"],
            "check_module": "elevenlabs",
        },
        {
            "name": "DashScope / Qwen3-TTS (freemium)",
            "packages": ["dashscope"],
            "check_module": "dashscope",
        },
    ]

    any_tts = False
    for e in engines:
        if e.get("skip_if"):
            print(f"  {SKIP} {e['name']}")
            print(f"        {e.get('skip_msg','')}")
            continue
        if check_import(e["check_module"]):
            print(f"  {OK} {e['name']} already installed")
            any_tts = True
        else:
            ok = run_pip(e["packages"], e["name"], e.get("extra_flags"))
            if ok:
                any_tts = True

    # Chatterbox needs torch — only attempt if GPU is available
    if check_import("chatterbox"):
        print(f"  {OK} Chatterbox (free, GPU) already installed")
        any_tts = True
    else:
        print(f"  {SKIP} Chatterbox (free, GPU) — install manually if you have 8GB VRAM:")
        print(f"        pip install chatterbox-tts torch torchaudio")

    if not any_tts:
        print(f"\n  {WARN} No TTS engine installed. Kokoro is recommended:")
        print(f"        pip install kokoro soundfile")
    return any_tts


def install_video():
    banner("Video tools (optional)")

    pkgs = {
        "moviepy":        ("moviepy",        "MoviePy — video compositing"),
        "faster-whisper": ("faster_whisper", "Faster-Whisper — auto transcription"),
    }
    for pkg, (module, label) in pkgs.items():
        if check_import(module):
            print(f"  {OK} {label} already installed")
        else:
            run_pip([pkg], label)


def setup_remotion():
    banner("Remotion — infographic card renderer (Node.js)")

    remotion_dir = BASE_DIR / "remotion"
    pkg_json = remotion_dir / "package.json"

    if not pkg_json.exists():
        print(f"  {SKIP} remotion/package.json not found — skipping")
        return False

    node_modules = remotion_dir / "node_modules"
    if node_modules.exists():
        print(f"  {OK} Remotion node_modules already installed")
        return True

    # Find npm
    npm_candidates = ["npm", "npm.cmd"]
    npm_cmd = None
    for c in npm_candidates:
        if check_cmd(c):
            npm_cmd = c
            break

    if not npm_cmd:
        print(f"  {FAIL} npm not found — install Node.js 18+ from nodejs.org")
        return False

    print(f"  Installing Remotion dependencies (npm install)...")
    r = subprocess.run([npm_cmd, "install"], cwd=str(remotion_dir), capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  {OK} Remotion installed successfully")
        return True
    else:
        print(f"  {FAIL} npm install failed:\n{r.stderr[-300:]}")
        return False


def apply_db_schema():
    banner("PostgreSQL — apply schema")

    # Load .env
    env_path = BASE_DIR / ".env"
    cfg = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                cfg[k.strip()] = v.strip()

    host = cfg.get("DB_HOST", "localhost")
    port = cfg.get("DB_PORT", "5432")
    name = cfg.get("DB_NAME", "bhrikutyflimdirector")
    user = cfg.get("DB_USER", "postgres")
    pw   = cfg.get("DB_PASSWORD", "")

    schema = BASE_DIR / "db" / "schema.sql"
    if not schema.exists():
        print(f"  {FAIL} db/schema.sql not found")
        return False

    # Find psql
    psql_candidates = [
        "psql",
        r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"/usr/bin/psql",
        r"/usr/local/bin/psql",
    ]
    psql = None
    for c in psql_candidates:
        try:
            r = subprocess.run([c, "--version"], capture_output=True)
            if r.returncode == 0:
                psql = c
                break
        except FileNotFoundError:
            continue

    if not psql:
        print(f"  {FAIL} psql not found. Add PostgreSQL bin/ to PATH or install PostgreSQL.")
        print(f"        Windows: C:\\Program Files\\PostgreSQL\\17\\bin\\psql.exe")
        return False

    env = os.environ.copy()
    env["PGPASSWORD"] = pw

    # Create DB if it doesn't exist
    create_cmd = [psql, "-U", user, "-h", host, "-p", port,
                  "-c", f"CREATE DATABASE {name};", "postgres"]
    r = subprocess.run(create_cmd, capture_output=True, text=True, env=env)
    if r.returncode == 0:
        print(f"  {OK} Database '{name}' created")
    elif "already exists" in r.stderr:
        print(f"  {OK} Database '{name}' already exists")
    else:
        print(f"  {WARN} Could not create DB: {r.stderr.strip()[:120]}")

    # Apply schema
    schema_cmd = [psql, "-U", user, "-h", host, "-p", port,
                  "-d", name, "-f", str(schema)]
    r = subprocess.run(schema_cmd, capture_output=True, text=True, env=env)
    if r.returncode == 0:
        print(f"  {OK} Schema applied to '{name}'")
        return True
    else:
        print(f"  {FAIL} Schema apply failed: {r.stderr.strip()[:200]}")
        return False


def check_system_tools():
    banner("System tools check")

    # ffmpeg
    if check_cmd("ffmpeg"):
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        ver = r.stdout.split("\n")[0] if r.stdout else "unknown"
        print(f"  {OK} ffmpeg: {ver[:60]}")
    else:
        # Try common install paths on Windows
        candidates = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\ffmpeg-2026-06-01-git-bf608f16fd-essentials_build\bin\ffmpeg.exe",
        ]
        found = next((c for c in candidates if Path(c).exists()), None)
        if found:
            # Add to PATH for this session
            bin_dir = str(Path(found).parent)
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
            subprocess.run(
                [sys.executable, "-c",
                 f"import subprocess; subprocess.run(['setx','PATH',r'{bin_dir};%PATH%'])"],
                capture_output=True
            )
            print(f"  {OK} ffmpeg found at {found} (added to PATH)")
        else:
            print(f"  {FAIL} ffmpeg not found")
            print(f"        Windows: winget install ffmpeg")
            print(f"        Mac:     brew install ffmpeg")

    # Node.js
    if check_cmd("node"):
        r = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"  {OK} Node.js: {r.stdout.strip()}")
    else:
        print(f"  {FAIL} Node.js not found — install from nodejs.org (needed for Remotion)")

    # psql
    psql_found = False
    for c in ["psql", r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
              r"C:\Program Files\PostgreSQL\15\bin\psql.exe"]:
        try:
            r = subprocess.run([c, "--version"], capture_output=True, text=True)
            if r.returncode == 0:
                print(f"  {OK} PostgreSQL: {r.stdout.strip()}")
                psql_found = True
                break
        except FileNotFoundError:
            continue
    if not psql_found:
        print(f"  {WARN} psql not found in PATH (DB features disabled)")
        print(f"        Add to PATH: C:\\Program Files\\PostgreSQL\\17\\bin")


def check_status():
    banner("Installation status")

    items = [
        ("anthropic",    "Claude SDK (primary AI)"),
        ("google.genai", "Gemini SDK (fallback AI)"),
        ("psycopg2",     "PostgreSQL driver"),
        ("numpy",        "NumPy"),
        ("kokoro",       "Kokoro TTS (free)"),
        ("elevenlabs",   "ElevenLabs TTS (paid)"),
        ("dashscope",    "DashScope / Qwen3 TTS"),
        ("chatterbox",   "Chatterbox TTS (GPU)"),
        ("moviepy",      "MoviePy (video)"),
        ("faster_whisper","Faster-Whisper (transcription)"),
    ]
    for module, label in items:
        if check_import(module):
            print(f"  {OK} {label}")
        else:
            print(f"  {SKIP} {label}")

    print()
    check_system_tools()

    remotion_ok = (BASE_DIR / "remotion" / "node_modules").exists()
    print(f"  {'[OK] ' if remotion_ok else '[SKIP]'} Remotion node_modules")

    # .env keys
    print()
    banner(".env API keys")
    env_path = BASE_DIR / ".env"
    keys = ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "ELEVENLABS_API_KEY",
            "DASHSCOPE_API_KEY", "DB_HOST"]
    if env_path.exists():
        cfg = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                cfg[k.strip()] = v.strip()
        for k in keys:
            val = cfg.get(k, "")
            if val:
                masked = val[:6] + "..." if len(val) > 6 else "set"
                print(f"  {OK} {k} = {masked}")
            else:
                print(f"  {SKIP} {k} not set")
    else:
        print(f"  {FAIL} .env file not found — copy .env.example to .env")


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Bhrikuty Film Director — global setup")
    parser.add_argument("--check",  action="store_true", help="Show installation status only")
    parser.add_argument("--core",   action="store_true", help="Install core Python packages only")
    parser.add_argument("--tts",    action="store_true", help="Install TTS engines only")
    parser.add_argument("--video",  action="store_true", help="Install video tools only")
    parser.add_argument("--node",   action="store_true", help="Set up Remotion (Node.js) only")
    parser.add_argument("--db",     action="store_true", help="Apply DB schema only")
    args = parser.parse_args()

    print(f"\nBhrikuty Film Director — Global Setup")
    print(f"Python: {sys.version.split()[0]}  |  {PY}")
    print(f"Project: {BASE_DIR}\n")

    if args.check:
        check_status()
        return

    specific = args.core or args.tts or args.video or args.node or args.db

    if not specific or args.core:
        install_core()

    if not specific or args.tts:
        install_tts()

    if not specific or args.video:
        install_video()

    if not specific or args.node:
        setup_remotion()

    if not specific or args.db:
        apply_db_schema()

    if not specific:
        check_system_tools()

    banner("Setup complete")
    print("  Run 'python install.py --check' anytime to see what's installed.")
    print("  Start the dashboard: python server.py")
    print("  Run a pipeline:      python pipeline.py --project ecoWorld --phase 1 --topic \"...\"")
    print()


if __name__ == "__main__":
    main()
