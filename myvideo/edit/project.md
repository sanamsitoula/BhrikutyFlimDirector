# Docker DevOps Ep.1 — Project Log

## Session 1 — 2026-05-27

**Goal:** Edit clip1.mp4 (screen recording), clip2.mp4 (B-roll), info.png (infographic), and profile photos (p1.jpg, p2.jpg) into a 2–3 minute YouTube video for a bilingual Nepali+English Docker installation tutorial.

**Source material:**
- `clip1.mp4` — 87.2s screen recording of Docker install walkthrough (silent)
- `clip2.mp4` — 16s B-roll / hook footage
- `info.png` — DevOps/Docker infographic (2752×1536)
- `p1.jpg`, `p2.jpg` — host profile photos
- `voice.html` — editorial script (6 scenes, Hook → Shipping Container → Wall of Confusion → DevOps Roadmap → Install Steps → Outro)

**Strategy decisions:**
- No voiceover available — text-only labels approach; user will add voice later
- PIL frame-by-frame animation for host intro card and outro card
- ffmpeg zoompan Ken Burns for infographic (slow zoom 100%→108% over 34s)
- Neutral punch color grade (contrast +6%) on both clip segments
- ffmpeg drawtext overlays (not libass/ASS — libass font cache unreliable on this Windows build)
- Ambient music synthesized via ffmpeg aevalsrc (55Hz drone + harmonics, 175s)

**Timeline structure:**
| Segment | Source | Duration | Content |
|---------|--------|----------|---------|
| slot_1 | PIL animation | 12s | Host intro card — p1.jpg, dot grid, microphone, title |
| seg_clip2 | clip2 0–16s | 16s | Hook B-roll — "IT WORKS ON MY MACHINE!" |
| slot_2 | info.png zoompan | 34s | Infographic — Wall of Confusion → DEVOPS → DOCKER |
| seg_clip1 | clip1 0–87.2s | 87s | Install walkthrough — STEP 1–6 labels |
| slot_3 | PIL animation | 20s | Outro — Subscribe CTA, Ep. 2 teaser |

**Text overlays (drawtext, y=18 top-center):**
- 12.5–18s: "IT WORKS ON MY MACHINE!" white bold 40px
- 18.5–24.5s: "The 4 most dangerous words in software" gray 28px
- 24.8–27.8s: "Docker solves this." blue bold 32px
- 29.5–62s: Infographic section labels (amber/blue/green)
- 62.5–149s: STEP 1–6 installation labels (white/green)

**Key files:**
- `final.mp4` — 2:49, 26.5MB, 1920×1080@24fps ✓
- `base.mp4` — lossless concat of all 5 segments, 2:49, 24MB
- `animations/slot_1/render.mp4` — 12s intro card
- `animations/slot_2/render.mp4` — 34s infographic zoom
- `animations/slot_3/render.mp4` — 20s outro card
- `clips_graded/seg_clip1.mp4` — graded clip1
- `clips_graded/seg_clip2.mp4` — graded clip2
- `music/ambient.mp3` — 175s synthesized ambient
- `burn_text.py` — drawtext render script
- `master.ass` — ASS file (authored but not used — drawtext used instead)

**Issues encountered:**
- libass font cache failure on Windows: ASS/SRT subtitles rendered silently with no text. Workaround: explicit `fontfile=` in drawtext bypasses libass entirely.
- PowerShell colon parsing in aevalsrc expressions: fixed by assigning expression to a variable before interpolation.

**Self-eval:** 4 subtitle frames sampled via timeline_view — all passed. Text visible, colors correct, no overlay collisions.

**Next session:** Add voiceover audio to final.mp4 (user will supply). Consider adding Nepali subtitle track.
