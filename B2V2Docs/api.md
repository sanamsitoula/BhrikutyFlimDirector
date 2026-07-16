# api.md — API Contracts, Versioning, Error Responses (Priority 6)

## Current implementation

`server.py` implements a hand-rolled `http.server.BaseHTTPRequestHandler`. Routes are dispatched via long `if/elif re.match(...)` chains in `do_GET` (server.py:230) and `do_POST` (server.py:342). **There is no framework, no versioning prefix (`/v1/...`), and no OpenAPI/schema definition.** This document is the authoritative route inventory until that changes.

## Route inventory (verified against `server.py` directly)

### Static pages (GET)

| Route | Serves |
|---|---|
| `/`, `/dashboard.html` | `dashboard.html` |
| `/projects`, `/projects.html` | `projects.html` |
| `/brand`, `/brand.html` | `brand.html` |
| `/tools`, `/tools.html` | `tools.html` |
| `/phase/{project}/{num}` | `phase_dashboard.html` |
| any other existing file path under `BASE_DIR` | served with content-type inferred from extension |

### Data/API routes (GET)

| Route | Handler | Notes |
|---|---|---|
| `/api/brands` | `_api_brands` | list all brands |
| `/api/brands/{slug}` | `_api_brand` | single brand |
| `/api/projects` | `_api_projects` | |
| `/api/projects/{name}/summary` | `_api_project_summary` | |
| `/api/projects/{slug}/runs` | `_api_runs` | |
| `/api/phase-data?project=&phase=` | `_api_phase_data` | defaults: project=`chain_clarity`, phase=`1` — **defaulting to a live brand is a footgun; see Risks below** |
| `/api/file?project=&phase=&file=` | `_api_file` | reads a specific file; path-traversal guard is inline, not shared |
| `/api/file-versions?project=&phase=&step=` | `_api_file_versions` | `.versions/` history |
| `/api/output-text?project=&phase=&path=` | `_api_output_text` | |
| `/api/browse?project=&phase=` | `_api_browse` | |
| `/api/jobs/{id}/stream` | `_stream_job` | Server-Sent Events; one thread per job, `queue.Queue`-backed, no reconnect/resume beyond replaying a buffered list |
| `/api/jobs/{id}` | `_api_job_status` | |
| `/api/db-status` | inline `{"available": db_available()}` | |
| `/api/db-summary` | `_api_db_summary` | |
| `/api/db-sync?brand=` | `_api_db_sync` | |
| `/api/tools-status` | `_api_tools_status` | |
| `/media/{project}/{phase}/{subpath}` | `_serve_media` | serves generated media files |

### Data/API routes (POST)

| Route | Handler | Body | Notes |
|---|---|---|---|
| `/api/brands` | `_api_create_brand` | JSON | |
| `/api/brands/{slug}` | `_api_update_brand` | JSON | |
| `/api/run` | `_api_run` | JSON | spawns a phase run — currently a raw `threading.Thread(daemon=True)`, no concurrency cap (CP3 in `architecture.md`) |
| `/api/run-step` | `_api_run_step` | JSON | runs a single pipeline step |
| `/api/save-file` | `_api_save_file` | JSON | |
| `/api/create-phase` | `_api_create_phase` | JSON | |
| `/api/publish` | `_api_publish` | JSON | |
| `/api/log-view` | `_api_log_view` | JSON | |
| `/api/upload-audio` | inline handler | multipart | writes into `phase_N/voiceover/`; filename validated inline against `../`, `..\\`, `/`, `\\` |
| `/api/upload-clip` | inline handler | multipart | writes into `phase_N/clips/`; **same filename is currently a dead end — nothing reads it back into a render** (see `product.md` Journey D) |

## Response conventions (as currently implemented — not fully consistent, flagged for `roadmap.md` Phase 1/3)

- Success: `_send_json(data)` → `200` with JSON body, shape varies per endpoint (no shared envelope).
- Errors: `_send_json({"error": "..."}, status)` — status codes used inconsistently (mostly `400`/`404`); no single documented error-shape contract yet.
- **No request validation layer**: JSON bodies are `json.loads()`'d and read with `.get()` defaults inline per handler — malformed input degrades to a default rather than a `400` in most places. This is forgiving but means the same malformed request can behave differently per endpoint.

## Known gaps (do not build new routes that repeat these patterns)

1. **No authentication/authorization on any route.** Acceptable only for localhost-only use — see `security.md`. Any new route touching real user data (uploaded footage/faces) must not ship without addressing CP7.
2. **Path-traversal guards are re-implemented per-endpoint** (`/api/upload-audio`, `/api/upload-clip`, `_api_file`) rather than one shared, tested guard function. New file-accepting endpoints must call a **shared** guard, not copy the inline check again.
3. **No response envelope standard.** New endpoints should at minimum: return `{"error": "<message>"}` with an appropriate 4xx/5xx on failure, and avoid inventing a fourth different success-shape convention without checking existing ones first.
4. **No API versioning.** If a breaking route change is ever needed, decide on a versioning strategy (`/api/v2/...` vs. header-based) before shipping — do not silently change an existing route's response shape, since the dashboard pages consume these routes directly with no client-side schema validation.

## Target (once `api/` becomes a real thin layer — `roadmap.md` Stage 2+)

- Routes move to `api/routes/*.py`; the business logic they currently contain (regex parsing, compliance status computation) moves to `core/` — **the route's URL, method, and response shape do not change** as part of this move (backward compatibility requirement, `requirements.md` NFR-8).
- A single request-validation and error-envelope convention is introduced once, applied to all routes going forward — not retrofitted to every existing route in one pass unless a specific route is already being touched for another reason.
