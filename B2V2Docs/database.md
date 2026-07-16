# database.md — Schema, Relationships, Indexing (Priority 5)

## Role of the database

**Postgres is a shadow index, not the source of truth.** The filesystem (`youtube_scripts/setup/projects/{brand}/phase_N/*`) is authoritative. Every DB write in `db/db.py` is wrapped in `try/except: pass` so the application degrades gracefully with `db_available() == False`. Do not design any new feature that requires the DB to be present — it must always be optional acceleration/indexing on top of the filesystem.

## Current schema (as of `db/schema.sql`)

| Table | Purpose | Key columns |
|---|---|---|
| `brands` | Brand profile shadow | `slug` (unique), `name`, `platforms` (JSONB), `tone_of_voice`/`colors`/`typography`/`logo`/`sound_identity` (JSONB), `content_pillars` (JSONB) |
| `phases` | Per-brand phase metadata | `brand_slug` FK → `brands.slug`, `phase_num`, `topic`, `outline`, `status`; UNIQUE(`brand_slug`, `phase_num`) |
| `pipeline_runs` | One row per pipeline execution | `run_id` (unique), `brand_slug`, `phase_num`, `status`, `args` (JSONB) |
| `pipeline_steps` | One row per step within a run | `run_id` FK, `step_num`, `step_name`, `status`, `output`; UNIQUE(`run_id`, `step_num`) |
| `generated_files` | Tracks every artifact written | `brand_slug`, `phase_num`, `file_type`, `file_path`, `file_size_bytes`, `run_id` FK; UNIQUE(`brand_slug`, `phase_num`, `file_path`) |
| `compliance_logs` | Compliance check results | `brand_slug`, `phase_num`, `run_id`, `overall_status`, `checks` (JSONB) |
| `content_specs` | Parsed `content_spec.json` | `brand_slug`, `phase_num`, `youtube_chapters`/`platform_cuts`/`text_overlays` (JSONB), `tags` (TEXT[]); UNIQUE(`brand_slug`, `phase_num`) |

**Two additional tables exist only via `db/migrate.py`, NOT in `schema.sql`** — `asset_versions` and `content_views`. `db.py` actively queries both (`record_asset_version`/`list_asset_versions`/`log_content_view`/`get_view_counts`). **This is a confirmed drift, not a documentation gap**: a fresh `psql -f db/schema.sql` run, as the file's own header instructs, leaves the database missing two tables the running application depends on. `migrate.py` must be run afterward for the schema to actually match the code.

**Fix requirement** (tracked as `roadmap.md` Phase 1, error E2): `schema.sql` must be the single canonical source that creates every table `db.py` queries. Either fold `asset_versions`/`content_views` into `schema.sql` directly, or replace both files with one numbered migration chain that `schema.sql` is generated from — do not leave two files that can silently diverge again.

## Confirmed config drift (also Phase 1 fix)

`DB_NAME` defaults differ across three files:
- `db/db.py:44` → `"press_jemc"`
- `db/migrate.py:35` → `"bhrikutyflimdirector"`
- `install.py:220` → `"press_jemc"`

Anyone who doesn't set `DB_NAME` explicitly in `.env` will have different scripts silently talking to two different databases. All three must default to the same value, or all three must require the env var explicitly with no silent default — pick one and apply it everywhere; do not add a fourth default.

## Design conventions already in place (follow these for new tables)

- `slug`-based foreign keys to `brands.slug`, not surrogate brand IDs, in every child table — keep this pattern for consistency.
- `JSONB` for variable-shape config (colors, tone, platform cuts) rather than normalizing every brand attribute into columns — this is a reasonable, deliberate choice; do not "fix" it into a rigid schema without a concrete need.
- `updated_at` triggers via `set_updated_at()` — any new mutable table should get the same trigger, not a bespoke one.
- Indexes exist on every `(brand_slug, phase_num)`-style lookup column — new tables queried the same way need the same index shape.

## Planned additions (Phase 7 of `roadmap.md` — `ProjectMemory`, not yet built)

Do not build these ahead of schedule — they depend on real usage history existing first:
- `audience_profiles` — target-audience inferences per brand.
- `templates` — saved style/pacing/voice combinations a brand has used successfully.
- `learned_preferences` — running summary of an operator's typical choices, derived from `pipeline_runs`.

These extend the existing schema; they do not replace any table above.

## Migration process (target, once Phase 1/2 land)

Until Stage 2 of the roadmap replaces `schema.sql` + `migrate.py`'s ad hoc `CREATE TABLE IF NOT EXISTS` pattern with a real numbered migration chain: any schema change must be added to **both** `schema.sql` (so a fresh install is correct) **and** `migrate.py` (so an existing install can catch up) in the same change — never one without the other, which is exactly how the current drift happened.
