-- =============================================================
--  Bhrikuty Film Director — PostgreSQL Schema
--  Database : bhrikutyflimdirector
--  Run once : psql -U postgres -d bhrikutyflimdirector -f db/schema.sql
-- =============================================================

-- ── Extensions ────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Brands ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS brands (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(200)        NOT NULL,
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
);

-- ── Phases ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS phases (
    id          SERIAL PRIMARY KEY,
    brand_slug  VARCHAR(100) NOT NULL REFERENCES brands(slug) ON DELETE CASCADE,
    phase_num   INTEGER      NOT NULL,
    topic       TEXT,
    outline     TEXT,
    duration_min INTEGER     DEFAULT 12,
    tags        TEXT,
    status      VARCHAR(50)  DEFAULT 'pending',
    created_at  TIMESTAMP    DEFAULT NOW(),
    updated_at  TIMESTAMP    DEFAULT NOW(),
    UNIQUE (brand_slug, phase_num)
);

-- ── Pipeline runs ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id          SERIAL PRIMARY KEY,
    run_id      VARCHAR(64) UNIQUE NOT NULL,
    brand_slug  VARCHAR(100) REFERENCES brands(slug),
    phase_num   INTEGER,
    status      VARCHAR(50)  DEFAULT 'running',
    args        JSONB        DEFAULT '{}',
    started_at  TIMESTAMP    DEFAULT NOW(),
    finished_at TIMESTAMP
);

-- ── Pipeline steps per run ────────────────────────────────────
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
);

-- ── Generated files tracker ───────────────────────────────────
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
);

-- ── Compliance logs ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS compliance_logs (
    id              SERIAL PRIMARY KEY,
    brand_slug      VARCHAR(100),
    phase_num       INTEGER,
    run_id          VARCHAR(64),
    overall_status  VARCHAR(50),
    checks          JSONB DEFAULT '[]',
    checked_at      TIMESTAMP DEFAULT NOW()
);

-- ── Content specs (parsed content_spec.json) ──────────────────
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
);

-- ── Content views (dashboard view/action log) ──────────────────
CREATE TABLE IF NOT EXISTS content_views (
    id         SERIAL PRIMARY KEY,
    brand_slug VARCHAR(100) NOT NULL,
    phase_num  INTEGER      NOT NULL,
    step_key   VARCHAR(200),
    file_name  VARCHAR(500),
    action     VARCHAR(500),
    viewed_at  TIMESTAMP    DEFAULT NOW()
);

-- ── Asset versions (mirrors on-disk .versions/{step}/vN/ history) ──
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
);

-- ── Auto-update updated_at ────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_brands_updated_at') THEN
        CREATE TRIGGER trg_brands_updated_at
            BEFORE UPDATE ON brands
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_phases_updated_at') THEN
        CREATE TRIGGER trg_phases_updated_at
            BEFORE UPDATE ON phases
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END $$;

-- ── Useful indexes ────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_phases_brand       ON phases(brand_slug);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_brand ON pipeline_runs(brand_slug, phase_num);
CREATE INDEX IF NOT EXISTS idx_gen_files_brand     ON generated_files(brand_slug, phase_num);
CREATE INDEX IF NOT EXISTS idx_compliance_brand    ON compliance_logs(brand_slug, phase_num);
CREATE INDEX IF NOT EXISTS idx_content_specs_brand ON content_specs(brand_slug, phase_num);
CREATE INDEX IF NOT EXISTS idx_content_views_brand ON content_views(brand_slug, phase_num);
CREATE INDEX IF NOT EXISTS idx_asset_versions_lookup ON asset_versions(brand_slug, phase_num, step_key);

-- ── Seed: import existing file-based brands (run manually) ────
-- INSERT INTO brands (slug, name) VALUES ('chain_clarity', 'Chain Clarity')
-- ON CONFLICT (slug) DO NOTHING;
