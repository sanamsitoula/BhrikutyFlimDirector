"""
core/config.py — the ONE .env loader for this repo.

This replaces the byte-identical ~6-line loader previously copy-pasted in
server.py, pipeline.py, and tools/generate_phase.py (see B2V2Docs/architecture.md
§2 / CP1). New callers should import load_dotenv() from here rather than adding
a fourth copy.

Behavior matches the original copies exactly: reads .env from the repo root
(one level above this file), skips blank lines and lines starting with "#",
splits on the first "=", and uses os.environ.setdefault() so a real
environment variable already set (e.g. by the shell or CI) always wins over
the .env file's value.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(env_path: Path = None) -> None:
    """Load key=value pairs from .env into os.environ (existing env vars win)."""
    path = env_path or (REPO_ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def any_llm_provider_configured() -> bool:
    """True if at least one LLM provider (Anthropic/Gemini/Qwen-DashScope) is
    configured. Mirrors tools/generate_phase.py's own fallback check — use
    this instead of gating any step on one specific provider's env var
    (see B2V2Docs/architecture.md CP10 / historical bug E10)."""
    return bool(
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("DASHSCOPE_API_KEY")
        or os.environ.get("DASHSCOPE_API_KEY_2")
    )
