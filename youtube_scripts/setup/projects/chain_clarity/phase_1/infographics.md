# Infographic Layout Specs — Phase 1
## Chain Clarity · Agent 6 — Infographic Designer

**Reads from:** script.md (phase 1), brand_profile.json
**Produces:** 4 card layout specs for Agent 12 (Asset Generator)

---

## CARD 01 — "WHAT IS A BLOCK?"

**Export format:** Instagram Post 1080×1080px (primary) · YouTube Thumbnail 1280×720px (secondary)
**Script reference:** Section 2, 2:30–5:00
**Layout type:** Anatomy diagram — labelled component breakdown

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  WHAT IS A BLOCK?          ← headline (72px+, teal)│
│  ─────────────────                                  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  [BLOCK ICON · hex outline in teal]          │  │
│  │                                              │  │
│  │  ① DATA              transaction records     │  │
│  │  ② TIMESTAMP         exact sealing moment   │  │
│  │  ③ HASH              digital fingerprint    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  "~2,000–3,000 transactions per block"  ← stat    │
│                                                     │
│  [bottom-right: Chain Clarity wordmark · 36px]     │
└─────────────────────────────────────────────────────┘
```

### Text Content (max 7 words per line — enforced)

- **Headline:** WHAT IS A BLOCK? [6 words ✓]
- **Label 1:** DATA: Transaction records inside [5 words ✓]
- **Label 2:** TIMESTAMP: Exact sealing moment [4 words ✓]
- **Label 3:** HASH: A digital fingerprint [4 words ✓]
- **Stat:** ~2,000 transactions per Bitcoin block [5 words ✓]
- **Sub-stat:** "One block = one sealed ledger page" [7 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline text | Electric Teal | #00D4AA |
| Label numbers (①②③) | Deep Gold | #F5A623 |
| Label titles (DATA etc.) | White | #FFFFFF |
| Label descriptions | Slate | #8B9BB4 |
| Block hex outline | Electric Teal | #00D4AA |
| Stat number | Deep Gold | #F5A623 |
| Stat label | Slate | #8B9BB4 |

### Animation Entry (Agent 12 to implement)

1. Background fade-in (0.2s ease-out)
2. Logo mark slides from top (0.3s ease-out)
3. Headline types word-by-word (80ms/word typewriter)
4. Block hex outline draws in (stroke animation, 0.6s)
5. Label rows slide up, staggered 0.15s between each
6. Stat counts up: 0 → 2,000 (1s easeOutCubic)
7. Wordmark fades in (0.3s)

---

## CARD 02 — "THE HASH: A DIGITAL FINGERPRINT"

**Export format:** Instagram Post 1080×1080px · Stories 1080×1920px
**Script reference:** Section 3, 5:00–7:15
**Layout type:** Input/Output demo with contrast callout

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  THE HASH FINGERPRINT      ← headline (teal, 80px) │
│                                                     │
│  INPUT           →        OUTPUT                   │
│  ───────────               ────────────────────    │
│  "Hello"                  185f8db32921bd46...       │
│                                                     │
│  "Hello!"                 334d016f755cd6dc...       │
│                                                     │
│  ══════════════════════════════════════════════    │
│  1 CHARACTER CHANGE                                 │
│  COMPLETELY DIFFERENT FINGERPRINT        ← violet  │
│  ══════════════════════════════════════════════    │
│                                                     │
│  "You can't predict it.    ← body (slate, 48px)   │
│   You can't reverse it."                           │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content

- **Headline:** THE HASH FINGERPRINT [3 words ✓]
- **Column heads:** INPUT [1 word ✓] · OUTPUT [1 word ✓]
- **Input row 1:** "Hello" [1 word ✓]
- **Output row 1:** 185f8db32921bd46d3... [hash, truncated — JetBrains Mono]
- **Input row 2:** "Hello!" [1 word ✓]
- **Output row 2:** 334d016f755cd6dc58... [hash, truncated — JetBrains Mono]
- **Key insight line 1:** 1 CHARACTER CHANGE → [4 words ✓]
- **Key insight line 2:** 100% DIFFERENT FINGERPRINT [3 words ✓]
- **Body line 1:** You can't predict it. [5 words ✓]
- **Body line 2:** You can't reverse it. [5 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline | Electric Teal | #00D4AA |
| "INPUT" label | Slate | #8B9BB4 |
| "OUTPUT" label | Slate | #8B9BB4 |
| Hash output text | Deep Gold | #F5A623 (JetBrains Mono) |
| Key insight text | Electric Violet | #7B5CF0 |
| Key insight background strip | rgba(#7B5CF0, 12%) | — |
| Body text | Slate | #8B9BB4 |
| Arrow (→) | Electric Teal | #00D4AA |
| Divider lines | rgba(#8B9BB4, 30%) | — |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline typewriters in (80ms/word)
4. INPUT label slides up (0.4s)
5. First input/output pair fades in (0.4s delay)
6. Second input/output pair fades in (0.3s stagger after first)
7. Key insight strip bounces in from bottom (0.5s spring)
8. Body text slides up (0.4s)

---

## CARD 03 — "BLOCKS ARE LINKED BY HASHES"

**Export format:** Instagram Post 1080×1080px · YouTube Thumbnail 1280×720px
**Script reference:** Section 4, 7:15–9:00
**Layout type:** Chain diagram — sequential blocks with hash pointer arrows

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  THE CHAIN LINK            ← headline (teal, 80px) │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ BLOCK 99 │───▶│BLOCK 100 │───▶│BLOCK 101 │      │
│  │          │    │          │    │          │      │
│  │ data     │    │ data     │    │ data     │      │
│  │ time     │    │ time     │    │ time     │      │
│  │ hash:99x │    │prev:99x  │    │prev:100x │      │
│  └──────────┘    └──────────┘    └──────────┘      │
│          ↑ stored here ──────────────────┘          │
│                                                     │
│  "Change Block 99 →       ← body (slate)           │
│   Block 100 breaks."                               │
│                                                     │
│  PREV_HASH IS THE CHAIN    ← violet callout        │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content

- **Headline:** THE CHAIN LINK [3 words ✓]
- **Block labels:** BLOCK 99 · BLOCK 100 · BLOCK 101 [2 words each ✓]
- **Block rows:** data · time · hash: [internal labels]
- **Prev hash labels:** prev: 99x · prev: 100x [JetBrains Mono, gold]
- **Body line 1:** Change Block 99. [3 words ✓]
- **Body line 2:** Block 100 breaks. [3 words ✓]
- **Callout:** PREV_HASH IS THE CHAIN [5 words ✓]
- **Arrow label:** hash stored here [3 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline | Electric Teal | #00D4AA |
| Block borders | Electric Teal | #00D4AA |
| Block fill | rgba(#00D4AA, 8%) | — |
| Block labels (BLOCK N) | White | #FFFFFF |
| Block row text | Slate | #8B9BB4 |
| prev_hash values | Deep Gold | #F5A623 (JetBrains Mono) |
| Arrow connectors | Deep Gold | #F5A623 |
| PREV_HASH callout | Electric Violet | #7B5CF0 |
| Body text | Slate | #8B9BB4 |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline typewriters in (80ms/word)
4. Block 99 slides in from left (0.4s)
5. Arrow draws from Block 99 to Block 100 (0.4s stroke)
6. Block 100 slides in (0.15s stagger after arrow)
7. Arrow draws to Block 101 (0.4s)
8. Block 101 slides in (0.15s stagger)
9. Callout bounces in from below (0.3s spring)
10. Body text slides up (0.4s)

---

## CARD 04 — "TAMPER ONE. BREAK THE CHAIN."

**Export format:** Instagram Post 1080×1080px · Stories 1080×1920px
**Script reference:** Section 4 (immutability cascade), 7:30–9:00
**Layout type:** Cascade failure diagram — dramatic visual

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  TAMPER WITH ONE.          ← line 1 (white, 80px)  │
│  BREAK THE CHAIN.          ← line 2 (teal, 80px)   │
│                                                     │
│  [BLOCK 500] ← attacker alters this                 │
│  [#F5A623 ✗ symbol · "HASH CHANGED"]               │
│      ↓                                              │
│  [BLOCK 501] ← now invalid [red border]             │
│      ↓                                              │
│  [BLOCK 502] ← now invalid [red border]             │
│      ↓                                              │
│  [BLOCK 503...] ← cascade continues [red border]   │
│                                                     │
│  ══════════════════════════════════════════════    │
│  THE PAST CANNOT           ← line 1 (violet)       │
│  BE REWRITTEN.             ← line 2 (violet)       │
│  ══════════════════════════════════════════════    │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content

- **Headline line 1:** TAMPER WITH ONE. [3 words ✓]
- **Headline line 2:** BREAK THE CHAIN. [3 words ✓]
- **Altered block label:** BLOCK 500: ALTERED [3 words ✓]
- **Hash changed label:** HASH CHANGED [2 words ✓]
- **Invalid block label:** NOW INVALID [2 words ✓]
- **Cascade label:** CASCADE CONTINUES... [2 words ✓]
- **Conclusion line 1:** THE PAST CANNOT [3 words ✓]
- **Conclusion line 2:** BE REWRITTEN. [2 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline line 1 | White | #FFFFFF |
| Headline line 2 | Electric Teal | #00D4AA |
| Altered block border | Deep Gold | #F5A623 |
| Altered block ✗ icon | Deep Gold | #F5A623 |
| Invalid block borders | #EF4444 (danger red — one-time exception, not brand) | #EF4444 |
| Invalid block fill | rgba(#EF4444, 10%) | — |
| Cascade arrows | #EF4444 | #EF4444 |
| Conclusion callout | Electric Violet | #7B5CF0 |
| Conclusion bg strip | rgba(#7B5CF0, 12%) | — |

**Design note:** The red (#EF4444) is a deliberate, one-time semantic exception for "danger/failure" state only. It is not a brand color. Use it only on this card's invalid blocks. Every other element remains on brand HEX codes.

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline line 1 typewriters in (80ms/word)
4. Headline line 2 typewriters in (80ms/word, 0.2s delay)
5. Block 500 slides in with gold border pulsing (0.5s)
6. ✗ icon and "HASH CHANGED" stamp appears (0.3s)
7. Arrow drops down (0.3s)
8. Block 501 slides in with red border (0.3s)
9. Blocks 502, 503 cascade in with stagger (0.2s each)
10. Conclusion strip bounces in (0.4s spring)

---

**Next Step:** `🖼️ INFOGRAPHIC DESIGNER complete → 🎨 /preview 1 (Agent 12)`
