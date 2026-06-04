"""
publish_youtube.py — Upload a video to YouTube via Data API v3
=============================================================
Requires:
  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

Setup (one-time):
  1. console.cloud.google.com → Create project → Enable YouTube Data API v3
  2. Create OAuth 2.0 Desktop credentials → Download client_secrets.json
  3. Save client_secrets.json to the project root
  4. Run this script once — browser opens for auth → saves token.json

Usage:
  python tools/publish/publish_youtube.py --project ecoWorld --phase 1
  python tools/publish/publish_youtube.py --project ecoWorld --phase 1 --schedule "2025-06-10T14:00:00Z"
  python tools/publish/publish_youtube.py --project ecoWorld --phase 1 --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load .env
_env = Path(__file__).parent.parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

PROJECT_ROOT  = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"
SECRETS_FILE  = Path(__file__).parent.parent.parent / "client_secrets.json"
TOKEN_FILE    = Path(__file__).parent.parent.parent / "youtube_token.json"
SCOPES        = ["https://www.googleapis.com/auth/youtube.upload",
                 "https://www.googleapis.com/auth/youtube"]


def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not SECRETS_FILE.exists():
                print(f"[ERROR] client_secrets.json not found: {SECRETS_FILE}")
                print("  Download from: console.cloud.google.com → APIs → OAuth 2.0 Credentials")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print(f"  [AUTH] Token saved: {TOKEN_FILE}")

    return creds


def publish(project: str, phase: int, schedule_at: str = None,
            privacy: str = "private", dry_run: bool = False):
    """Upload the assembled YouTube video for a phase."""
    phase_dir = PROJECT_ROOT / project / f"phase_{phase}"
    out_dir   = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}"

    # ── Locate video file ──────────────────────────────────────────────────────
    video_path = out_dir / "youtube" / "final_1080p.mp4"
    if not video_path.exists():
        print(f"[ERROR] Video not found: {video_path}")
        print(f"  Generate first: python tools/video/create_video.py --project {project} --phase {phase}")
        sys.exit(1)

    # ── Load metadata ──────────────────────────────────────────────────────────
    spec_path = phase_dir / "content_spec.json"
    spec = {}
    if spec_path.exists():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

    bp_path = PROJECT_ROOT / project / "brand_profile.json"
    brand = {}
    if bp_path.exists():
        brand = json.loads(bp_path.read_text(encoding="utf-8"))

    title       = spec.get("title", f"Phase {phase}")
    yt          = spec.get("youtube", {})
    description = (out_dir / "youtube" / "description.txt").read_text(
        encoding="utf-8") if (out_dir / "youtube" / "description.txt").exists() else ""
    tags        = spec.get("tags", [])[:500]   # YouTube tag limit
    srt_path    = phase_dir / "subtitles.srt"

    size_mb = round(video_path.stat().st_size / 1024 / 1024, 2)

    print(f"\n{'='*58}")
    print(f"  YouTube Upload — {project}  Phase {phase}")
    print(f"{'='*58}")
    print(f"  Video  : {video_path}  ({size_mb} MB)")
    print(f"  Title  : {title}")
    print(f"  Privacy: {privacy}")
    if schedule_at:
        print(f"  Schedule: {schedule_at}")
    print()

    if dry_run:
        print("[DRY RUN] Would upload with:")
        print(f"  title      = {title}")
        print(f"  tags       = {tags}")
        print(f"  description = {description[:120]}…")
        print(f"  SRT captions: {'yes' if srt_path.exists() else 'no'}")
        print("\n[DRY RUN] No upload performed.")
        return

    # ── Upload ─────────────────────────────────────────────────────────────────
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("[ERROR] Required packages not installed.")
        print("  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        sys.exit(1)

    creds   = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title":       title,
            "description": description,
            "tags":        tags,
            "categoryId":  "27",   # Education
        },
        "status": {
            "privacyStatus":     privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    if schedule_at and privacy == "private":
        body["status"]["publishAt"] = schedule_at
        body["status"]["privacyStatus"] = "private"

    print("[1/3] Uploading video…")
    media = MediaFileUpload(str(video_path), mimetype="video/mp4",
                            resumable=True, chunksize=10 * 1024 * 1024)
    req  = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"   Upload progress: {pct}%", end="\r")

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\n  ✅ Uploaded: {video_url}")
    print(f"     Video ID: {video_id}")

    # ── Upload SRT captions ────────────────────────────────────────────────────
    if srt_path.exists():
        print("[2/3] Uploading SRT captions…")
        try:
            media_caption = MediaFileUpload(str(srt_path), mimetype="application/octet-stream",
                                            resumable=False)
            cap_body = {
                "snippet": {
                    "videoId":      video_id,
                    "language":     "en",
                    "name":         "English",
                    "isDraft":      False,
                },
            }
            youtube.captions().insert(
                part="snippet", body=cap_body, media_body=media_caption
            ).execute()
            print("  ✅ Captions uploaded")
        except Exception as e:
            print(f"  ⚠️  Caption upload failed (non-fatal): {e}")
    else:
        print("[2/3] No subtitles.srt — skipping captions")

    # ── Save publish record ────────────────────────────────────────────────────
    print("[3/3] Saving publish record…")
    record = {
        "platform":   "youtube",
        "video_id":   video_id,
        "url":        video_url,
        "title":      title,
        "privacy":    privacy,
        "published_at": schedule_at or "immediate",
    }
    record_path = out_dir / "youtube" / "publish_record.json"
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"  Saved: {record_path}")

    print(f"\n{'='*58}")
    print(f"  DONE — {video_url}")
    print(f"{'='*58}\n")
    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--project",  required=True)
    parser.add_argument("--phase",    type=int, required=True)
    parser.add_argument("--privacy",  default="private",
                        choices=["private", "unlisted", "public"])
    parser.add_argument("--schedule", default="",
                        help="ISO 8601 datetime to schedule publish e.g. 2025-06-10T14:00:00Z")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Show what would be uploaded without actually uploading")
    args = parser.parse_args()

    publish(args.project, args.phase,
            schedule_at=args.schedule or None,
            privacy=args.privacy,
            dry_run=args.dry_run)


if __name__ == "__main__":
    main()
