"""
publish_platform.py — Unified publisher for all social media platforms
======================================================================
Publishes generated content to one or all platforms using their official APIs.

Usage:
  python tools/publish/publish_platform.py --project ecoWorld --phase 1 --platform all
  python tools/publish/publish_platform.py --project ecoWorld --phase 1 --platform youtube
  python tools/publish/publish_platform.py --project ecoWorld --phase 1 --platform tiktok,instagram
  python tools/publish/publish_platform.py --project ecoWorld --phase 1 --dry-run

Supported platforms: youtube, tiktok, instagram, twitter, linkedin
"""

import argparse
import json
import os
import sys
import time
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

PROJECT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "setup" / "projects"

# ── Platform publish functions ────────────────────────────────────────────────

def publish_youtube(project, phase, dry_run=False):
    """Delegate to publish_youtube.py"""
    import importlib.util
    script = Path(__file__).parent / "publish_youtube.py"
    spec = importlib.util.spec_from_file_location("publish_youtube", script)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.publish(project, phase, dry_run=dry_run)


def publish_tiktok(project, phase, dry_run=False):
    """Post TikTok hook clip + main clip via TikTok Content Posting API."""
    out_dir = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}" / "tiktok"
    api_key = os.environ.get("TIKTOK_API_KEY", "")

    hook_clip = out_dir / "clip_01_hook.mp4"
    main_clip = out_dir / "clip_02_main.mp4"
    caption   = (out_dir / "caption_hook.txt").read_text(encoding="utf-8").strip() \
                if (out_dir / "caption_hook.txt").exists() else ""

    print(f"\n{'='*50}\n  TikTok Publish — {project} Phase {phase}\n{'='*50}")
    print(f"  Hook clip : {hook_clip}  ({'✓' if hook_clip.exists() else '✗'})")
    print(f"  Main clip : {main_clip}  ({'✓' if main_clip.exists() else '✗'})")

    if not api_key:
        print("\n[SKIP] TIKTOK_API_KEY not set in .env")
        print("  Setup: https://developers.tiktok.com/products/content-posting-api/")
        return {"status": "skipped", "reason": "no_api_key"}

    if dry_run:
        print("[DRY RUN] Would post hook clip + main clip to TikTok")
        return {"status": "dry_run"}

    # TikTok Content Posting API
    import urllib.request
    results = []
    for clip_path, clip_type in [(hook_clip, "hook"), (main_clip, "main")]:
        if not clip_path.exists():
            print(f"  [SKIP] {clip_type} clip not found")
            continue
        try:
            # Step 1: Init upload
            init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            headers  = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json; charset=UTF-8",
            }
            init_body = json.dumps({
                "post_info": {
                    "title": caption[:100],
                    "privacy_level": "SELF_ONLY",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source":      "FILE_UPLOAD",
                    "video_size":  clip_path.stat().st_size,
                    "chunk_size":  clip_path.stat().st_size,
                    "total_chunk_count": 1,
                }
            }).encode()
            req = urllib.request.Request(init_url, data=init_body, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                init_resp = json.loads(r.read())
            upload_url = init_resp["data"]["upload_url"]
            publish_id = init_resp["data"]["publish_id"]
            print(f"  [TikTok] Init OK — publish_id: {publish_id}")

            # Step 2: Upload binary
            with open(clip_path, "rb") as f:
                video_data = f.read()
            upload_headers = {
                "Content-Type":  "video/mp4",
                "Content-Length": str(len(video_data)),
                "Content-Range":  f"bytes 0-{len(video_data)-1}/{len(video_data)}",
            }
            upload_req = urllib.request.Request(upload_url, data=video_data,
                                                headers=upload_headers, method="PUT")
            urllib.request.urlopen(upload_req, timeout=120)
            print(f"  [TikTok] ✅ {clip_type} clip uploaded")
            results.append({"clip": clip_type, "publish_id": publish_id})

        except Exception as e:
            print(f"  [TikTok] ❌ {clip_type} failed: {e}")
            results.append({"clip": clip_type, "error": str(e)})

    _save_record(project, phase, "tiktok", results)
    return results


def publish_instagram(project, phase, dry_run=False):
    """Post Instagram Reel via Meta Graph API."""
    out_dir  = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}" / "instagram"
    token    = os.environ.get("META_ACCESS_TOKEN", "")
    acct_id  = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")
    reel     = out_dir / "reel_60s.mp4"
    caption  = (out_dir / "caption_reel.txt").read_text(encoding="utf-8").strip() \
               if (out_dir / "caption_reel.txt").exists() else ""

    print(f"\n{'='*50}\n  Instagram Publish — {project} Phase {phase}\n{'='*50}")
    print(f"  Reel: {reel}  ({'✓' if reel.exists() else '✗'})")

    if not token or not acct_id:
        print("\n[SKIP] META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID not set in .env")
        print("  Setup: https://developers.facebook.com/docs/instagram-api/guides/content-publishing")
        return {"status": "skipped", "reason": "no_credentials"}

    if dry_run:
        print(f"[DRY RUN] Would post Reel to @{acct_id}")
        return {"status": "dry_run"}

    import urllib.request, urllib.parse
    base = f"https://graph.facebook.com/v18.0/{acct_id}"

    try:
        # Step 1: Create media container (reel must be publicly accessible URL)
        # Note: In production, upload to a CDN first and use the URL
        print("  [NOTE] Instagram requires a public video URL for upload.")
        print("  [NOTE] Host final_1080p.mp4 on a CDN or use ngrok for local testing.")
        video_url = os.environ.get("INSTAGRAM_VIDEO_URL", "")
        if not video_url:
            print("  [SKIP] Set INSTAGRAM_VIDEO_URL=https://... in .env with the hosted video URL")
            return {"status": "skipped", "reason": "no_video_url"}

        params = urllib.parse.urlencode({
            "media_type":   "REELS",
            "video_url":    video_url,
            "caption":      caption[:2200],
            "access_token": token,
        }).encode()
        req = urllib.request.Request(f"{base}/media", data=params, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            container = json.loads(r.read())
        container_id = container["id"]
        print(f"  [Instagram] Container created: {container_id}")
        time.sleep(5)   # wait for processing

        # Step 2: Publish
        pub_params = urllib.parse.urlencode({
            "creation_id":  container_id,
            "access_token": token,
        }).encode()
        pub_req = urllib.request.Request(f"{base}/media_publish",
                                         data=pub_params, method="POST")
        with urllib.request.urlopen(pub_req, timeout=30) as r:
            pub_resp = json.loads(r.read())
        media_id = pub_resp["id"]
        print(f"  [Instagram] ✅ Published — media_id: {media_id}")
        result = {"status": "published", "media_id": media_id}
        _save_record(project, phase, "instagram", result)
        return result

    except Exception as e:
        print(f"  [Instagram] ❌ Failed: {e}")
        return {"status": "error", "error": str(e)}


def publish_twitter(project, phase, dry_run=False):
    """Post Twitter/X thread via Twitter API v2."""
    out_dir = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}" / "twitter"
    token   = os.environ.get("TWITTER_BEARER_TOKEN", "")
    client_id     = os.environ.get("TWITTER_CLIENT_ID", "")
    client_secret = os.environ.get("TWITTER_CLIENT_SECRET", "")
    thread_file = out_dir / "thread.txt"

    print(f"\n{'='*50}\n  Twitter/X Publish — {project} Phase {phase}\n{'='*50}")

    if not (token and client_id):
        print("\n[SKIP] TWITTER_BEARER_TOKEN or TWITTER_CLIENT_ID not set in .env")
        print("  Setup: https://developer.twitter.com/en/portal/dashboard")
        return {"status": "skipped", "reason": "no_credentials"}

    if not thread_file.exists():
        print(f"[SKIP] thread.txt not found: {thread_file}")
        print("  Generate: python tools/text_content_generator.py "
              f"--project {project} --phase {phase}")
        return {"status": "skipped", "reason": "no_thread_file"}

    # Parse thread.txt — expect tweets separated by "---" or numbered
    thread_raw = thread_file.read_text(encoding="utf-8")
    tweets = [t.strip() for t in thread_raw.split("---") if t.strip()]
    if not tweets:
        # Try numbered tweets
        import re
        tweets = re.findall(r'(?:Tweet\s+\d+|^\d+\.)\s*[:\n]\s*(.+?)(?=(?:Tweet\s+\d+|^\d+\.)|\Z)',
                            thread_raw, re.DOTALL | re.MULTILINE)
        tweets = [t.strip() for t in tweets if t.strip()]
    if not tweets:
        tweets = [t.strip() for t in thread_raw.split("\n\n") if t.strip()][:10]

    print(f"  Thread : {len(tweets)} tweets")
    for i, tw in enumerate(tweets[:3]):
        print(f"   Tweet {i+1}: {tw[:80]}…")

    if dry_run:
        print(f"\n[DRY RUN] Would post {len(tweets)}-tweet thread")
        return {"status": "dry_run", "tweets": len(tweets)}

    try:
        import tweepy
    except ImportError:
        print("[ERROR] tweepy not installed: pip install tweepy")
        return {"status": "error", "error": "tweepy_not_installed"}

    try:
        client = tweepy.Client(
            bearer_token=token,
            consumer_key=os.environ.get("TWITTER_API_KEY",""),
            consumer_secret=os.environ.get("TWITTER_API_SECRET",""),
            access_token=os.environ.get("TWITTER_ACCESS_TOKEN",""),
            access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET",""),
        )
        tweet_ids = []
        reply_to  = None
        for i, tweet_text in enumerate(tweets):
            kwargs = {"text": tweet_text[:280]}
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to
            resp    = client.create_tweet(**kwargs)
            tweet_id = resp.data["id"]
            tweet_ids.append(tweet_id)
            reply_to = tweet_id
            print(f"  [Twitter] Tweet {i+1}/{len(tweets)} posted: {tweet_id}")
            time.sleep(1)   # rate limit safety

        url = f"https://twitter.com/i/web/status/{tweet_ids[0]}"
        print(f"  ✅ Thread posted: {url}")
        result = {"status": "published", "thread_url": url, "tweet_ids": tweet_ids}
        _save_record(project, phase, "twitter", result)
        return result

    except Exception as e:
        print(f"  [Twitter] ❌ Failed: {e}")
        return {"status": "error", "error": str(e)}


def publish_linkedin(project, phase, dry_run=False):
    """Post LinkedIn article + video via LinkedIn Marketing API."""
    out_dir  = PROJECT_ROOT / project / "_output" / f"phase_{phase:02d}" / "linkedin"
    token    = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    person_id = os.environ.get("LINKEDIN_PERSON_ID", "")
    article  = out_dir / "article.md"
    caption  = (out_dir / "caption_clip.txt").read_text(encoding="utf-8").strip() \
               if (out_dir / "caption_clip.txt").exists() else ""

    print(f"\n{'='*50}\n  LinkedIn Publish — {project} Phase {phase}\n{'='*50}")

    if not (token and person_id):
        print("\n[SKIP] LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_ID not set in .env")
        print("  Setup: https://www.linkedin.com/developers/apps")
        return {"status": "skipped", "reason": "no_credentials"}

    if dry_run:
        print("[DRY RUN] Would post LinkedIn article")
        return {"status": "dry_run"}

    import urllib.request, urllib.parse
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    try:
        # Post as a simple text post with article content
        commentary = caption[:3000]
        body = json.dumps({
            "author":     f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": commentary},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }).encode()
        req = urllib.request.Request("https://api.linkedin.com/v2/ugcPosts",
                                     data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        post_id = resp.get("id", "")
        post_url = f"https://www.linkedin.com/feed/update/{post_id}"
        print(f"  [LinkedIn] ✅ Posted: {post_url}")
        result = {"status": "published", "post_id": post_id, "url": post_url}
        _save_record(project, phase, "linkedin", result)
        return result

    except Exception as e:
        print(f"  [LinkedIn] ❌ Failed: {e}")
        return {"status": "error", "error": str(e)}


def _save_record(project: str, phase: int, platform: str, data):
    """Write publish_record.json to the platform output folder."""
    record_path = (PROJECT_ROOT / project / "_output"
                   / f"phase_{phase:02d}" / platform / "publish_record.json")
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps({
        "platform": platform, "project": project, "phase": phase,
        "result": data,
    }, indent=2, default=str), encoding="utf-8")
    print(f"  Saved record: {record_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

_PUBLISHERS = {
    "youtube":   publish_youtube,
    "tiktok":    publish_tiktok,
    "instagram": publish_instagram,
    "twitter":   publish_twitter,
    "linkedin":  publish_linkedin,
}


def main():
    parser = argparse.ArgumentParser(description="Publish to social media platforms")
    parser.add_argument("--project",  required=True)
    parser.add_argument("--phase",    type=int, required=True)
    parser.add_argument("--platform", default="all",
                        help="Comma-separated: youtube,tiktok,instagram,twitter,linkedin or 'all'")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Show what would be published without actually posting")
    args = parser.parse_args()

    platforms = (list(_PUBLISHERS.keys())
                 if args.platform == "all"
                 else [p.strip() for p in args.platform.split(",")])

    print(f"\n{'='*58}")
    print(f"  Social Media Publisher — {args.project}  Phase {args.phase}")
    print(f"  Platforms: {', '.join(platforms)}")
    if args.dry_run:
        print(f"  Mode: DRY RUN — no actual posts")
    print(f"{'='*58}")

    results = {}
    for platform in platforms:
        fn = _PUBLISHERS.get(platform)
        if not fn:
            print(f"[WARN] Unknown platform: {platform}")
            continue
        results[platform] = fn(args.project, args.phase, dry_run=args.dry_run)

    print(f"\n{'='*58}")
    print(f"  PUBLISH SUMMARY")
    print(f"{'='*58}")
    for platform, result in results.items():
        status = result.get("status", "unknown") if isinstance(result, dict) else "done"
        icon   = "✅" if status == "published" else ("⏭" if status in ("skipped","dry_run") else "❌")
        print(f"  {icon} {platform:<12} {status}")
    print()


if __name__ == "__main__":
    main()
