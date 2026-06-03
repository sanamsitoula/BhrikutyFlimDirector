"""
db/db.py — PostgreSQL connection helper for Bhrikuty Film Director

Graceful fallback: if psycopg2 is not installed or the DB is unreachable,
all public functions return None / empty results so the file-based pipeline
continues without interruption.

Install driver:
    pip install psycopg2-binary

Apply schema:
    psql -U postgres -d press_jemc -f db/schema.sql
"""

import os
import json
import logging
from pathlib import Path
from contextlib import contextmanager

log = logging.getLogger("bhrikuty.db")

# ── Load .env so this module works when imported standalone ───────────────────
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

try:
    import psycopg2
    import psycopg2.extras
    _HAS_PSYCOPG2 = True
except ImportError:
    _HAS_PSYCOPG2 = False


def _cfg() -> dict:
    return {
        "host":     os.environ.get("DB_HOST", "localhost"),
        "port":     int(os.environ.get("DB_PORT", "5432")),
        "dbname":   os.environ.get("DB_NAME",  "press_jemc"),
        "user":     os.environ.get("DB_USER",  "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }


def is_available() -> bool:
    if not _HAS_PSYCOPG2:
        return False
    try:
        conn = psycopg2.connect(**_cfg())
        conn.close()
        return True
    except Exception:
        return False


@contextmanager
def get_conn():
    if not _HAS_PSYCOPG2:
        raise RuntimeError("psycopg2 not installed — run: pip install psycopg2-binary")
    conn = psycopg2.connect(**_cfg(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Brand operations ──────────────────────────────────────────────────────────

def upsert_brand(profile: dict) -> bool:
    """Insert or update a brand from a brand_profile dict. Returns True on success."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO brands
                    (slug, name, tagline, niche, target_audience,
                     platforms, tone_of_voice, colors, typography,
                     logo, sound_identity, content_pillars,
                     card_dimensions, animation_style)
                VALUES
                    (%(slug)s, %(name)s, %(tagline)s, %(niche)s, %(target_audience)s,
                     %(platforms)s, %(tone_of_voice)s, %(colors)s, %(typography)s,
                     %(logo)s, %(sound_identity)s, %(content_pillars)s,
                     %(card_dimensions)s, %(animation_style)s)
                ON CONFLICT (slug) DO UPDATE SET
                    name            = EXCLUDED.name,
                    tagline         = EXCLUDED.tagline,
                    niche           = EXCLUDED.niche,
                    target_audience = EXCLUDED.target_audience,
                    platforms       = EXCLUDED.platforms,
                    tone_of_voice   = EXCLUDED.tone_of_voice,
                    colors          = EXCLUDED.colors,
                    typography      = EXCLUDED.typography,
                    logo            = EXCLUDED.logo,
                    sound_identity  = EXCLUDED.sound_identity,
                    content_pillars = EXCLUDED.content_pillars,
                    card_dimensions = EXCLUDED.card_dimensions,
                    animation_style = EXCLUDED.animation_style,
                    updated_at      = NOW()
            """, {
                "slug":            profile.get("brand_slug", ""),
                "name":            profile.get("brand_name", ""),
                "tagline":         profile.get("tagline", ""),
                "niche":           profile.get("niche", ""),
                "target_audience": profile.get("target_audience", ""),
                "platforms":       json.dumps(profile.get("platforms", [])),
                "tone_of_voice":   json.dumps(profile.get("tone_of_voice", {})),
                "colors":          json.dumps(profile.get("colors", {})),
                "typography":      json.dumps(profile.get("typography", {})),
                "logo":            json.dumps(profile.get("logo", {})),
                "sound_identity":  json.dumps(profile.get("sound_identity", {})),
                "content_pillars": json.dumps(profile.get("content_pillars", [])),
                "card_dimensions": json.dumps(profile.get("card_dimensions", {})),
                "animation_style": json.dumps(profile.get("animation_style", {})),
            })
        return True
    except Exception as e:
        log.warning("upsert_brand failed: %s", e)
        return False


def list_brands() -> list:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT slug, name, tagline, niche, created_at FROM brands ORDER BY name")
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning("list_brands failed: %s", e)
        return []


def get_brand(slug: str) -> dict | None:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM brands WHERE slug = %s", (slug,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log.warning("get_brand failed: %s", e)
        return None


# ── Phase operations ──────────────────────────────────────────────────────────

def upsert_phase(brand_slug: str, phase_num: int, topic: str = "", tags: str = "") -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO phases (brand_slug, phase_num, topic, tags)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (brand_slug, phase_num) DO UPDATE SET
                    topic      = EXCLUDED.topic,
                    tags       = EXCLUDED.tags,
                    updated_at = NOW()
            """, (brand_slug, phase_num, topic, tags))
        return True
    except Exception as e:
        log.warning("upsert_phase failed: %s", e)
        return False


def update_phase_status(brand_slug: str, phase_num: int, status: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE phases SET status = %s, updated_at = NOW()
                WHERE brand_slug = %s AND phase_num = %s
            """, (status, brand_slug, phase_num))
        return True
    except Exception as e:
        log.warning("update_phase_status failed: %s", e)
        return False


def list_phases(brand_slug: str) -> list:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT phase_num, topic, tags, status, updated_at
                FROM phases WHERE brand_slug = %s ORDER BY phase_num
            """, (brand_slug,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning("list_phases failed: %s", e)
        return []


# ── Pipeline run operations ───────────────────────────────────────────────────

def create_run(run_id: str, brand_slug: str, phase_num: int, args: dict) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO pipeline_runs (run_id, brand_slug, phase_num, args)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (run_id) DO NOTHING
            """, (run_id, brand_slug, phase_num, json.dumps(args)))
        return True
    except Exception as e:
        log.warning("create_run failed: %s", e)
        return False


def finish_run(run_id: str, status: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE pipeline_runs
                SET status = %s, finished_at = NOW()
                WHERE run_id = %s
            """, (status, run_id))
        return True
    except Exception as e:
        log.warning("finish_run failed: %s", e)
        return False


def list_runs(brand_slug: str, limit: int = 20) -> list:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT run_id, phase_num, status, started_at, finished_at
                FROM pipeline_runs
                WHERE brand_slug = %s
                ORDER BY started_at DESC
                LIMIT %s
            """, (brand_slug, limit))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning("list_runs failed: %s", e)
        return []


# ── Compliance log operations ─────────────────────────────────────────────────

def save_compliance(brand_slug: str, phase_num: int, run_id: str,
                    overall_status: str, checks: list) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO compliance_logs
                    (brand_slug, phase_num, run_id, overall_status, checks)
                VALUES (%s, %s, %s, %s, %s)
            """, (brand_slug, phase_num, run_id, overall_status, json.dumps(checks)))
        return True
    except Exception as e:
        log.warning("save_compliance failed: %s", e)
        return False


# ── Content spec operations ───────────────────────────────────────────────────

def upsert_content_spec(brand_slug: str, phase_num: int, spec: dict) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO content_specs
                    (brand_slug, phase_num, title, duration_min,
                     youtube_chapters, platform_cuts, text_overlays, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (brand_slug, phase_num) DO UPDATE SET
                    title            = EXCLUDED.title,
                    duration_min     = EXCLUDED.duration_min,
                    youtube_chapters = EXCLUDED.youtube_chapters,
                    platform_cuts    = EXCLUDED.platform_cuts,
                    text_overlays    = EXCLUDED.text_overlays,
                    tags             = EXCLUDED.tags,
                    created_at       = NOW()
            """, (
                brand_slug, phase_num,
                spec.get("title", ""),
                spec.get("duration_min", 12),
                json.dumps(spec.get("youtube", {}).get("chapters", [])),
                json.dumps(spec.get("platform_cuts", {})),
                json.dumps(spec.get("text_overlays", [])),
                spec.get("tags", []) if isinstance(spec.get("tags"), list) else [],
            ))
        return True
    except Exception as e:
        log.warning("upsert_content_spec failed: %s", e)
        return False
