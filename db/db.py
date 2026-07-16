"""
db/db.py — PostgreSQL connection helper for Bhrikuty Film Director

Graceful fallback: if psycopg2 is not installed or the DB is unreachable,
all public functions return None / empty results so the file-based pipeline
continues without interruption.

Install driver:
    pip install psycopg2-binary

Apply schema:
    psql -U postgres -d bhrikutyflimdirector -f db/schema.sql
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
        "dbname":   os.environ.get("DB_NAME",  "bhrikutyflimdirector"),
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
            # Ensure brand row exists so FK on pipeline_runs never fires
            cur.execute("""
                INSERT INTO brands (slug, name)
                VALUES (%s, %s)
                ON CONFLICT (slug) DO NOTHING
            """, (brand_slug, brand_slug))
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


# ── Generated files tracker ───────────────────────────────────────────────────

def record_file(brand_slug: str, phase_num: int, file_type: str,
                file_path: str, file_size: int, run_id: str | None) -> bool:
    """Insert a generated-file record (idempotent — skips exact duplicates)."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO generated_files
                    (brand_slug, phase_num, file_type, file_path, file_size_bytes, run_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (brand_slug, phase_num, file_type, file_path, file_size, run_id))
        return True
    except Exception as e:
        log.warning("record_file failed: %s", e)
        return False


def list_files(brand_slug: str, phase_num: int | None = None) -> list:
    """Return generated files for a brand (optionally filtered by phase)."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if phase_num is not None:
                cur.execute("""
                    SELECT file_type, file_path, file_size_bytes, generated_at
                    FROM generated_files
                    WHERE brand_slug = %s AND phase_num = %s
                    ORDER BY generated_at DESC
                """, (brand_slug, phase_num))
            else:
                cur.execute("""
                    SELECT phase_num, file_type, file_path, file_size_bytes, generated_at
                    FROM generated_files WHERE brand_slug = %s
                    ORDER BY phase_num, generated_at DESC
                """, (brand_slug,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning("list_files failed: %s", e)
        return []


# ── Content view tracker ─────────────────────────────────────────────────────

def log_content_view(brand_slug: str, phase_num: int,
                     step_key: str, file_name: str, action: str) -> bool:
    """Record that a user opened a content viewer for this step/file."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO content_views (brand_slug, phase_num, step_key, file_name, action)
                VALUES (%s, %s, %s, %s, %s)
            """, (brand_slug, phase_num, step_key, file_name, action))
        return True
    except Exception as e:
        log.warning("log_content_view failed: %s", e)
        return False


def get_view_counts(brand_slug: str, phase_num: int) -> dict:
    """Return view count per file_name for a phase."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT file_name, COUNT(*) as views
                FROM content_views
                WHERE brand_slug = %s AND phase_num = %s
                GROUP BY file_name ORDER BY views DESC
            """, (brand_slug, phase_num))
            return {row["file_name"]: row["views"] for row in cur.fetchall()}
    except Exception as e:
        log.warning("get_view_counts failed: %s", e)
        return {}


# ── Asset versioning ─────────────────────────────────────────────────────────

def record_asset_version(brand_slug: str, phase_num: int, step_key: str,
                         file_name: str, version: int, file_path: str,
                         media_url: str, file_size: int = 0,
                         extra: dict = None, run_id: str = None) -> bool:
    """Insert a versioned asset record (upsert on conflict)."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO asset_versions
                    (brand_slug, phase_num, step_key, file_name, version,
                     file_path, media_url, file_size, extra, run_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (brand_slug, phase_num, file_name, version)
                DO UPDATE SET
                    file_path  = EXCLUDED.file_path,
                    media_url  = EXCLUDED.media_url,
                    file_size  = EXCLUDED.file_size,
                    extra      = EXCLUDED.extra,
                    run_id     = EXCLUDED.run_id,
                    created_at = NOW()
            """, (brand_slug, phase_num, step_key, file_name, version,
                  file_path, media_url, file_size,
                  json.dumps(extra or {}), run_id))
        return True
    except Exception as e:
        log.warning("record_asset_version failed: %s", e)
        return False


def list_asset_versions(brand_slug: str, phase_num: int,
                        step_key: str = None) -> list:
    """Return all asset versions for a brand+phase, optionally filtered by step."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if step_key:
                cur.execute("""
                    SELECT step_key, file_name, version, file_path, media_url,
                           file_size, extra, run_id, created_at
                    FROM asset_versions
                    WHERE brand_slug = %s AND phase_num = %s AND step_key = %s
                    ORDER BY file_name, version DESC
                """, (brand_slug, phase_num, step_key))
            else:
                cur.execute("""
                    SELECT step_key, file_name, version, file_path, media_url,
                           file_size, extra, run_id, created_at
                    FROM asset_versions
                    WHERE brand_slug = %s AND phase_num = %s
                    ORDER BY step_key, file_name, version DESC
                """, (brand_slug, phase_num))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning("list_asset_versions failed: %s", e)
        return []


def get_next_version(brand_slug: str, phase_num: int,
                     file_name: str) -> int:
    """Return the next version number for a given file (1 if no versions exist)."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(MAX(version), 0) + 1
                FROM asset_versions
                WHERE brand_slug = %s AND phase_num = %s AND file_name = %s
            """, (brand_slug, phase_num, file_name))
            row = cur.fetchone()
            return row[0] if row else 1
    except Exception as e:
        log.warning("get_next_version failed: %s", e)
        return 1


# ── Pipeline step tracking ────────────────────────────────────────────────────

def upsert_pipeline_step(run_id: str, step_num: int, step_name: str,
                         status: str, output: str = "") -> bool:
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO pipeline_steps (run_id, step_num, step_name, status, output, started_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (run_id, step_num) DO UPDATE SET
                    step_name   = EXCLUDED.step_name,
                    status      = EXCLUDED.status,
                    output      = EXCLUDED.output,
                    finished_at = CASE WHEN EXCLUDED.status IN ('done','failed')
                                  THEN NOW() ELSE pipeline_steps.finished_at END
            """, (run_id, step_num, step_name, status, output))
        return True
    except Exception as e:
        log.warning("upsert_pipeline_step failed: %s", e)
        return False


# ── DB summary ────────────────────────────────────────────────────────────────

def get_db_summary() -> dict:
    """Return row counts for all tables — useful for dashboard health check."""
    tables = ["brands", "phases", "pipeline_runs", "pipeline_steps",
              "generated_files", "compliance_logs", "content_specs"]
    result = {}
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            for t in tables:
                cur.execute(f"SELECT COUNT(*) AS n FROM {t}")
                row = cur.fetchone()
                result[t] = row["n"] if row else 0
    except Exception as e:
        log.warning("get_db_summary failed: %s", e)
    return result
