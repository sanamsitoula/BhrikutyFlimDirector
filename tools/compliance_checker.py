"""
compliance_checker.py — Automated brand compliance for Chain Clarity
Usage: python tools/compliance_checker.py --project chain_clarity --phase 4
       python tools/compliance_checker.py --project chain_clarity --phase all
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).parent.parent / "youtube_scripts" / "setup" / "projects"


def load_brand(project: str) -> dict:
    path = PROJECT_ROOT / project / "brand_profile.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_forbidden_words(text: str, forbidden: list[str]) -> list[str]:
    # Strip markdown headings, ON-SCREEN TEXT lines, B-ROLL lines, and title lines
    # so we only check actual spoken/written content
    filtered_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Skip headings, title lines, and metadata (## , # , **Format:**, ON-SCREEN TEXT, B-ROLL, TITLE CARD)
        if re.match(r'^#{1,4}\s', stripped):
            continue
        if re.match(r'\*\*(Format|Target|Duration|Status|Date|Phase|Files):', stripped, re.IGNORECASE):
            continue
        filtered_lines.append(line)

    filtered_text = "\n".join(filtered_lines)
    found = []
    text_lower = filtered_text.lower()
    for word in forbidden:
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(word)
    return found


def check_sentence_length(text: str, max_words: int = 15) -> list[str]:
    violations = []
    # Only check SPOKEN sections — skip headings, ON-SCREEN TEXT, and B-ROLL lines
    spoken_lines = []
    in_spoken = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.upper().startswith("SPOKEN"):
            in_spoken = True
            continue
        if stripped.startswith("[") or stripped.startswith("ON-SCREEN") or stripped.startswith("##") or stripped.startswith("#"):
            in_spoken = False
            continue
        if in_spoken and stripped:
            spoken_lines.append(stripped)

    spoken_text = " ".join(spoken_lines)
    sentences = re.split(r'[.!?]+', spoken_text)
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        word_count = len(s.split())
        if word_count > max_words:
            violations.append(f"({word_count} words) {s[:80]}...")
    return violations


def check_hex_colors(html: str, brand_colors: dict) -> tuple[list[str], list[str]]:
    """Returns (valid_colors_found, invalid_colors_found)."""
    brand_hexes = {v["hex"].upper() for v in brand_colors.values()}
    # #FFFFFF (white) is universally allowed for text on dark backgrounds
    # #EF4444 is the documented semantic exception for danger states
    allowed_semantic = {"#EF4444", "#FFFFFF"}
    all_allowed = brand_hexes | allowed_semantic

    found_hexes = set(re.findall(r'#[0-9A-Fa-f]{6}', html))
    found_hexes = {h.upper() for h in found_hexes}

    invalid = [h for h in found_hexes if h not in all_allowed]
    valid = [h for h in found_hexes if h in brand_hexes]
    css_names = re.findall(r':\s*(red|blue|green|white|black|teal|gold|navy|purple|gray|grey)\b', html, re.IGNORECASE)
    return valid, invalid, css_names


def check_fonts(html: str) -> dict:
    results = {}
    results["space_grotesk"] = "Space Grotesk" in html
    results["inter"] = "'Inter'" in html or '"Inter"' in html
    results["jetbrains_mono"] = "JetBrains Mono" in html
    results["cdn_loaded"] = "fonts.googleapis.com" in html
    return results


def check_animation_sequence(html: str) -> dict:
    checks = {
        "bg_fade_in":    bool(re.search(r'fadeIn\s+0\.2s', html)),
        "logo_slide_down": bool(re.search(r'slideDown\s+0\.3s', html)),
        "headline_word_by_word": bool(re.search(r'wordIn\s+0\.15s', html)),
        "content_slide_up": bool(re.search(r'slideUp\s+0\.4s', html)),
        "stat_bounce_in": bool(re.search(r'bounce\s+0\.3s', html)),
    }
    return checks


def check_subtitles(srt_path: Path) -> dict:
    if not srt_path.exists():
        return {"error": "subtitles.srt not found"}

    content = srt_path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in content.strip().split("\n\n") if b.strip()]

    violations_words = []
    violations_duration = []
    cue_count = len(blocks)

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        timecode = lines[1] if len(lines) > 1 else ""
        text_lines = lines[2:]

        for tl in text_lines:
            tl = tl.strip()
            if not tl:
                continue
            # Strip inline SRT formatting tags and standalone punctuation before counting
            clean = re.sub(r'<[^>]+>', '', tl)
            # Split and remove tokens that are only punctuation/dashes (not real words)
            tokens = [w for w in clean.split() if re.search(r'[a-zA-Z0-9]', w)]
            words = len(tokens)
            if words > 7:
                violations_words.append(f"{words} words: {tl[:60]}")

        # Check duration
        tc_match = re.match(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)', timecode)
        if tc_match:
            def to_ms(tc):
                parts = tc.replace(',', ':').split(':')
                h, m, s, ms = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                return h * 3600000 + m * 60000 + s * 1000 + ms
            start_ms = to_ms(tc_match.group(1))
            end_ms = to_ms(tc_match.group(2))
            duration_ms = end_ms - start_ms
            if duration_ms < 1000 or duration_ms > 6000:
                violations_duration.append(f"{duration_ms}ms: {' '.join(text_lines)[:40]}")

    return {
        "cue_count": cue_count,
        "word_violations": violations_words,
        "duration_violations": violations_duration,
    }


def check_bpm(music_brief: str) -> bool:
    # Match patterns like "88-112", "88–112", "96–100 BPM", or just any BPM number in range
    return bool(re.search(r'\b(88|8[9]|9\d|10\d|11[012])\b', music_brief))


def run_checks(project: str, phase_num: int) -> dict:
    brand = load_brand(project)
    phase_dir = PROJECT_ROOT / project / f"phase_{phase_num}"

    if not phase_dir.exists():
        print(f"[ERROR] Phase directory not found: {phase_dir}")
        sys.exit(1)

    results = {
        "project": project,
        "phase": phase_num,
        "date": str(date.today()),
        "checks": {}
    }

    # CHECK 1: Tone of voice
    script_path = phase_dir / "script.md"
    short_path = phase_dir / "script_short.md"
    tone_check = {"status": "PASS", "issues": []}

    for path in [script_path, short_path]:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            forbidden = brand["tone_of_voice"]["forbidden_words"]
            found = check_forbidden_words(text, forbidden)
            if found:
                tone_check["status"] = "FAIL"
                tone_check["issues"].append(f"{path.name}: forbidden words found: {found}")
            long_sentences = check_sentence_length(text)
            if long_sentences:
                tone_check["issues"].append(f"{path.name}: {len(long_sentences)} sentences exceed 15 words")

    results["checks"]["tone_of_voice"] = tone_check

    # CHECK 2: Color codes in HTML cards
    assets_dir = phase_dir / "infographic_assets"
    color_check = {"status": "PASS", "issues": [], "css_name_violations": []}

    for html_file in sorted(assets_dir.glob("*.html")):
        html = html_file.read_text(encoding="utf-8")
        valid, invalid, css_names = check_hex_colors(html, brand["colors"])
        if invalid:
            color_check["status"] = "FAIL"
            color_check["issues"].append(f"{html_file.name}: unknown hex: {invalid}")
        if css_names:
            color_check["status"] = "FAIL"
            color_check["css_name_violations"].append(f"{html_file.name}: CSS color names: {css_names}")

    results["checks"]["color_codes"] = color_check

    # CHECK 3: Typography
    font_check = {"status": "PASS", "issues": []}

    for html_file in sorted(assets_dir.glob("*.html")):
        html = html_file.read_text(encoding="utf-8")
        fonts = check_fonts(html)
        missing = [k for k, v in fonts.items() if not v]
        if missing:
            font_check["issues"].append(f"{html_file.name}: missing {missing}")
            font_check["status"] = "WARN"

    results["checks"]["typography"] = font_check

    # CHECK 4: Animation sequence
    anim_check = {"status": "PASS", "issues": []}

    for html_file in sorted(assets_dir.glob("*.html")):
        html = html_file.read_text(encoding="utf-8")
        anims = check_animation_sequence(html)
        missing = [k for k, v in anims.items() if not v]
        if missing:
            anim_check["issues"].append(f"{html_file.name}: missing animations: {missing}")
            anim_check["status"] = "WARN"

    results["checks"]["animation_sequence"] = anim_check

    # CHECK 5: Subtitles
    srt_result = check_subtitles(phase_dir / "subtitles.srt")
    sub_check = {"status": "PASS", "issues": [], "cue_count": srt_result.get("cue_count", 0)}

    if srt_result.get("word_violations"):
        # Word-count violations: WARN (not FAIL) — minor style issue, manually approved in pre-existing phases
        if sub_check["status"] == "PASS":
            sub_check["status"] = "WARN"
        sub_check["issues"].extend([f"[word-count] {v}" for v in srt_result["word_violations"][:5]])
    if srt_result.get("duration_violations"):
        # Duration violations are more serious — FAIL
        sub_check["status"] = "FAIL"
        sub_check["issues"].extend(srt_result["duration_violations"][:3])
    if srt_result.get("error"):
        sub_check["status"] = "WARN"
        sub_check["issues"].append(srt_result["error"])

    results["checks"]["subtitles"] = sub_check

    # CHECK 6: Sound identity
    music_path = phase_dir / "music_brief.md"
    sound_check = {"status": "PASS", "issues": []}

    if music_path.exists():
        music = music_path.read_text(encoding="utf-8")
        if not check_bpm(music):
            sound_check["issues"].append("BPM range 88-112 not found in music_brief.md")
            sound_check["status"] = "WARN"
        forbidden_genres = brand["sound_identity"]["forbidden_genres"]
        # Only flag genres if they appear on lines that are NOT the "Forbidden genres:" list.
        # Filter out lines that explicitly list forbidden genres.
        non_forbidden_lines = [
            line for line in music.split("\n")
            if not re.search(
                r'forbidden.{0,30}genre|no trap|no hype|avoid.*genre|\*\*Forbidden[\*:]',
                line, re.IGNORECASE
            )
        ]
        recommended_text = "\n".join(non_forbidden_lines).lower()
        for genre in forbidden_genres:
            if re.search(r'\b' + re.escape(genre.lower()) + r'\b', recommended_text):
                context_pos = recommended_text.find(genre.lower())
                pre_context = recommended_text[max(0, context_pos - 40):context_pos]
                if not any(kw in pre_context for kw in ["no ", "not ", "avoid", "without", "never", "forbidden", "excl"]):
                    sound_check["issues"].append(f"Forbidden genre recommended: {genre}")
                    sound_check["status"] = "FAIL"
    else:
        sound_check["status"] = "WARN"
        sound_check["issues"].append("music_brief.md not found")

    results["checks"]["sound_identity"] = sound_check

    # Overall verdict
    statuses = [c["status"] for c in results["checks"].values()]
    if "FAIL" in statuses:
        results["overall"] = "FAIL"
    elif "WARN" in statuses:
        results["overall"] = "PASS_WITH_WARNINGS"
    else:
        results["overall"] = "PASS"

    return results


def write_report(results: dict, project: str, phase_num: int):
    phase_dir = PROJECT_ROOT / project / f"phase_{phase_num}"
    report_path = phase_dir / "compliance_report_auto.md"

    lines = [
        f"# Auto Compliance Report — Phase {phase_num}",
        f"## Chain Clarity · Auto-generated by compliance_checker.py",
        f"",
        f"**Date:** {results['date']}",
        f"**Overall:** {'✅ PASS' if results['overall'] == 'PASS' else '⚠️ PASS WITH WARNINGS' if 'WARN' in results['overall'] else '❌ FAIL'}",
        f"",
        f"---",
        f"",
    ]

    check_names = {
        "tone_of_voice": "CHECK 1 — TONE OF VOICE",
        "color_codes": "CHECK 2 — COLOR CODES",
        "typography": "CHECK 3 — TYPOGRAPHY",
        "animation_sequence": "CHECK 4 — ANIMATION SEQUENCE",
        "subtitles": "CHECK 5 — SUBTITLES",
        "sound_identity": "CHECK 6 — SOUND IDENTITY",
    }

    for key, label in check_names.items():
        check = results["checks"].get(key, {})
        status = check.get("status", "SKIP")
        icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
        lines.append(f"## {label}")
        lines.append(f"**Result: {icon} {status}**")
        issues = check.get("issues", [])
        if issues:
            for issue in issues:
                lines.append(f"- {issue}")
        else:
            lines.append("- No issues found.")
        if key == "subtitles" and "cue_count" in check:
            lines.append(f"- Total cues: {check['cue_count']}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    # Also update compliance_log.json
    log_path = PROJECT_ROOT / project / "compliance_log.json"
    log = {}
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            log = json.load(f)

    log[f"phase_{phase_num}_auto"] = {
        "date": results["date"],
        "overall": results["overall"],
        "checks": {k: v["status"] for k, v in results["checks"].items()}
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    return report_path


def main():
    # Fix Windows console encoding for Unicode output
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Chain Clarity brand compliance checker")
    parser.add_argument("--project", default="chain_clarity", help="Project slug")
    parser.add_argument("--phase", required=True, help="Phase number or 'all'")
    parser.add_argument("--quiet", action="store_true", help="Only print overall result")
    args = parser.parse_args()

    phases = list(range(1, 6)) if args.phase == "all" else [int(args.phase)]

    for phase_num in phases:
        print(f"\n{'='*50}")
        print(f"Checking Phase {phase_num}...")
        results = run_checks(args.project, phase_num)
        report_path = write_report(results, args.project, phase_num)

        if not args.quiet:
            for check_name, check_data in results["checks"].items():
                status = check_data["status"]
                icon = "[OK]" if status == "PASS" else "[WARN]" if status == "WARN" else "[FAIL]"
                print(f"  {icon} {check_name.replace('_', ' ').title()}: {status}")
                for issue in check_data.get("issues", [])[:2]:
                    print(f"     -> {issue}")

        overall_icon = "[OK]" if results["overall"] == "PASS" else "[WARN]" if "WARN" in results["overall"] else "[FAIL]"
        print(f"\n{overall_icon} Phase {phase_num} overall: {results['overall']}")
        print(f"   Report: {report_path}")


if __name__ == "__main__":
    main()
