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

        elif path == "/api/tools-status":
            self._api_tools_status()

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
             "cmd": f'python pipeline.py --project {proj} --phase {ph} --skip-generate --video path/to/recording.mp4'},

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

        output_dir = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}"
        output_files = []
        if output_dir.exists():
            for f in sorted(output_dir.rglob("*")):
                if f.is_file():
                    output_files.append(str(f.relative_to(output_dir)))

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
            "video_type": video_type,
            "brand": brand_profile,
            "roadmap_phase": roadmap_phase,
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

    def _api_run_step(self, data: dict):
        """Run a single generate_phase.py sub-step (--only <file>)."""
        job_id  = uuid.uuid4().hex[:8]
        project = data.get("project", "chain_clarity")
        phase   = int(data.get("phase", 1))
        topic   = data.get("topic", "")
        outline = data.get("outline", "")
        only    = data.get("only", "")

        cmd = [sys.executable, str(BASE_DIR / "tools" / "generate_phase.py"),
               "--project", project, "--phase", str(phase)]
        if topic:   cmd += ["--topic",   topic]
        if outline: cmd += ["--outline", outline]
        if only:    cmd += ["--only",    only]

        q: queue.Queue = queue.Queue()
        jobs[job_id] = {"status": "running", "output": [], "q": q, "cmd": cmd}
        print(f"  [STEP {job_id}] {' '.join(cmd)}")

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

        threading.Thread(target=worker, daemon=True).start()
        self._send_json({"job_id": job_id, "cmd": " ".join(cmd)})

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
