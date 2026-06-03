"""
db/sync.py - Sync all file-system data into PostgreSQL
=======================================================
Reads brand_profile.json, roadmap.json, content_spec.json,
compliance_log.json, and phase file lists, then upserts
everything into the DB.

Run manually:
    python db/sync.py                         (all brands)
    python db/sync.py --brand ecoWorld        (one brand)
    python db/sync.py --brand ecoWorld --verbose

Run automatically via API:
    POST /api/db-sync  { "brand": "ecoWorld" }
"""

import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load .env
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sync_brand(brand_slug: str, verbose: bool = False) -> dict:
    """Sync one brand's data (brand + all phases) from filesystem to DB."""
    from db.db import (
        upsert_brand, upsert_phase, upsert_content_spec,
        save_compliance, record_file, is_available
    )

    if not is_available():
        return {"ok": False, "error": "DB not available"}

    brand_dir = PROJECT_ROOT / brand_slug
    if not brand_dir.exists():
        return {"ok": False, "error": f"Brand dir not found: {brand_dir}"}

    results = {"brand": brand_slug, "synced": {}, "errors": []}

    # ── Brand profile ──────────────────────────────────────────────────────────
    bp = brand_dir / "brand_profile.json"
    if bp.exists():
        profile = _load_json(bp)
        ok = upsert_brand(profile)
        results["synced"]["brand"] = ok
        if verbose: print(f"  brand upsert: {'OK' if ok else 'FAIL'}")
        if not ok:
            results["errors"].append("brand upsert failed")
    else:
        results["errors"].append("brand_profile.json not found")

    # ── Roadmap phases ─────────────────────────────────────────────────────────
    rm = brand_dir / "roadmap.json"
    roadmap = _load_json(rm) if rm.exists() else {}
    phase_topics = {p["phase"]: p.get("title", "") for p in roadmap.get("phases", [])}

    # ── Phase directories ──────────────────────────────────────────────────────
    phase_dirs = sorted([d for d in brand_dir.iterdir()
                         if d.is_dir() and d.name.startswith("phase_")])
    results["synced"]["phases"] = []

    for pd in phase_dirs:
        phase_num = int(pd.name.replace("phase_", ""))
        topic     = phase_topics.get(phase_num, "")

        # Read content_spec if it exists
        spec_path = pd / "content_spec.json"
        spec = _load_json(spec_path) if spec_path.exists() else {}
        if spec.get("title"):
            topic = spec["title"]

        # Upsert phase row
        ok = upsert_phase(brand_slug, phase_num, topic)
        if verbose: print(f"  phase {phase_num} upsert: {'OK' if ok else 'FAIL'}")

        # Upsert content_spec
        if spec:
            ok2 = upsert_content_spec(brand_slug, phase_num, spec)
            if verbose: print(f"    content_spec upsert: {'OK' if ok2 else 'FAIL'}")

        # Compliance
        comp_log = _load_json(brand_dir / "compliance_log.json")
        comp_key = f"phase_{phase_num}_auto"
        if comp_key in comp_log:
            entry = comp_log[comp_key]
            checks = [{"check": k, "status": v} for k, v in entry.get("checks", {}).items()]
            ok3 = save_compliance(brand_slug, phase_num, "sync", entry.get("overall",""), checks)
            if verbose: print(f"    compliance sync: {'OK' if ok3 else 'FAIL'}")

        # Generated files
        file_count = 0
        for f in sorted(pd.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                rel = str(f.relative_to(pd)).replace("\\", "/")
                ok4 = record_file(brand_slug, phase_num, f.suffix.lstrip("."),
                                  rel, f.stat().st_size, None)
                if ok4: file_count += 1
        if verbose: print(f"    files recorded: {file_count}")

        results["synced"]["phases"].append({
            "phase": phase_num, "topic": topic,
            "has_spec": bool(spec), "files": file_count
        })

    return results


def sync_all(verbose: bool = False) -> list:
    """Sync all brands found in the projects directory."""
    brands = [d.name for d in sorted(PROJECT_ROOT.iterdir())
              if d.is_dir() and not d.name.startswith("_")
              and (d / "brand_profile.json").exists()]
    if not brands:
        print("[WARN] No brands with brand_profile.json found.")
        return []
    results = []
    for slug in brands:
        print(f"\n[SYNC] {slug}")
        r = sync_brand(slug, verbose=verbose)
        results.append(r)
        errors = r.get("errors", [])
        phases = r.get("synced", {}).get("phases", [])
        print(f"  Phases: {len(phases)}  Errors: {len(errors)}")
        for e in errors:
            print(f"  ⚠️  {e}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync filesystem → PostgreSQL")
    parser.add_argument("--brand",   default="", help="Sync only this brand slug")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print("  Bhrikuty DB Sync - filesystem to PostgreSQL")
    print(f"{'='*55}\n")

    from db.db import is_available
    if not is_available():
        print("[ERROR] Cannot connect to PostgreSQL.")
        print("  Check DB_HOST / DB_USER / DB_PASSWORD / DB_NAME in .env")
        sys.exit(1)

    if args.brand:
        r = sync_brand(args.brand, args.verbose)
        print(f"\nDone: {r}")
    else:
        sync_all(args.verbose)

    print("\n[DONE] Sync complete. Check your DB now.")
