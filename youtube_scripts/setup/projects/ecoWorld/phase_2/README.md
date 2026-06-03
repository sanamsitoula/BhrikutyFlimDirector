# Eco World — Phase 2 Production Checklist

> Complete each step in order. Do not skip steps.

## Pre-Production
- [ ] Topic confirmed and approved
- [ ] Outline written (3–5 key points)
- [ ] Duration decided (default: 12 min)
- [ ] Tags and keywords prepared

## Step 1 — Script Generation
```
python pipeline.py --project ecoWorld --phase 2 --topic "Your Topic" --outline "Your outline" --duration 12
```
- [ ] `script.md` generated (> 1,000 words)
- [ ] `script_short.md` generated (60-second cut)
- [ ] `voiceover_brief.md` generated
- [ ] `clip_brief.md` generated
- [ ] `subtitles.srt` generated

## Step 2 — Compliance Check
```
python tools/compliance_checker.py --project ecoWorld --phase 2
```
- [ ] `compliance_report_auto.md` status is PASS or PASS_WITH_WARNINGS
- [ ] No FAIL items in the report
- [ ] Forbidden words not present

## Step 3 — Infographic Cards
```
# (auto-generated in Step 1 — check infographic_assets/)
```
- [ ] `infographic_assets/card_01.html` exists
- [ ] `infographic_assets/card_02.html` exists
- [ ] All cards use brand colors only
- [ ] Cards pass visual review

## Step 4 — Voiceover
```
python tools/tts/kokoro_voiceover.py --phase 2 --project ecoWorld
```
- [ ] `voiceover/phase_2.wav` exists
- [ ] Audio is clean — no clipping, noise
- [ ] Pacing matches voiceover_brief.md
- [ ] Duration matches target

## Step 5 — Video Assembly
- [ ] Raw footage captured / sourced
- [ ] Video assembled with voiceover
- [ ] Subtitles burned (if required)
- [ ] Final video exported as 1920×1080 MP4

## Step 6 — Platform Cuts
```
python tools/platform_cutter.py --project ecoWorld --phase 2 --video _output/phase_02/final.mp4
```
- [ ] `_output/phase_02/youtube/final_1080p.mp4`
- [ ] `_output/phase_02/tiktok/clip_01_hook.mp4`
- [ ] `_output/phase_02/instagram/reel_60s.mp4`
- [ ] `_output/phase_02/twitter/card_clip.mp4`

## Step 7 — Text Content
```
python tools/text_content_generator.py --project ecoWorld --phase 2
```
- [ ] `_output/phase_02/youtube/description.txt`
- [ ] `_output/phase_02/twitter/thread.txt`
- [ ] `_output/phase_02/linkedin/article.md`
- [ ] `_output/phase_02/blog/post.md`

## Step 8 — Review & Publish
- [ ] All files reviewed by a human
- [ ] YouTube video uploaded + description added
- [ ] TikTok clips uploaded
- [ ] Instagram reel + carousel posted
- [ ] Twitter thread posted
- [ ] LinkedIn article published
- [ ] Blog post published

---
*Bhrikuty Film Director — Phase 2 of 5*
