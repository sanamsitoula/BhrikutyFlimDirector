"""
db/migrate.py - Apply schema migrations via Python (no psql required)
======================================================================
Usage: python db/migrate.py
"""

import os
import sys
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

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("[ERROR] psycopg2 not installed: pip install psycopg2-binary")
    sys.exit(1)


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "bhrikutyflimdirector"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
    )


MIGRATIONS = [
    # ── Core tables ───────────────────────────────────────────────────────────
    ("create_brands", """
        CREATE TABLE IF NOT EXISTS brands (
            id              SERIAL PRIMARY KEY,
            slug            VARCHAR(100) UNIQUE NOT NULL,
            name            VARCHAR(200) NOT NULL DEFAULT '',
            tagline         TEXT,
            niche           TEXT,
            target_audience TEXT,
            platforms       JSONB  DEFAULT '[]',
            tone_of_voice   JSONB  DEFAULT '{}',
            colors          JSONB  DEFAULT '{}',
            typography      JSONB  DEFAULT '{}',
            logo            JSONB  DEFAULT '{}',
            sound_identity  JSONB  DEFAULT '{}',
            content_pillars JSONB  DEFAULT '[]',
            card_dimensions JSONB  DEFAULT '{}',
            animation_style JSONB  DEFAULT '{}',
            created_at      TIMESTAMP DEFAULT NOW(),
            updated_at      TIMESTAMP DEFAULT NOW()
        )
    """),

    ("create_phases", """
        CREATE TABLE IF NOT EXISTS phases (
            id           SERIAL PRIMARY KEY,
            brand_slug   VARCHAR(100) NOT NULL REFERENCES brands(slug) ON DELETE CASCADE,
            phase_num    INTEGER      NOT NULL,
            topic        TEXT,
            outline      TEXT,
            duration_min INTEGER      DEFAULT 12,
            tags         TEXT,
            status       VARCHAR(50)  DEFAULT 'pending',
            created_at   TIMESTAMP    DEFAULT NOW(),
            updated_at   TIMESTAMP    DEFAULT NOW(),
            UNIQUE (brand_slug, phase_num)
        )
    """),

    ("create_pipeline_runs", """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id          SERIAL PRIMARY KEY,
            run_id      VARCHAR(64) UNIQUE NOT NULL,
            brand_slug  VARCHAR(100) REFERENCES brands(slug),
            phase_num   INTEGER,
            status      VARCHAR(50)  DEFAULT 'running',
            args        JSONB        DEFAULT '{}',
            started_at  TIMESTAMP    DEFAULT NOW(),
            finished_at TIMESTAMP
        )
    """),

    ("create_pipeline_steps", """
        CREATE TABLE IF NOT EXISTS pipeline_steps (
            id          SERIAL PRIMARY KEY,
            run_id      VARCHAR(64) NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
            step_num    INTEGER     NOT NULL,
            step_name   VARCHAR(200),
            status      VARCHAR(50)  DEFAULT 'pending',
            output      TEXT,
            started_at  TIMESTAMP,
            finished_at TIMESTAMP,
            UNIQUE (run_id, step_num)
        )
    """),

    ("create_generated_files", """
        CREATE TABLE IF NOT EXISTS generated_files (
            id              SERIAL PRIMARY KEY,
            brand_slug      VARCHAR(100),
            phase_num       INTEGER,
            file_type       VARCHAR(100),
            file_path       TEXT,
            file_size_bytes BIGINT,
            run_id          VARCHAR(64) REFERENCES pipeline_runs(run_id),
            generated_at    TIMESTAMP DEFAULT NOW(),
            UNIQUE (brand_slug, phase_num, file_path)
        )
    """),

    ("create_compliance_logs", """
        CREATE TABLE IF NOT EXISTS compliance_logs (
            id             SERIAL PRIMARY KEY,
            brand_slug     VARCHAR(100),
            phase_num      INTEGER,
            run_id         VARCHAR(64),
            overall_status VARCHAR(50),
            checks         JSONB DEFAULT '[]',
            checked_at     TIMESTAMP DEFAULT NOW()
        )
    """),

    ("create_content_specs", """
        CREATE TABLE IF NOT EXISTS content_specs (
            id               SERIAL PRIMARY KEY,
            brand_slug       VARCHAR(100),
            phase_num        INTEGER,
            title            TEXT,
            duration_min     INTEGER,
            youtube_chapters JSONB DEFAULT '[]',
            platform_cuts    JSONB DEFAULT '{}',
            text_overlays    JSONB DEFAULT '[]',
            tags             TEXT[],
            created_at       TIMESTAMP DEFAULT NOW(),
            UNIQUE (brand_slug, phase_num)
        )
    """),

    # ── Asset versioning ──────────────────────────────────────────────────────────
    ("create_asset_versions", """
        CREATE TABLE IF NOT EXISTS asset_versions (
            id          SERIAL PRIMARY KEY,
            brand_slug  VARCHAR(100) NOT NULL,
            phase_num   INTEGER      NOT NULL,
            step_key    VARCHAR(100) NOT NULL,
            file_name   VARCHAR(500) NOT NULL,
            version     INTEGER      NOT NULL DEFAULT 1,
            file_path   TEXT,
            media_url   TEXT,
            file_size   BIGINT       DEFAULT 0,
            extra       JSONB        DEFAULT '{}',
            run_id      VARCHAR(64),
            created_at  TIMESTAMP    DEFAULT NOW(),
            UNIQUE (brand_slug, phase_num, file_name, version)
        )
    """),
    ("idx_asset_versions_lookup", """
        CREATE INDEX IF NOT EXISTS idx_asset_versions_lookup
        ON asset_versions (brand_slug, phase_num, step_key)
    """),

    # ── Add missing unique constraints (safe - IF NOT EXISTS equiv via DO block) ─
    ("unique_pipeline_steps", """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'pipeline_steps_run_id_step_num_key'
            ) THEN
                ALTER TABLE pipeline_steps ADD CONSTRAINT pipeline_steps_run_id_step_num_key
                    UNIQUE (run_id, step_num);
            END IF;
        END $$
    """),

    ("unique_generated_files", """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'generated_files_brand_slug_phase_num_file'
            ) THEN
                ALTER TABLE generated_files ADD CONSTRAINT generated_files_brand_slug_phase_num_file
                    UNIQUE (brand_slug, phase_num, file_path);
            END IF;
        END $$
    """),

    # ── Indexes ───────────────────────────────────────────────────────────────
    ("idx_phases_brand",       "CREATE INDEX IF NOT EXISTS idx_phases_brand ON phases(brand_slug)"),
    ("idx_runs_brand",         "CREATE INDEX IF NOT EXISTS idx_pipeline_runs_brand ON pipeline_runs(brand_slug, phase_num)"),
    ("idx_gen_files_brand",    "CREATE INDEX IF NOT EXISTS idx_gen_files_brand ON generated_files(brand_slug, phase_num)"),
    ("idx_compliance_brand",   "CREATE INDEX IF NOT EXISTS idx_compliance_brand ON compliance_logs(brand_slug, phase_num)"),
    ("idx_content_specs_brand","CREATE INDEX IF NOT EXISTS idx_content_specs_brand ON content_specs(brand_slug, phase_num)"),

    # ── Trigger for updated_at ────────────────────────────────────────────────
    ("set_updated_at_fn", """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql
    """),
    ("trg_brands_updated_at", """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_brands_updated_at') THEN
                CREATE TRIGGER trg_brands_updated_at
                    BEFORE UPDATE ON brands
                    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
            END IF;
        END $$
    """),
    ("trg_phases_updated_at", """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_phases_updated_at') THEN
                CREATE TRIGGER trg_phases_updated_at
                    BEFORE UPDATE ON phases
                    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
            END IF;
        END $$
    """),
]


def run_migrations():
    print(f"\n{'='*55}")
    print("  Bhrikuty DB Migrations")
    print(f"  DB: {os.environ.get('DB_NAME')} @ {os.environ.get('DB_HOST')}")
    print(f"{'='*55}\n")

    try:
        conn = get_conn()
        print(f"  Connected to: {os.environ.get('DB_NAME')}\n")
    except Exception as e:
        print(f"[ERROR] Cannot connect: {e}")
        print("  Check DB_HOST / DB_USER / DB_PASSWORD / DB_NAME in .env")
        sys.exit(1)

    ok, failed = 0, 0
    cur = conn.cursor()

    for name, sql in MIGRATIONS:
        try:
            cur.execute(sql.strip())
            conn.commit()
            print(f"  [OK]  {name}")
            ok += 1
        except Exception as e:
            conn.rollback()
            print(f"  [WARN] {name}: {str(e)[:80]}")
            failed += 1

    cur.close()
    conn.close()

    print(f"\n  Done: {ok} OK, {failed} warnings")
    print(f"\nNext step: python db/sync.py  (populate from filesystem)")


if __name__ == "__main__":
    run_migrations()
