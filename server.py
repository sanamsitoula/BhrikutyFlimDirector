#!/usr/bin/env python3
"""
server.py — Bhrikuty Dashboard Web Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run:  python server.py
Open: http://localhost:8080

No external dependencies — uses Python's built-in http.server.
"""

import subprocess
import sys
import os
import re
import json
import threading
import queue
import uuid
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR     = Path(__file__).parent
PROJECT_ROOT = BASE_DIR / "youtube_scripts" / "setup" / "projects"

# Load .env
_env = BASE_DIR / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# DB (optional — file-based mode works without it)
try:
    sys.path.insert(0, str(BASE_DIR))
    from db.db import (upsert_brand, list_runs, create_run, finish_run,
                       is_available as db_available)
    from tools.init_brand import scaffold_brand
    _DB = True
except Exception:
    _DB = False
    def db_available():   return False
    def upsert_brand(_):  return False
    def list_runs(*_):    return []
    def create_run(*_):   return False
    def finish_run(*_):   return False
    def scaffold_brand(profile, **kw):
        # Minimal fallback: just write brand_profile.json
        slug = profile.get("brand_slug", "")
        d = PROJECT_ROOT / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "brand_profile.json").write_text(
            json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return d

jobs: dict = {}  # job_id -> {status, output, q, cmd}

# ── Asset versioning helpers ──────────────────────────────────────────────────

# Maps cmd_type → list of (step_key, relative paths relative to phase_dir or output_dir)
_STEP_OUTPUTS = {
    "generate":     ("script",    ["script.md", "script_short.md", "subtitles.srt",
                                    "voiceover_brief.md", "music_brief.md",
                                    "infographics.md", "clip_brief.md", "content_spec.json"]),
    "tts":          ("voiceover", ["voiceover"]),
    "create_video":     ("video",     ["youtube", "youtube_shorts"]),   # inside _output/phase_NN/
    "remotion_compose": ("video",     ["youtube", "youtube_shorts"]),
    "platform_cut": ("platform",  ["tiktok", "instagram", "twitter", "linkedin"]),
    "text_content": ("text",      ["blog", "github"]),
    "compliance":   ("compliance", ["compliance_report_auto.md"]),
}


def _backup_step_files(phase_dir: Path, out_dir: Path, cmd_type: str) -> int:
    """Copy existing output files to .versions/vN/ before a step re-runs.
    Returns the new version number (1 if this is the first run, ≥2 on re-runs).
    """
    import shutil
    step_key, rel_paths = _STEP_OUTPUTS.get(cmd_type, (cmd_type, []))
    version_base = phase_dir / ".versions" / step_key
    version_base.mkdir(parents=True, exist_ok=True)

    # Next version number
    existing = [int(d.name[1:]) for d in version_base.iterdir()
                if d.is_dir() and d.name.startswith("v") and d.name[1:].isdigit()]
    next_v = max(existing, default=0) + 1

    backed_up = []
    for rel in rel_paths:
        # Files can live in phase_dir OR _output/phase_NN/
        for base in (phase_dir, out_dir):
            src = base / rel
            if src.exists():
                dst = version_base / f"v{next_v}" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if src.is_dir():
                        if dst.exists():
                            shutil.rmtree(str(dst))
                        shutil.copytree(str(src), str(dst))
                    else:
                        shutil.copy2(str(src), str(dst))
                    backed_up.append(rel)
                except Exception as e:
                    print(f"  [VERSION] backup {src} → {dst} failed: {e}")

    if backed_up:
        print(f"  [VERSION] Backed up v{next_v}: {', '.join(backed_up)}")
    return next_v


def _scan_step_versions(phase_dir: Path, out_dir: Path) -> dict:
    """Scan .versions/ and return a dict of step_key → list of version info dicts."""
    version_base = phase_dir / ".versions"
    if not version_base.exists():
        return {}

    result = {}
    for step_dir in sorted(version_base.iterdir()):
        if not step_dir.is_dir():
            continue
        step_key = step_dir.name
        versions = []
        for vdir in sorted(step_dir.iterdir()):
            if not vdir.is_dir() or not vdir.name.startswith("v"):
                continue
            vnum_s = vdir.name[1:]
            if not vnum_s.isdigit():
                continue
            vnum = int(vnum_s)
            # Collect files in this version snapshot
            vfiles = []
            for f in sorted(vdir.rglob("*")):
                if f.is_file():
                    rel  = str(f.relative_to(vdir)).replace("\\", "/")
                    size = f.stat().st_size
                    mtime = int(f.stat().st_mtime)
                    vfiles.append({"name": f.name, "path": rel,
                                   "size_mb": round(size / 1024 / 1024, 2),
                                   "ts": mtime})
            if vfiles:
                versions.append({
                    "version": vnum,
                    "label":   f"v{vnum}",
                    "files":   vfiles,
                    "ts":      max(f["ts"] for f in vfiles),
                })
        if versions:
            result[step_key] = sorted(versions, key=lambda x: x["version"], reverse=True)

    return result


def _record_versions_to_db(brand_slug: str, phase_num: int,
                            phase_dir: Path, out_dir: Path,
                            step_key: str, version: int, run_id: str):
    """Write asset version records to PostgreSQL (best-effort)."""
    try:
        from db.db import record_asset_version, is_available as _dbok
        if not _dbok():
            return
        _, rel_paths = _STEP_OUTPUTS.get(step_key, (step_key, []))
        for rel in rel_paths:
            for base, url_base in ((phase_dir, f"phase_{phase_num}"),
                                   (out_dir, f"_output/phase_{phase_num:02d}")):
                src = base / rel
                if not src.exists():
                    continue
                files = [src] if src.is_file() else list(src.rglob("*"))
                for f in files:
                    if not f.is_file():
                        continue
                    rel_f = str(f.relative_to(base)).replace("\\", "/")
                    media_url = f"/media/{brand_slug}/{phase_num}/{url_base.split('/',1)[-1]}/{rel_f}"
                    record_asset_version(
                        brand_slug, phase_num, step_key,
                        file_name=f.name,
                        version=version,
                        file_path=str(f).replace("\\", "/"),
                        media_url=media_url,
                        file_size=f.stat().st_size,
                        extra={"rel_path": rel_f},
                        run_id=run_id,
                    )
    except Exception as e:
        print(f"  [VERSION DB] {e}")


def build_pipeline_cmd(data: dict) -> list:
    cmd = [sys.executable, str(BASE_DIR / "pipeline.py")]
    cmd += ["--project", data.get("project", "chain_clarity")]
    cmd += ["--phase", str(data.get("phase", 1))]
    if data.get("topic"):
        cmd += ["--topic", data["topic"]]
    if data.get("outline"):
        cmd += ["--outline", data["outline"]]
    if data.get("duration"):
        cmd += ["--duration", str(data["duration"])]
    if data.get("tags"):
        cmd += ["--tags", data["tags"]]
    if data.get("provider") and data["provider"] != "auto":
        cmd += ["--provider", data["provider"]]
    if data.get("skip_generate"):
        cmd.append("--skip-generate")
    if data.get("skip_voiceover"):
        cmd.append("--skip-voiceover")
    if data.get("skip_remotion"):
        cmd.append("--skip-remotion")
    if data.get("skip_text"):
        cmd.append("--skip-text")
    return cmd


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default access log; server prints its own

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        import re
        from urllib.parse import parse_qs, urlparse
        path = self.path.split("?")[0].rstrip("/") or "/"
        qs   = parse_qs(urlparse(self.path).query)

        if path in ("/", "/dashboard.html"):
            self._serve_file(BASE_DIR / "dashboard.html", "text/html; charset=utf-8")

        elif path in ("/projects", "/projects.html"):
            self._serve_file(BASE_DIR / "projects.html", "text/html; charset=utf-8")

        elif path in ("/brand", "/brand.html"):
            self._serve_file(BASE_DIR / "brand.html", "text/html; charset=utf-8")

        elif path in ("/tools", "/tools.html"):
            self._serve_file(BASE_DIR / "tools.html", "text/html; charset=utf-8")

        elif path == "/api/brands":
            self._api_brands()

        elif re.match(r"^/api/brands/[^/]+$", path):
            slug = path.split("/")[3]
            self._api_brand(slug)

        elif re.match(r"^/api/projects/[^/]+/summary$", path):
            proj_name = path.split("/")[3]
            self._api_project_summary(proj_name)

        elif re.match(r"^/phase/[^/]+/\d+$", path):
            # Per-phase dashboard: /phase/{project}/{num}
            self._serve_file(BASE_DIR / "phase_dashboard.html", "text/html; charset=utf-8")

        elif re.match(r"^/media/[^/]+/\d+/.+$", path):
            # Media files: /media/{project}/{phase}/{subpath}
            parts = path.lstrip("/").split("/")
            project, phase = parts[1], int(parts[2])
            subpath = "/".join(parts[3:])
            self._serve_media(project, phase, subpath)

        elif path == "/api/projects":
            self._api_projects()

        elif path == "/api/phase-data":
            self._api_phase_data(
                qs.get("project", ["chain_clarity"])[0],
                int(qs.get("phase", ["1"])[0])
            )

        elif path == "/api/file":
            self._api_file(
                qs.get("project", ["chain_clarity"])[0],
                int(qs.get("phase", ["1"])[0]),
                qs.get("file", ["script.md"])[0]
            )

        elif path.startswith("/api/jobs/") and path.endswith("/stream"):
            job_id = path.split("/")[3]
            self._stream_job(job_id)

        elif path.startswith("/api/jobs/"):
            job_id = path.split("/")[3]
            self._api_job_status(job_id)

        elif re.match(r"^/api/projects/[^/]+/runs$", path):
            slug = path.split("/")[3]
            self._api_runs(slug)

        elif path == "/api/db-status":
            self._send_json({"available": db_available()})

        elif path == "/api/file-versions":
            self._api_file_versions(
                qs.get("project", ["chain_clarity"])[0],
                int(qs.get("phase", ["1"])[0]),
                qs.get("step", [""])[0],
            )

        elif path == "/api/db-summary":
            self._api_db_summary()

        elif path == "/api/db-sync":
            self._api_db_sync(qs.get("brand", [""])[0])

        elif path == "/api/tools-status":
            self._api_tools_status()

        elif path == "/api/browse":
            self._api_browse(
                qs.get("project", [""])[0],
                qs.get("phase",   ["0"])[0]
            )

        elif path == "/api/output-text":
            self._api_output_text(
                qs.get("project", ["chain_clarity"])[0],
                int(qs.get("phase", ["1"])[0]),
                qs.get("path", [""])[0]
            )

        else:
            target = BASE_DIR / path.lstrip("/")
            if target.exists() and target.is_file():
                ct_map = {".js": "application/javascript", ".css": "text/css",
                          ".json": "application/json", ".html": "text/html",
                          ".png": "image/png", ".jpg": "image/jpeg",
                          ".mp4": "video/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav"}
                ct = ct_map.get(target.suffix, "text/plain")
                self._serve_file(target, ct)
            else:
                self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/brands":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
            self._api_create_brand(data)
        elif re.match(r"^/api/brands/[^/]+$", path):
            slug = path.split("/")[3]
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
            self._api_update_brand(slug, data)
        elif path == "/api/run":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
            self._api_run(data)
        elif path == "/api/save-file":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
            self._api_save_file(data)
        elif path == "/api/upload-audio":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            import cgi as _cgi
            # Parse multipart form data
            ctype = self.headers.get("Content-Type", "")
            env = {"REQUEST_METHOD": "POST", "CONTENT_TYPE": ctype, "CONTENT_LENGTH": str(length)}
            fs = _cgi.FieldStorage(fp=__import__('io').BytesIO(body), environ=env, keep_blank_values=True)
            project  = fs.getvalue("project", "")
            phase    = int(fs.getvalue("phase", "1"))
            filename = fs.getvalue("filename", "") or "phase_manual.mp3"
            if not project:
                self._send_json({"error": "project required"}, 400); return
            if any(c in filename for c in ("../", "..\\", "/", "\\")):
                self._send_json({"error": "invalid filename"}, 400); return
            audio_item = fs["audio"] if "audio" in fs else None
            if audio_item is None:
                self._send_json({"error": "audio field missing"}, 400); return
            vo_dir = PROJECT_ROOT / project / f"phase_{phase}" / "voiceover"
            vo_dir.mkdir(parents=True, exist_ok=True)
            out_path = vo_dir / filename
            out_path.write_bytes(audio_item.file.read())
            size_mb = round(out_path.stat().st_size / 1024 / 1024, 2)
            print(f"  [AUDIO] Uploaded: {project}/phase_{phase}/voiceover/{filename} ({size_mb} MB)")
            self._send_json({"ok": True, "path": str(out_path), "size_mb": size_mb,
                             "url": f"/media/{project}/{phase}/voiceover/{filename}"})
        elif path == "/api/create-phase":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body) if body else {}
            self._api_create_phase(data)
        elif path == "/api/publish":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body) if body else {}
            self._api_publish(data)
        elif path == "/api/log-view":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body) if body else {}
            self._api_log_view(data)
        elif path == "/api/upload-clip":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            import cgi as _cgi
            ctype = self.headers.get("Content-Type", "")
            env = {"REQUEST_METHOD": "POST", "CONTENT_TYPE": ctype, "CONTENT_LENGTH": str(length)}
            fs = _cgi.FieldStorage(fp=__import__('io').BytesIO(body), environ=env, keep_blank_values=True)
            project  = fs.getvalue("project", "")
            phase    = int(fs.getvalue("phase", "1"))
            filename = fs.getvalue("filename", "") or "clip.mp4"
            if not project:
                self._send_json({"error": "project required"}, 400); return
            if any(c in filename for c in ("../", "..\\", "/", "\\")):
                self._send_json({"error": "invalid filename"}, 400); return
            video_item = fs["video"] if "video" in fs else None
            if video_item is None:
                self._send_json({"error": "video field missing"}, 400); return
            clips_dir = PROJECT_ROOT / project / f"phase_{phase}" / "clips"
            clips_dir.mkdir(parents=True, exist_ok=True)
            out_path = clips_dir / filename
            out_path.write_bytes(video_item.file.read())
            size_mb = round(out_path.stat().st_size / 1024 / 1024, 2)
            print(f"  [CLIP] Uploaded: {project}/phase_{phase}/clips/{filename} ({size_mb} MB)")
            self._send_json({"ok": True, "path": str(out_path), "size_mb": size_mb,
                             "url": f"/media/{project}/{phase}/clips/{filename}"})
        elif path == "/api/run-step":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
            self._api_run_step(data)
        else:
            self._send_json({"error": "not found"}, 404)

    # ── helpers ────────────────────────────────────────────────────────────

    def _serve_file(self, path: Path, content_type: str):
        try:
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            print(f"[serve_file] {e}")

    def _send_json(self, data, status: int = 200):
        body = json.dumps(data).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _send_sse(self, data: dict):
        msg = f"data: {json.dumps(data)}\n\n".encode()
        try:
            self.wfile.write(msg)
            self.wfile.flush()
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass

    # ── API handlers ───────────────────────────────────────────────────────

    def _api_projects(self):
        projects = []
        if PROJECT_ROOT.exists():
            for p in sorted(PROJECT_ROOT.iterdir()):
                if p.is_dir() and not p.name.startswith("_"):
                    phases = sorted([
                        d.name for d in p.iterdir()
                        if d.is_dir() and d.name.startswith("phase_")
                    ])
                    projects.append({"name": p.name, "phases": phases})
        self._send_json(projects)

    def _api_run(self, data: dict):
        job_id = uuid.uuid4().hex[:8]
        cmd = build_pipeline_cmd(data)
        q: queue.Queue = queue.Queue()
        jobs[job_id] = {"status": "running", "output": [], "q": q, "cmd": cmd}
        print(f"  [JOB {job_id}] {' '.join(cmd)}")

        brand_slug = data.get("project", "")
        phase_num  = int(data.get("phase", 0))
        create_run(job_id, brand_slug, phase_num, data)

        def worker():
            env = os.environ.copy()
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(BASE_DIR),
                env=env,
            )
            for line in proc.stdout:
                jobs[job_id]["output"].append(line)
                q.put(line)
            proc.wait()
            final_status = "done" if proc.returncode == 0 else "failed"
            jobs[job_id]["status"] = final_status
            jobs[job_id]["returncode"] = proc.returncode
            finish_run(job_id, final_status)
            q.put(None)
            print(f"  [JOB {job_id}] finished — {final_status}")

        threading.Thread(target=worker, daemon=True).start()
        self._send_json({"job_id": job_id, "cmd": " ".join(cmd)})

    def _stream_job(self, job_id: str):
        if job_id not in jobs:
            self._send_json({"error": "job not found"}, 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self._cors_headers()
        self.end_headers()

        # Replay buffered output for late-connecting clients
        for line in list(jobs[job_id]["output"]):
            self._send_sse({"line": line})

        if jobs[job_id]["status"] != "running":
            self._send_sse({"done": True, "status": jobs[job_id]["status"]})
            return

        q = jobs[job_id]["q"]
        while True:
            try:
                line = q.get(timeout=30)
            except queue.Empty:
                self._send_sse({"ping": True})  # keep-alive
                continue
            if line is None:
                self._send_sse({"done": True, "status": jobs[job_id]["status"]})
                break
            self._send_sse({"line": line})

    def _api_brands(self):
        brands = []
        if PROJECT_ROOT.exists():
            for p in sorted(PROJECT_ROOT.iterdir()):
                if p.is_dir() and not p.name.startswith("_"):
                    bp = p / "brand_profile.json"
                    if bp.exists():
                        try:
                            profile = json.loads(bp.read_text(encoding="utf-8"))
                            phases = sorted([
                                d.name for d in p.iterdir()
                                if d.is_dir() and d.name.startswith("phase_")
                            ])
                            profile["_slug"] = p.name
                            profile["_phases"] = len(phases)
                            brands.append(profile)
                        except Exception:
                            pass
                    else:
                        brands.append({"_slug": p.name, "brand_name": p.name, "_phases": 0})
        self._send_json(brands)

    def _api_brand(self, slug: str):
        bp = PROJECT_ROOT / slug / "brand_profile.json"
        if not bp.exists():
            self._send_json({"error": "brand not found"}, 404)
            return
        try:
            profile = json.loads(bp.read_text(encoding="utf-8"))
            profile["_slug"] = slug
            self._send_json(profile)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _api_create_brand(self, data: dict):
        slug = data.get("brand_slug", "").strip().replace(" ", "_")
        if not slug:
            self._send_json({"error": "brand_slug required"}, 400)
            return
        try:
            proj_dir = scaffold_brand(data, quiet=True)
            print(f"  [BRAND] Scaffolded: {slug} -> {proj_dir}")
            self._send_json({"ok": True, "slug": slug, "path": str(proj_dir)})
        except Exception as e:
            print(f"  [BRAND ERROR] {e}")
            self._send_json({"error": str(e)}, 500)

    def _api_runs(self, slug: str):
        runs = list_runs(slug)
        self._send_json(runs)

    def _api_update_brand(self, slug: str, data: dict):
        proj_dir = PROJECT_ROOT / slug
        if not proj_dir.exists():
            self._send_json({"error": "brand not found"}, 404)
            return
        bp = proj_dir / "brand_profile.json"
        # Merge with existing to preserve unedited fields
        existing = {}
        if bp.exists():
            try: existing = json.loads(bp.read_text(encoding="utf-8"))
            except Exception: pass
        existing.update(data)
        bp.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [BRAND] Updated: {slug}")
        self._send_json({"ok": True, "slug": slug})

    def _api_save_file(self, data: dict):
        project  = data.get("project", "").strip()
        phase    = int(data.get("phase", 1))
        filename = data.get("filename", "").strip()
        content  = data.get("content", "")

        if not project or not filename:
            self._send_json({"error": "project and filename required"}, 400)
            return
        if any(c in filename for c in ("../", "..\\", "/", "\\")):
            self._send_json({"error": "invalid filename"}, 400)
            return

        phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
        phase_dir.mkdir(parents=True, exist_ok=True)

        file_path = phase_dir / filename
        file_path.write_text(content, encoding="utf-8")
        print(f"  [SAVE] {project}/phase_{phase}/{filename} ({len(content)} chars)")
        # Track in DB (best-effort)
        try:
            from db.db import record_file, is_available as _dbok
            if _dbok():
                record_file(project, phase, file_path.suffix.lstrip("."),
                            filename, len(content.encode()), None)
        except Exception:
            pass
        self._send_json({"ok": True, "path": str(file_path), "size": len(content)})

    def _api_project_summary(self, project: str):
        proj_dir = PROJECT_ROOT / project
        if not proj_dir.exists():
            self._send_json({"error": "not found"}, 404)
            return

        phases = sorted([
            d.name for d in proj_dir.iterdir()
            if d.is_dir() and d.name.startswith("phase_")
        ])

        total_done, total_steps_all, phase_summaries = 0, 0, []

        # Pre-load roadmap for topic lookup
        _topic_map = {}
        _rm = proj_dir / "roadmap.json"
        if _rm.exists():
            try:
                _rm_data = json.loads(_rm.read_text(encoding="utf-8"))
                for _p in _rm_data.get("phases", []):
                    _topic_map[_p["phase"]] = _p.get("title", "")
            except Exception:
                pass

        for ph_name in phases:
            phase_num = int(ph_name.replace("phase_", ""))
            phase_dir = proj_dir / ph_name

            files = [
                {"name": f.name, "size": f.stat().st_size, "ext": f.suffix}
                for f in sorted(phase_dir.iterdir()) if f.is_file()
            ]
            cards, output_files = [], []
            ia_dir = phase_dir / "infographic_assets"
            if ia_dir.exists():
                cards = [f.name for f in sorted(ia_dir.iterdir()) if f.suffix == ".html"]
            out_dir = proj_dir / "_output" / f"phase_{phase_num:02d}"
            if out_dir.exists():
                output_files = [str(f.relative_to(out_dir)) for f in out_dir.rglob("*") if f.is_file()]

            steps = self._pipeline_steps(phase_dir, files, cards, output_files,
                                         project=project, phase=phase_num,
                                         topic=_topic_map.get(phase_num, ""))
            done = sum(1 for s in steps if s["done"])
            total_done += done
            total_steps_all += len(steps)

            compliance = "unknown"
            cr = phase_dir / "compliance_report_auto.md"
            if cr.exists():
                txt = cr.read_text(encoding="utf-8", errors="replace")[:400]
                compliance = (
                    "PASS_WITH_WARNINGS" if "PASS WITH WARNINGS" in txt or "PASS_WITH_WARNINGS" in txt
                    else "PASS" if "PASS" in txt
                    else "FAIL" if "FAIL" in txt
                    else "unknown"
                )

            title = f"Phase {phase_num}"
            spec_path = phase_dir / "content_spec.json"
            if spec_path.exists():
                try:
                    spec = json.loads(spec_path.read_text(encoding="utf-8"))
                    title = spec.get("title", title)
                except Exception:
                    pass

            # last modified (max mtime of source files)
            mtimes = [f.stat().st_mtime for f in phase_dir.iterdir() if f.is_file()]
            last_mod = int(max(mtimes)) if mtimes else 0

            phase_summaries.append({
                "phase": phase_num, "title": title,
                "compliance_status": compliance,
                "file_count": len(files), "card_count": len(cards),
                "steps_done": done, "steps_total": len(steps),
                "last_modified": last_mod,
            })

        self._send_json({
            "name": project,
            "phase_count": len(phases),
            "total_steps_done": total_done,
            "total_steps": total_steps_all,
            "completion_pct": round(total_done / total_steps_all * 100) if total_steps_all else 0,
            "phases": phase_summaries,
        })

    def _serve_media(self, project: str, phase: int, subpath: str):
        if ".." in subpath:
            self._send_json({"error": "invalid path"}, 400)
            return
        phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
        candidates = [
            phase_dir / subpath,
            PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}" / subpath,
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                ct_map = {".mp4": "video/mp4", ".mp3": "audio/mpeg",
                          ".wav": "audio/wav", ".ogg": "audio/ogg", ".webm": "video/webm"}
                self._serve_file(p, ct_map.get(p.suffix.lower(), "application/octet-stream"))
                return
        self._send_json({"error": "media not found"}, 404)

    def _pipeline_steps(self, phase_dir: Path, files: list, cards: list, output_files: list,
                        project: str = "", phase: int = 0,
                        topic: str = "", outline: str = "") -> list:
        file_set   = {f["name"] for f in files}
        out_set    = set(output_files)
        file_sizes = {f["name"]: f["size"] for f in files}

        def has(name):   return name in file_set
        def sz(name):    return file_sizes.get(name, 0)
        def out_has(k):  return any(k in f for f in out_set)

        vo_dir = phase_dir / "voiceover"
        has_vo = vo_dir.exists() and any(
            f.suffix in (".wav", ".mp3", ".ogg") for f in vo_dir.iterdir()
        ) if vo_dir.exists() else False

        proj = project or "chain_clarity"
        ph   = phase   or 1
        t    = topic   or "YOUR_TOPIC_HERE"
        ol   = outline or "key concept 1, key concept 2, key concept 3"

        def _gp(only="", extra_outline=False):
            cmd = f'python tools/generate_phase.py --project {proj} --phase {ph} --topic "{t}"'
            if extra_outline:
                cmd += f' --outline "{ol}"'
            if only:
                cmd += f' --only {only}'
            return cmd

        # ── Step 1 sub-steps ──────────────────────────────────────────────────
        substeps = [
            {"id": "1_1", "num": "1.1", "name": "Main Script",
             "file": "script.md", "done": has("script.md") and sz("script.md") > 1000,
             "needs": "topic + outline  (seed for all other files)",
             "cmd":      f'python tools/generate_phase.py --project {proj} --phase {ph} --topic "{t}" --outline "{ol}" --only script.md',
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": ol, "only": "script.md"}},

            {"id": "1_2", "num": "1.2", "name": "Short Script (60 s)",
             "file": "script_short.md", "done": has("script_short.md"),
             "needs": "script.md",
             "cmd":      _gp("script_short.md"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "script_short.md"}},

            {"id": "1_3", "num": "1.3", "name": "Subtitles (SRT)",
             "file": "subtitles.srt", "done": has("subtitles.srt") and sz("subtitles.srt") > 100,
             "needs": "script.md",
             "cmd":      _gp("subtitles.srt"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "subtitles.srt"}},

            {"id": "1_4", "num": "1.4", "name": "Voiceover Brief",
             "file": "voiceover_brief.md", "done": has("voiceover_brief.md"),
             "needs": "script.md",
             "cmd":      _gp("voiceover_brief.md"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "voiceover_brief.md"}},

            {"id": "1_5", "num": "1.5", "name": "Music Brief",
             "file": "music_brief.md", "done": has("music_brief.md"),
             "needs": "topic only",
             "cmd":      _gp("music_brief.md"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "music_brief.md"}},

            {"id": "1_6", "num": "1.6", "name": "Infographics Brief",
             "file": "infographics.md", "done": has("infographics.md"),
             "needs": "script.md",
             "cmd":      _gp("infographics.md"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "infographics.md"}},

            {"id": "1_7", "num": "1.7", "name": "Clip Brief",
             "file": "clip_brief.md", "done": has("clip_brief.md"),
             "needs": "script.md",
             "cmd":      _gp("clip_brief.md"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "clip_brief.md"}},

            {"id": "1_8", "num": "1.8", "name": "Infographic Cards (×3)",
             "file": "card_01.html", "done": len(cards) > 0,
             "needs": "infographics.md",
             "cmd":      _gp("card_01.html"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "card_01.html"}},

            {"id": "1_9", "num": "1.9", "name": "Content Spec",
             "file": "content_spec.json", "done": has("content_spec.json"),
             "needs": "script.md",
             "cmd":      _gp("content_spec.json"),
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": "", "only": "content_spec.json"}},
        ]

        return [
            {"num": 1, "name": "Script Generation",
             "done": all(s["done"] for s in substeps),
             "key_files": ["script.md", "script_short.md", "voiceover_brief.md", "clip_brief.md"],
             "action": "view:script.md",
             "cmd": f'python tools/generate_phase.py --project {proj} --phase {ph} --topic "{t}" --outline "{ol}"',
             "run_data": {"project": proj, "phase": ph, "topic": t, "outline": ol},
             "substeps": substeps},

            {"num": 2, "name": "Compliance Check",
             "done": has("compliance_report_auto.md"),
             "key_files": ["compliance_report_auto.md"],
             "action": "view:compliance_report_auto.md",
             "cmd": f'python tools/compliance_checker.py --project {proj} --phase {ph}'},

            {"num": 3, "name": "TTS / Voiceover",
             "done": has_vo,
             "key_files": ["voiceover/"],
             "action": "run:voiceover",
             "cmd": f'python tools/tts/kokoro_voiceover.py --project {proj} --phase {ph}'},

            {"num": 4, "name": "Infographic Cards",
             "done": len(cards) > 0,
             "key_files": cards[:3],
             "action": "tab:infographics",
             "cmd": f'# Cards generated in Step 1.8 above\n# python tools/generate_phase.py --project {proj} --phase {ph} --topic "{t}" --only card_01.html'},

            {"num": 5, "name": "Video Assembly",
             "done": out_has(".mp4"),
             "key_files": ["_output/youtube/final_1080p.mp4"],
             "action": "run:video",
             "cmd": f'# From infographic cards + voiceover (no raw footage needed):\npython tools/video/create_video.py --project {proj} --phase {ph} --burn-subs --shorts\n\n# OR from raw screen recording:\npython pipeline.py --project {proj} --phase {ph} --skip-generate --video path/to/recording.mp4'},

            {"num": 6, "name": "Auto-Transcribe (SRT)",
             "done": has("subtitles.srt") and sz("subtitles.srt") > 500,
             "key_files": ["subtitles.srt"],
             "action": "view:subtitles.srt",
             "cmd": f'# AI-generated in Step 1.3:\n# python tools/generate_phase.py --project {proj} --phase {ph} --topic "{t}" --only subtitles.srt'},

            {"num": 7, "name": "Platform Cuts",
             "done": out_has("tiktok"),
             "key_files": ["_output/tiktok/", "_output/instagram/", "_output/twitter/"],
             "action": "run:cuts",
             "cmd": f'python tools/platform_cutter.py --project {proj} --phase {ph} --video _output/phase_{ph:02d}/youtube/final_1080p.mp4'},

            {"num": 8, "name": "Text Content",
             "done": out_has("blog"),
             "key_files": ["_output/blog/post.md", "_output/twitter/thread.txt", "_output/linkedin/article.md"],
             "action": "run:text",
             "cmd": f'python tools/text_content_generator.py --project {proj} --phase {ph}'},

            {"num": 9, "name": "Publish Checklist",
             "done": out_has("PIPELINE_SUMMARY"),
             "key_files": ["_output/PIPELINE_SUMMARY.md"],
             "action": "run:publish",
             "cmd": f'python pipeline.py --project {proj} --phase {ph} --skip-generate --skip-voiceover --skip-remotion'},
        ]

    # ── Production brief helpers ─────────────────────────────────────────────

    @staticmethod
    def _analyze_script(path: Path) -> dict:
        if not path.exists():
            return {}
        text = path.read_text(encoding="utf-8", errors="replace")
        words      = len(text.split())
        sections   = re.findall(r'^##\s+(.+)', text, re.MULTILINE)
        # Extract spoken-only word count (NARRATION: blocks)
        spoken_lines, in_spoken = [], False
        for line in text.split("\n"):
            s = line.strip()
            if re.match(r'^(NARRATION|SPOKEN)\s*:', s, re.IGNORECASE):
                in_spoken = True
                continue
            if re.match(r'^#{1,4}\s', s) or s.startswith("[") or s.startswith("ON-SCREEN"):
                in_spoken = False; continue
            if in_spoken and s:
                spoken_lines.append(s)
        spoken_words = len(" ".join(spoken_lines).split())
        # Key concepts: bold text phrases
        concepts = list(dict.fromkeys(re.findall(r'\*\*([^*]{3,40})\*\*', text)))[:10]
        return {
            "word_count":           words,
            "spoken_word_count":    spoken_words,
            "section_count":        len(sections),
            "sections":             sections[:10],
            "estimated_duration_min": round(spoken_words / 150, 1) if spoken_words else round(words / 150, 1),
            "key_concepts":         concepts,
        }

    @staticmethod
    def _analyze_infographics(path: Path) -> dict:
        if not path.exists():
            return {"total": 0, "cards": []}
        text = path.read_text(encoding="utf-8", errors="replace")
        # Match "Card N: Title" or "### Card N — Title"
        matches = re.findall(r'(?:###?\s*)?Card\s+(\d+)\s*[:\-—]+\s*(.+)', text, re.IGNORECASE)
        cards = [{"num": int(n), "title": t.strip()} for n, t in matches]
        # Deduplicate by card number
        seen, unique = set(), []
        for c in cards:
            if c["num"] not in seen:
                seen.add(c["num"]); unique.append(c)
        return {"total": len(unique) or max(3, len(re.findall(r'Card\s+\d+', text, re.IGNORECASE))),
                "cards": unique}

    @staticmethod
    def _analyze_music(path: Path) -> dict:
        if not path.exists():
            return {}
        text = path.read_text(encoding="utf-8", errors="replace")
        bpm_match = re.search(r'(\d{2,3})\s*[-–]\s*(\d{2,3})\s*BPM', text, re.IGNORECASE)
        moods     = re.findall(r'(?:mood|feel)[^\n]*:\s*([^\n]+)', text, re.IGNORECASE)
        searches  = re.findall(r'"([^"]{5,60})"', text)[:5]
        return {
            "bpm":          f"{bpm_match.group(1)}-{bpm_match.group(2)}" if bpm_match else "",
            "mood":         moods[0].strip() if moods else "",
            "search_terms": searches,
        }

    @staticmethod
    def _parse_srt_segments(srt_path: Path) -> list:
        """Parse subtitles.srt → list of {index, ts, text} for the Audio tab preview."""
        if not srt_path.exists():
            return []
        try:
            raw    = srt_path.read_text(encoding="utf-8", errors="replace")
            blocks = re.split(r'\n{2,}', raw.strip())
            segs   = []
            for block in blocks:
                lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
                if len(lines) < 3 or not lines[0].isdigit() or "-->" not in lines[1]:
                    continue
                segs.append({
                    "index": int(lines[0]),
                    "ts":    lines[1],
                    "text":  " ".join(lines[2:]),
                })
            return segs[:200]          # cap to avoid large payloads
        except Exception:
            return []

    @staticmethod
    def _analyze_voiceover(vo_dir: Path) -> dict:
        if not vo_dir.exists():
            return {"exists": False}
        audio = [f for f in sorted(vo_dir.iterdir())
                 if f.suffix.lower() in (".wav", ".mp3", ".ogg", ".m4a")]
        if not audio:
            return {"exists": False}
        f = audio[0]
        size_mb = round(f.stat().st_size / 1024 / 1024, 2)
        # Try ffprobe for duration
        dur_s = 0.0
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(f)],
                capture_output=True, text=True, timeout=10)
            dur_s = float(r.stdout.strip())
        except Exception:
            pass
        mins, secs = divmod(int(dur_s), 60)
        return {
            "exists":    True,
            "filename":  f.name,
            "size_mb":   size_mb,
            "duration_s": dur_s,
            "duration_display": f"{mins}m {secs:02d}s" if dur_s else "",
        }

    def _api_phase_data(self, project: str, phase: int):
        phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
        if not phase_dir.exists():
            # Auto-scaffold so the dashboard can show an empty pipeline with editors
            phase_dir.mkdir(parents=True, exist_ok=True)
            print(f"  [PHASE] Auto-created: {project}/phase_{phase}")

        files = []
        for f in sorted(phase_dir.iterdir()):
            if f.is_file():
                files.append({"name": f.name, "size": f.stat().st_size, "ext": f.suffix})

        spec, compliance_status = {}, "unknown"

        spec_path = phase_dir / "content_spec.json"
        if spec_path.exists():
            spec = json.loads(spec_path.read_text(encoding="utf-8"))

        cr_path = phase_dir / "compliance_report_auto.md"
        if cr_path.exists():
            cr_text = cr_path.read_text(encoding="utf-8")[:600]
            if "PASS WITH WARNINGS" in cr_text or "PASS_WITH_WARNINGS" in cr_text:
                compliance_status = "PASS_WITH_WARNINGS"
            elif "PASS" in cr_text:
                compliance_status = "PASS"
            elif "FAIL" in cr_text:
                compliance_status = "FAIL"

        cards = []
        card_urls = {}
        cards_manifest = {}
        ia_dir = phase_dir / "infographic_assets"
        if ia_dir.exists():
            cards = [f.name for f in sorted(ia_dir.iterdir()) if f.suffix == ".html"]
            card_urls = {
                c: {
                    "url":      f"/media/{project}/{phase}/infographic_assets/{c}",
                    "filename": c,
                    "size":     (ia_dir / c).stat().st_size if (ia_dir / c).exists() else 0,
                }
                for c in cards
            }
            cm = ia_dir / "cards_manifest.json"
            if cm.exists():
                try:
                    cards_manifest = json.loads(cm.read_text(encoding="utf-8"))
                except Exception:
                    pass

        # Production brief analyses
        script_analysis      = self._analyze_script(phase_dir / "script.md")
        infographics_analysis= self._analyze_infographics(phase_dir / "infographics.md")
        music_analysis       = self._analyze_music(phase_dir / "music_brief.md")

        # Voiceover audio files
        voiceover_files = []
        vo_dir = phase_dir / "voiceover"
        if vo_dir.exists():
            for f in sorted(vo_dir.iterdir()):
                if f.suffix.lower() in (".wav", ".mp3", ".ogg", ".m4a", ".flac"):
                    voiceover_files.append({
                        "name":    f.name,
                        "url":     f"/media/{project}/{phase}/voiceover/{f.name}",
                        "size":    f.stat().st_size,
                        "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
                        "ext":     f.suffix.lower().lstrip("."),
                    })

        # Raw clips in phase_N/clips/
        clips = []
        clips_dir = phase_dir / "clips"
        if clips_dir.exists():
            for f in sorted(clips_dir.iterdir()):
                if f.suffix.lower() in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
                    clips.append({
                        "name":    f.name,
                        "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
                        "url":     f"/media/{project}/{phase}/clips/{f.name}",
                    })

        output_dir = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}"
        output_files = []
        if output_dir.exists():
            for f in sorted(output_dir.rglob("*")):
                if f.is_file():
                    output_files.append(str(f.relative_to(output_dir)))

        # Platform outputs — structured by platform for the Outputs tab
        _PLATFORMS = [
            ("youtube",        "YouTube",           "▶️"),
            ("youtube_shorts", "YouTube Shorts",    "📱"),
            ("tiktok",         "TikTok",            "🎵"),
            ("instagram",      "Instagram",         "📸"),
            ("twitter",        "Twitter / X",       "🐦"),
            ("linkedin",       "LinkedIn",          "💼"),
            ("blog",           "Blog",              "📝"),
            ("github",         "GitHub",            "🐙"),
        ]
        platform_outputs = {}
        for pd_slug, pd_label, pd_icon in _PLATFORMS:
            pd_dir  = output_dir / pd_slug
            pfiles  = []                           # renamed: was 'files', shadowed outer files
            if pd_dir.exists():
                for f in sorted(pd_dir.rglob("*")):
                    if f.is_file():
                        rel  = str(f.relative_to(output_dir)).replace("\\", "/")
                        ext  = f.suffix.lower()
                        fsz  = f.stat().st_size
                        pfiles.append({
                            "name":      f.name,
                            "path":      rel,
                            "size_mb":   round(fsz / 1024 / 1024, 2),
                            "ext":       ext.lstrip("."),
                            "is_video":  ext in (".mp4", ".webm", ".mov"),
                            "is_text":   ext in (".txt", ".md", ".html"),
                            "media_url": f"/media/{project}/{phase}/{rel}",
                        })
            platform_outputs[pd_slug] = {
                "label":       pd_label,
                "icon":        pd_icon,
                "files":       pfiles,
                "has_content": len(pfiles) > 0,
            }

        # Brand profile + roadmap (loaded before pipeline steps — needed for CMD strings)
        brand_profile = {}
        bp_path = PROJECT_ROOT / project / "brand_profile.json"
        if bp_path.exists():
            try:
                brand_profile = json.loads(bp_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        roadmap_phase = {}
        rm_path = PROJECT_ROOT / project / "roadmap.json"
        if rm_path.exists():
            try:
                rm_data = json.loads(rm_path.read_text(encoding="utf-8"))
                for ph_entry in rm_data.get("phases", []):
                    if ph_entry.get("phase") == phase:
                        roadmap_phase = ph_entry
                        break
            except Exception:
                pass

        phase_topic   = roadmap_phase.get("title", spec.get("title", ""))
        phase_outline = ", ".join(roadmap_phase.get("learning_goals", [])[:3])

        # Video type preference
        video_type = "broll"
        vt_path = phase_dir / "video_type.json"
        if vt_path.exists():
            try:
                video_type = json.loads(vt_path.read_text(encoding="utf-8")).get("video_type", "broll")
            except Exception:
                pass

        steps = self._pipeline_steps(phase_dir, files, cards, output_files,
                                     project=project, phase=phase,
                                     topic=phase_topic, outline=phase_outline)
        done_count = sum(1 for s in steps if s["done"])

        self._send_json({
            "project": project,
            "phase": phase,
            "title": spec.get("title", roadmap_phase.get("title", f"Phase {phase}")),
            "status": spec.get("status", "unknown"),
            "duration_min": spec.get("duration_min", 12),
            "tags": spec.get("tags", []),
            "youtube": spec.get("youtube", {}),
            "platform_cuts": spec.get("platform_cuts", {}),
            "files": files,
            "cards": cards,
            "card_urls": card_urls,
            "cards_manifest": cards_manifest,
            "compliance_status": compliance_status,
            "output_files": output_files,
            "pipeline_steps": steps,
            "steps_done": done_count,
            "steps_total": len(steps),
            "voiceover_files": voiceover_files,
            "clips": clips,
            "voiceover_analysis": self._analyze_voiceover(vo_dir),
            "srt_segments":       self._parse_srt_segments(phase_dir / "subtitles.srt"),
            "script_analysis":    script_analysis,
            "infographics_analysis": infographics_analysis,
            "music_analysis":     music_analysis,
            "platform_outputs": platform_outputs,
            "video_type": video_type,
            "brand": brand_profile,
            "roadmap_phase": roadmap_phase,
            "step_versions": _scan_step_versions(phase_dir, output_dir),
            "view_counts":   self._get_view_counts(project, phase),
        })

    def _api_file(self, project: str, phase: int, filename: str):
        # Prevent path traversal
        if any(c in filename for c in ("../", "..\\", "/", "\\")):
            self._send_json({"error": "invalid filename"}, 400)
            return

        phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
        # Also support infographic_assets subfolder
        if filename.endswith(".html"):
            candidate = phase_dir / "infographic_assets" / filename
            if candidate.exists():
                content = candidate.read_text(encoding="utf-8", errors="replace")
                self._send_json({"content": content, "type": "html", "filename": filename})
                return

        file_path = phase_dir / filename
        if not file_path.exists():
            self._send_json({"error": "file not found"}, 404)
            return
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            ftype = "json" if filename.endswith(".json") else "srt" if filename.endswith(".srt") else "text"
            self._send_json({"content": content, "type": ftype, "filename": filename})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _api_browse(self, project: str, phase_str: str):
        """Return a directory tree for a project (and optionally a phase)."""
        phase = int(phase_str) if phase_str and phase_str.isdigit() else 0
        base = (PROJECT_ROOT / project / f"phase_{phase}") if phase else (PROJECT_ROOT / project)
        if not base.exists():
            self._send_json({"error": "not found"}, 404); return

        SKIP = {"__pycache__", ".git", "node_modules", ".venv"}
        MAX_DEPTH = 3

        def _tree(d: Path, depth: int = 0) -> list:
            if depth >= MAX_DEPTH:
                return []
            items = []
            try:
                entries = sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            except PermissionError:
                return []
            for f in entries:
                if f.name.startswith(".") or f.name in SKIP:
                    continue
                rel = str(f.relative_to(base)).replace("\\", "/")
                if f.is_dir():
                    items.append({"name": f.name, "type": "dir", "path": rel,
                                  "children": _tree(f, depth + 1)})
                else:
                    items.append({"name": f.name, "type": "file", "path": rel,
                                  "size": f.stat().st_size, "ext": f.suffix.lstrip(".")})
            return items

        self._send_json({
            "project": project, "phase": phase,
            "base":    str(base), "tree": _tree(base)
        })

    def _api_db_summary(self):
        try:
            from db.db import get_db_summary
            self._send_json({"available": True, "tables": get_db_summary()})
        except Exception as e:
            self._send_json({"available": False, "error": str(e)})

    def _api_db_sync(self, brand: str = ""):
        try:
            sys.path.insert(0, str(BASE_DIR))
            from db.sync import sync_brand, sync_all
            if brand:
                result = sync_brand(brand)
            else:
                result = sync_all()
            self._send_json({"ok": True, "result": result})
        except Exception as e:
            print(f"  [DB SYNC ERROR] {e}")
            self._send_json({"ok": False, "error": str(e)})

    def _api_file_versions(self, project: str, phase: int, step_key: str = ""):
        """Return all versioned snapshots for a project/phase (optionally one step)."""
        phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
        out_dir   = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}"

        # Filesystem versions (.versions/ dir)
        fs_versions = _scan_step_versions(phase_dir, out_dir)

        # DB versions (best-effort)
        db_versions: dict = {}
        try:
            from db.db import list_asset_versions, is_available as _dbok
            if _dbok():
                rows = list_asset_versions(project, phase, step_key or None)
                for row in rows:
                    sk = row["step_key"]
                    if sk not in db_versions:
                        db_versions[sk] = {}
                    vnum = row["version"]
                    if vnum not in db_versions[sk]:
                        db_versions[sk][vnum] = {
                            "version": vnum,
                            "label":   f"v{vnum}",
                            "ts":      int(row["created_at"].timestamp()) if row.get("created_at") else 0,
                            "files":   [],
                        }
                    db_versions[sk][vnum]["files"].append({
                        "name":     row["file_name"],
                        "path":     row["file_path"],
                        "media_url": row["media_url"],
                        "size_mb":  round((row.get("file_size") or 0) / 1024 / 1024, 2),
                    })
        except Exception as e:
            print(f"  [VERSION] DB read: {e}")

        # Merge fs + db (fs is source of truth; db adds media_url)
        if step_key:
            result = {step_key: fs_versions.get(step_key, [])}
        else:
            result = fs_versions

        self._send_json({
            "project": project, "phase": phase,
            "versions": result,
            "db_versions": {sk: list(v.values())
                            for sk, v in db_versions.items()},
        })

    def _api_output_text(self, project: str, phase: int, filepath: str):
        if ".." in filepath or filepath.startswith("/"):
            self._send_json({"error": "invalid path"}, 400); return
        f = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}" / filepath
        if not f.exists():
            self._send_json({"error": "file not found"}, 404); return
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            self._send_json({"content": content, "filename": f.name,
                             "size": f.stat().st_size})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _api_tools_status(self):
        def key_set(k): return bool(os.environ.get(k, "").strip())
        status = {
            "script": [
                {"id": "anthropic",  "name": "Claude Sonnet 4.6",  "tier": "primary",
                 "flag": "anthropic",  "pkg": "pip install anthropic",
                 "note": "Best quality · auto-fallback to Gemini",
                 "configured": key_set("ANTHROPIC_API_KEY")},
                {"id": "gemini",     "name": "Gemini 2.5 Flash",   "tier": "fallback",
                 "flag": "gemini",     "pkg": "pip install google-generativeai",
                 "note": "Free tier · auto-used when Anthropic fails",
                 "configured": key_set("GEMINI_API_KEY")},
                {"id": "openai",     "name": "ChatGPT GPT-4o",     "tier": "optional",
                 "flag": "openai",     "pkg": "pip install openai",
                 "note": "Optional · ~$0.03/script",
                 "configured": key_set("OPENAI_API_KEY")},
                {"id": "dashscope",  "name": "Qwen3 (DashScope)",  "tier": "optional",
                 "flag": "dashscope",  "pkg": "pip install dashscope",
                 "note": "Optional · multilingual · Alibaba",
                 "configured": key_set("DASHSCOPE_API_KEY")},
            ],
            "tts": [
                {"id": "chatterbox", "name": "Chatterbox TTS",     "tier": "free",
                 "local": True, "note": "Free · GPU · emotion control · MIT",
                 "configured": True},
                {"id": "kokoro",     "name": "Kokoro TTS",         "tier": "free",
                 "local": True, "note": "Free · CPU · fast · Python <=3.12",
                 "configured": True},
                {"id": "elevenlabs", "name": "ElevenLabs",         "tier": "paid",
                 "pkg": "pip install elevenlabs",
                 "note": "Best quality · voice cloning · ~$0.05/1K chars",
                 "configured": key_set("ELEVENLABS_API_KEY")},
                {"id": "dashscope_tts","name": "Qwen-TTS (DashScope)","tier": "freemium",
                 "pkg": "pip install dashscope",
                 "note": "Freemium · multilingual",
                 "configured": key_set("DASHSCOPE_API_KEY")},
            ],
            "transcription": [
                {"id": "whisper",    "name": "Faster-Whisper",     "tier": "free",
                 "local": True, "note": "Free · local · pip install faster-whisper",
                 "configured": True},
                {"id": "assemblyai", "name": "AssemblyAI",         "tier": "paid",
                 "note": "Paid · auto YouTube chapters · ~$0.03/video",
                 "configured": key_set("ASSEMBLYAI_API_KEY")},
                {"id": "deepgram",   "name": "Deepgram",           "tier": "paid",
                 "note": "Paid · lowest latency",
                 "configured": key_set("DEEPGRAM_API_KEY")},
            ],
            "image": [
                {"id": "bfl",        "name": "FLUX.1 Pro",         "tier": "paid",
                 "note": "~$0.055/image", "configured": key_set("BFL_API_KEY")},
                {"id": "ideogram",   "name": "Ideogram v2",        "tier": "paid",
                 "note": "Best text-in-image · ~$0.08/image",
                 "configured": key_set("IDEOGRAM_API_KEY")},
                {"id": "dalle",      "name": "DALL-E 3 (OpenAI)",  "tier": "paid",
                 "note": "~$0.04/image", "configured": key_set("OPENAI_API_KEY")},
            ],
            "video": [
                {"id": "runway",     "name": "Runway Gen-4",       "tier": "paid",
                 "note": "Cinematic AI b-roll · ~$0.05/sec",
                 "configured": key_set("RUNWAY_API_KEY")},
                {"id": "kling",      "name": "Kling AI",           "tier": "paid",
                 "note": "Best cost/quality · $7.99/mo",
                 "configured": key_set("KLING_API_KEY")},
            ],
        }
        self._send_json(status)

    def _api_publish(self, data: dict):
        """Kick off a social media publish job via publish_platform.py."""
        project  = data.get("project", "").strip()
        phase    = int(data.get("phase", 1))
        platform = data.get("platform", "all").strip()
        dry_run  = bool(data.get("dry_run", False))

        if not project:
            self._send_json({"error": "project required"}, 400)
            return

        job_id = uuid.uuid4().hex[:8]
        cmd = [sys.executable, str(BASE_DIR / "tools" / "publish" / "publish_platform.py"),
               "--project", project, "--phase", str(phase),
               "--platform", platform]
        if dry_run:
            cmd.append("--dry-run")

        q: queue.Queue = queue.Queue()
        jobs[job_id] = {"status": "running", "output": [], "q": q, "cmd": cmd}
        print(f"  [PUBLISH {job_id}] {platform} for {project}/phase_{phase}")

        def worker():
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, cwd=str(BASE_DIR), env=os.environ.copy())
            for line in proc.stdout:
                jobs[job_id]["output"].append(line)
                q.put(line)
            proc.wait()
            final = "done" if proc.returncode == 0 else "failed"
            jobs[job_id]["status"] = final
            q.put(None)
            print(f"  [PUBLISH {job_id}] {final}")

        threading.Thread(target=worker, daemon=True).start()
        self._send_json({"job_id": job_id, "cmd": " ".join(cmd)})

    def _get_view_counts(self, project: str, phase: int) -> dict:
        try:
            from db.db import get_view_counts, is_available as _dbok
            if _dbok():
                return get_view_counts(project, phase)
        except Exception:
            pass
        return {}

    def _api_log_view(self, data: dict):
        """Record a content-view event in PostgreSQL (best-effort)."""
        project   = data.get("project", "").strip()
        phase     = int(data.get("phase", 1))
        action    = data.get("action", "").strip()
        step_name = data.get("step_name", "").strip()
        file_name = action.split(":")[-1] if ":" in action else action
        try:
            from db.db import log_content_view, is_available as _dbok
            if _dbok():
                log_content_view(project, phase, step_name, file_name, action)
        except Exception as e:
            print(f"  [VIEW LOG] {e}")
        self._send_json({"ok": True})

    def _api_create_phase(self, data: dict):
        """Scaffold a new phase directory and register it in the DB.

        POST body: { "project": "ecoWorld", "phase": 7, "topic": "", "tags": "" }
        """
        project  = data.get("project", "").strip()
        phase    = int(data.get("phase", 1))
        topic    = data.get("topic", "").strip()
        tags     = data.get("tags",  "").strip()

        if not project:
            self._send_json({"error": "project required"}, 400)
            return
        if phase < 1 or phase > 999:
            self._send_json({"error": "phase must be 1–999"}, 400)
            return

        phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
        phase_dir.mkdir(parents=True, exist_ok=True)
        # Create output folder too so the dashboard has somewhere to write
        (PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}").mkdir(parents=True, exist_ok=True)

        # Write a minimal placeholder content_spec so the dashboard shows something
        spec_path = phase_dir / "content_spec.json"
        if not spec_path.exists():
            import json as _json2
            spec_path.write_text(_json2.dumps({
                "title":       topic or f"Phase {phase}",
                "status":      "pending",
                "duration_min": 12,
                "tags":        [t.strip() for t in tags.split(",") if t.strip()],
                "youtube":     {},
                "platform_cuts": {},
            }, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"  [PHASE] Scaffolded: {project}/phase_{phase}")

        # ── Persist to DB (best-effort) ──────────────────────────────────────
        db_ok = False
        try:
            from db.db import upsert_brand, upsert_phase, is_available as _db_ok
            if _db_ok():
                # Ensure brand exists in DB before inserting phase (FK)
                bp = PROJECT_ROOT / project / "brand_profile.json"
                if bp.exists():
                    try:
                        upsert_brand(json.loads(bp.read_text(encoding="utf-8")))
                    except Exception:
                        pass
                db_ok = upsert_phase(project, phase, topic, tags)
        except Exception as e:
            print(f"  [PHASE DB] {e}")

        self._send_json({
            "ok":       True,
            "project":  project,
            "phase":    phase,
            "db_saved": db_ok,
            "url":      f"/phase/{project}/{phase}",
        })

    def _api_run_step(self, data: dict):
        """Run a pipeline tool command.

        cmd_type values:
          generate      — generate_phase.py --only <file>  (default)
          create_video  — tools/video/create_video.py
          platform_cut  — tools/platform_cutter.py
          text_content  — tools/text_content_generator.py
          tts           — tools/tts/<engine>_voiceover.py
          compliance    — tools/compliance_checker.py
        """
        job_id   = uuid.uuid4().hex[:8]
        project  = data.get("project", "chain_clarity")
        phase    = int(data.get("phase", 1))
        cmd_type = data.get("cmd_type", "generate")

        if cmd_type == "remotion_compose":
            remotion_out = data.get(
                "remotion_out",
                os.environ.get("REMOTION_OUT_DIR", r"D:\claude_project\LearnRemotion\out")
            )
            cmd = [sys.executable,
                   str(BASE_DIR / "tools" / "video" / "remotion_composer.py"),
                   "--project", project, "--phase", str(phase),
                   "--remotion-out", remotion_out,
                   "--shorts"]
            if data.get("burn_subs"):
                cmd.append("--burn-subs")
            if data.get("keep_audio"):
                cmd.append("--keep-audio")

        elif cmd_type == "create_video":
            cmd = [sys.executable,
                   str(BASE_DIR / "tools" / "video" / "create_video.py"),
                   "--project", project, "--phase", str(phase),
                   "--burn-subs", "--shorts"]

        elif cmd_type == "platform_cut":
            # prefer a specific video path; fall back to the standard output location
            video_path = data.get(
                "video_path",
                str(PROJECT_ROOT / project / "_output"
                    / f"phase_{phase:02d}" / "youtube" / "final_1080p.mp4")
            )
            cmd = [sys.executable, str(BASE_DIR / "tools" / "platform_cutter.py"),
                   "--project", project, "--phase", str(phase),
                   "--video", video_path]

        elif cmd_type == "text_content":
            cmd = [sys.executable,
                   str(BASE_DIR / "tools" / "text_content_generator.py"),
                   "--project", project, "--phase", str(phase)]

        elif cmd_type == "tts":
            engine = data.get("engine", "edge")   # edge | kokoro | elevenlabs
            voice  = data.get("voice",  "").strip()
            source = data.get("source", "auto").strip()  # auto | srt | script
            tts_script = BASE_DIR / "tools" / "tts" / f"{engine}_voiceover.py"
            if not tts_script.exists():
                self._send_json({"error": f"TTS script not found: {tts_script}"}, 400)
                return
            cmd = [sys.executable, str(tts_script),
                   "--project", project, "--phase", str(phase)]
            if voice:
                cmd += ["--voice", voice]
            if source and source != "auto":
                cmd += ["--source", source]

        elif cmd_type == "compliance":
            cmd = [sys.executable, str(BASE_DIR / "tools" / "compliance_checker.py"),
                   "--project", project, "--phase", str(phase)]

        else:
            # original behaviour: generate_phase.py --only <file>
            topic   = data.get("topic", "")
            outline = data.get("outline", "")
            only    = data.get("only", "")
            cmd = [sys.executable, str(BASE_DIR / "tools" / "generate_phase.py"),
                   "--project", project, "--phase", str(phase)]
            if topic:   cmd += ["--topic",   topic]
            if outline: cmd += ["--outline", outline]
            if only:    cmd += ["--only",    only]

        # ── Version backup: copy existing outputs before overwriting ─────────
        phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
        out_dir   = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}"
        new_version = _backup_step_files(phase_dir, out_dir, cmd_type)

        q: queue.Queue = queue.Queue()
        jobs[job_id] = {
            "status": "running", "output": [], "q": q, "cmd": cmd,
            "version": new_version, "cmd_type": cmd_type,
            "project": project, "phase": phase,
        }
        print(f"  [STEP {job_id}] v{new_version}  {' '.join(cmd)}")

        def worker():
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, cwd=str(BASE_DIR), env=os.environ.copy())
            for line in proc.stdout:
                jobs[job_id]["output"].append(line)
                q.put(line)
            proc.wait()
            final = "done" if proc.returncode == 0 else "failed"
            jobs[job_id]["status"] = final
            jobs[job_id]["returncode"] = proc.returncode
            q.put(None)
            print(f"  [STEP {job_id}] {final}")
            # Record new output files to DB
            if final == "done":
                step_key = _STEP_OUTPUTS.get(cmd_type, (cmd_type, []))[0]
                _record_versions_to_db(project, phase, phase_dir, out_dir,
                                       step_key, new_version, job_id)

        threading.Thread(target=worker, daemon=True).start()
        self._send_json({
            "job_id": job_id,
            "cmd": " ".join(cmd),
            "version": new_version,
        })

    def _api_job_status(self, job_id: str):
        if job_id not in jobs:
            self._send_json({"error": "not found"}, 404)
            return
        job = jobs[job_id]
        self._send_json({
            "status": job["status"],
            "lines": len(job["output"]),
            "returncode": job.get("returncode"),
        })


_SILENT_ERRORS = (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)


class QuietThreadingServer(HTTPServer):
    """Handles multiple requests concurrently and suppresses harmless Windows disconnect errors."""

    allow_reuse_address = True

    def handle_error(self, request, client_address):
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, _SILENT_ERRORS):
            return  # browser closed connection early — not an error
        super().handle_error(request, client_address)

    def process_request(self, request, client_address):
        t = threading.Thread(target=self._process_request_thread,
                             args=(request, client_address), daemon=True)
        t.start()

    def _process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n{'='*52}")
    print(f"  Bhrikuty Film Director -- Dashboard Server")
    print(f"  Open: http://localhost:{port}")
    print(f"  Projects root: {PROJECT_ROOT}")
    print(f"{'='*52}\n")

    httpd = QuietThreadingServer(("0.0.0.0", port), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
