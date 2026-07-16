# deployment.md — Infrastructure, CI/CD, Monitoring, Backups

## Current state (verified)

- **No containerization.** The app runs as a plain Python process (`python server.py`) on a local machine, plus a Node/TS Remotion sub-project (`remotion/`) invoked via `node scripts/render_all_cards.js`.
- **No CI/CD.** No `.github/workflows` exist — nothing runs lint/test/build on push today.
- **No monitoring/observability.** No structured logging beyond `print()` statements (e.g. `[AUDIO] Uploaded: ...`, `[CLIP] Uploaded: ...`); no metrics, no alerting.
- **No backup strategy documented.** Persistent state is split across:
  - Filesystem (`youtube_scripts/setup/projects/{brand}/`) — the real source of truth, including `.versions/` history.
  - Postgres (`db/db.py`) — a best-effort shadow index, optional (`db_available()` gates everything).
- **Install/bootstrap**: `install.py` (435 lines) handles pip/npm installs and schema application as a separate, independent process from `pipeline.py`/`server.py` — it duplicates config logic rather than sharing it (flagged in `architecture.md`/`coding-rules.md`).

## Rules for new work

1. **Do not introduce a deployment target (Docker, cloud VM, serverless) speculatively.** The current local-first, filesystem-as-truth model is a deliberate fit for a single-operator tool — containerization is only warranted once multi-machine or hosted use is an actual, scheduled requirement (see `architecture.md` §4/CP7's note on multi-user collaboration being explicitly blocked on auth + shared storage first).
2. **CI, when added (`roadmap.md` Stage 3), gates on**: lint (once configured, `coding-rules.md`) + the pytest suite covering `core/` + the Demo & Validation harness (one pass/fail row per output format). It should not gate on anything requiring a live paid API call by default — those run behind an explicit `--live` opt-in flag.
3. **Backup**: until a formal strategy is defined, any operational change that could affect the four live brands' data must be preceded by a manual, verified backup of the affected `youtube_scripts/setup/projects/{brand}/` directory (and a `pg_dump` if Postgres is in use for that brand) — this is a standing operational rule, not a future roadmap item.
4. **Any new environment variable must be added to `.env.example`** in the same change that introduces it, and must not silently default differently across files (see the `DB_NAME` drift in `database.md` as the cautionary example — do not repeat that pattern for any new config value).

## Target state (sequenced in `roadmap.md`, not built yet)

- **Stage 3**: GitHub Actions workflow running lint + the new pytest suite + the Demo & Validation harness on every push/PR — the first real CI gate this project will have.
- **Stage 6+ (optional)**: distributed/cloud rendering (e.g. Lambda-based, per the HyperFrames pattern evaluated in the historical audit) — deferred until local rendering is a proven bottleneck, not built preemptively.
- A numbered migration chain (replacing `schema.sql` + `migrate.py`'s current ad hoc pattern, see `database.md`) is a deployment-adjacent prerequisite for any environment where a fresh install must be reliably reproducible.

## Monitoring (deferred, flagged for when job-queue work lands)

Once the durable job queue (CP3) exists, it should expose enough state (job status, retry count, cost-per-job for paid-API calls) to answer "is anything stuck, and what did this run cost" without reading raw `print()` output — this is a natural extension of the queue work, not a separate monitoring project, and should not be over-built ahead of that need.
