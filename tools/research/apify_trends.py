"""
apify_trends.py — Social media trend research via Apify actors
==============================================================
Uses the 3,268 Apify actors from tools/social_apis/ to research
trending content, hashtags, competitor performance, and video ideas.

Requires: pip install apify-client
API key:  APIFY_API_TOKEN in .env
          Get free token: https://console.apify.com/account/integrations

Usage:
  python tools/research/apify_trends.py --topic "microeconomics" --platform youtube
  python tools/research/apify_trends.py --topic "blockchain" --platform tiktok --limit 20
  python tools/research/apify_trends.py --hashtag "economics" --platform instagram
  python tools/research/apify_trends.py --channel "UCrandom123" --platform youtube
  python tools/research/apify_trends.py --list-actors
"""

import argparse
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_env = Path(__file__).parent.parent.parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

OUTPUT_ROOT = Path(__file__).parent.parent.parent / "youtube_scripts" / "research"

# ── Curated Apify actor IDs for content creators ─────────────────────────────
# From: tools/social_apis/social-media-apis-3268/README.md
ACTORS = {
    # YouTube
    "youtube_search":     "streamers/youtube-scraper",
    "youtube_comments":   "n.nobar/youtube-channel-comment-collector",
    "youtube_transcript": "vulnv/youtube-transcript-downloader-timestamp-export",
    "youtube_trending":   "jupri/youtube-trending",

    # TikTok
    "tiktok_search":      "clockworks/free-tiktok-scraper",
    "tiktok_trending":    "jupri/tiktok",
    "tiktok_hashtag":     "clockworks/tiktok-hashtag-scraper",

    # Instagram
    "instagram_hashtag":  "apidojo/instagram-scraper",
    "instagram_profile":  "apidojo/instagram-scraper",
    "instagram_reels":    "scrapearchitect/instagram-video-scraper-lite",

    # Twitter/X
    "twitter_search":     "quacker/twitter-scraper",
    "twitter_trending":   "quacker/twitter-scraper",

    # LinkedIn
    "linkedin_posts":     "scary_good_apis/linkedin-search-posts",
    "linkedin_profile":   "dataweave/linkedin-profile-scraper",

    # Cross-platform
    "trend_analyzer":     "manju4k/social-media-trend-scraper-6-in-1-ai-analysis",
    "video_transcript":   "agentx/video-transcript",
    "all_video_scraper":  "agentx/all-video-scraper",
}

PLATFORM_ACTORS = {
    "youtube":   ["youtube_search", "youtube_trending", "youtube_comments"],
    "tiktok":    ["tiktok_search", "tiktok_trending", "tiktok_hashtag"],
    "instagram": ["instagram_hashtag", "instagram_reels"],
    "twitter":   ["twitter_search", "twitter_trending"],
    "linkedin":  ["linkedin_posts"],
    "all":       ["trend_analyzer"],
}


def _get_client():
    token = os.environ.get("APIFY_API_TOKEN", "")
    if not token:
        print("[ERROR] APIFY_API_TOKEN not set in .env")
        print("  Get free token: https://console.apify.com/account/integrations")
        print("  Free tier: 5 USD credit/month — enough for ~50 research runs")
        sys.exit(1)
    try:
        from apify_client import ApifyClient
        return ApifyClient(token)
    except ImportError:
        print("[ERROR] apify-client not installed: pip install apify-client")
        sys.exit(1)


def search_youtube(topic: str, limit: int = 10) -> list:
    """Search YouTube for videos matching a topic."""
    client = _get_client()
    print(f"[YouTube] Searching for: {topic} (limit {limit})…")
    run = client.actor(ACTORS["youtube_search"]).call(run_input={
        "searchKeywords": topic,
        "maxResults":     limit,
        "type":           "video",
    })
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"  Found {len(items)} videos")
    return items


def search_tiktok(topic: str, limit: int = 10) -> list:
    """Search TikTok for videos matching a topic/hashtag."""
    client = _get_client()
    print(f"[TikTok] Searching for: {topic} (limit {limit})…")
    run = client.actor(ACTORS["tiktok_search"]).call(run_input={
        "hashtags": [topic.lstrip("#")],
        "resultsPerPage": limit,
    })
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"  Found {len(items)} videos")
    return items


def get_trending(platform: str, topic: str = "", limit: int = 20) -> list:
    """Get trending content for a platform."""
    client = _get_client()
    actor_key = f"{platform}_trending"
    actor_id  = ACTORS.get(actor_key)
    if not actor_id:
        print(f"[WARN] No trending actor for {platform}")
        return []

    print(f"[{platform.capitalize()}] Getting trending content…")
    run_input = {"limit": limit}
    if topic:
        run_input["query"] = topic
    run   = client.actor(actor_id).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"  Found {len(items)} trending items")
    return items


def analyze_trends(topic: str, platforms: list = None) -> dict:
    """Cross-platform trend analysis using the 6-in-1 scraper."""
    client = _get_client()
    plats  = platforms or ["youtube", "tiktok", "instagram"]
    print(f"[Trends] Analyzing '{topic}' across {', '.join(plats)}…")
    run = client.actor(ACTORS["trend_analyzer"]).call(run_input={
        "query":        topic,
        "platforms":    plats,
        "limit":        20,
        "aiAnalysis":   True,
    })
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"  Trend data: {len(items)} entries")
    return {"topic": topic, "platforms": plats, "data": items}


def research_competitors(channel_url: str) -> dict:
    """Scrape a competitor YouTube channel for content insights."""
    client = _get_client()
    print(f"[Competitor] Analyzing: {channel_url}")
    run = client.actor(ACTORS["youtube_search"]).call(run_input={
        "startUrls":    [{"url": channel_url}],
        "maxResults":   20,
    })
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    # Extract top performing videos
    sorted_items = sorted(items,
                          key=lambda x: int(x.get("viewCount", 0) or 0),
                          reverse=True)
    print(f"  Found {len(items)} videos, top by views:")
    for v in sorted_items[:5]:
        views = v.get("viewCount", "?")
        title = v.get("title", "?")[:60]
        print(f"    {views:>10} views — {title}")
    return {"channel": channel_url, "videos": sorted_items}


def save_research(data: dict, filename: str):
    """Save research results to JSON."""
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_ROOT / filename
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False,
                               default=str), encoding="utf-8")
    print(f"  Saved: {out}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Social media trend research via Apify")
    parser.add_argument("--topic",      default="",  help="Topic/keyword to research")
    parser.add_argument("--hashtag",    default="",  help="Hashtag to research (without #)")
    parser.add_argument("--channel",    default="",  help="Competitor YouTube channel URL")
    parser.add_argument("--platform",   default="all",
                        help="youtube|tiktok|instagram|twitter|linkedin|all")
    parser.add_argument("--limit",      type=int, default=10, help="Max results")
    parser.add_argument("--list-actors",action="store_true",  help="List available Apify actors")
    args = parser.parse_args()

    if args.list_actors:
        print(f"\n{'='*60}")
        print("  Available Apify Actors (from social_apis catalog)")
        print(f"{'='*60}")
        for key, actor_id in ACTORS.items():
            print(f"  {key:<25} → apify.com/actor/{actor_id}")
        print(f"\nFull catalog: tools/social_apis/social-media-apis-3268/README.md")
        print(f"(3,268 actors available)")
        return

    topic   = args.topic or args.hashtag
    results = {}

    if args.channel:
        results["competitor"] = research_competitors(args.channel)
    elif args.platform == "all" and topic:
        results["trends"] = analyze_trends(topic)
    elif args.platform == "youtube" and topic:
        results["youtube"] = search_youtube(topic, args.limit)
    elif args.platform == "tiktok" and topic:
        results["tiktok"] = search_tiktok(topic, args.limit)
    elif args.platform in ("instagram", "twitter", "linkedin") and topic:
        results[args.platform] = get_trending(args.platform, topic, args.limit)
    else:
        parser.print_help()
        return

    if results:
        safe_topic = (topic or args.channel).replace(" ", "_").replace("/", "_")[:30]
        filename   = f"{args.platform}_{safe_topic}.json"
        saved      = save_research(results, filename)
        print(f"\n✅ Research saved → {saved}")
        print(f"   Use findings to inform your next script topic and outline.")


if __name__ == "__main__":
    main()
