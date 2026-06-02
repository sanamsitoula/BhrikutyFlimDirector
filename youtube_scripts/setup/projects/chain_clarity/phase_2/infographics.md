# Infographic Layout Specs — Phase 2
## Chain Clarity · Agent 6 — Infographic Designer

**Phase 2 card count:** 3 cards
**Script sections covered:** Section 2 (PoW), Section 3 (21M cap/halvings), Section 4 (BTC vs ETH)

---

## CARD 01 — "PROOF OF WORK vs PROOF OF STAKE"

**Export format:** Instagram Post 1080×1080px · YouTube Thumbnail 1280×720px
**Script reference:** Sections 2 & 5
**Layout type:** Two-column comparison table

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  PROOF OF WORK               ← headline (white)    │
│  vs PROOF OF STAKE           ← sub (teal)           │
│  ──────────────────────────────────────────────    │
│                                                     │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │  PoW         │    │  PoS                     │  │
│  │  [gold col]  │    │  [violet col]            │  │
│  ├──────────────┤    ├──────────────────────────┤  │
│  │ HOW:         │    │ HOW:                     │  │
│  │ Solve puzzle │    │ Lock collateral          │  │
│  ├──────────────┤    ├──────────────────────────┤  │
│  │ ENERGY:      │    │ ENERGY:                  │  │
│  │ Very high    │    │ Minimal (−99.9%)         │  │
│  ├──────────────┤    ├──────────────────────────┤  │
│  │ SECURITY:    │    │ SECURITY:                │  │
│  │ Energy cost  │    │ Slashing risk            │  │
│  ├──────────────┤    ├──────────────────────────┤  │
│  │ USED BY:     │    │ USED BY:                 │  │
│  │ Bitcoin      │    │ Ethereum (post-Merge)    │  │
│  └──────────────┘    └──────────────────────────┘  │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content (7 words max per line)

- **Headline:** PROOF OF WORK [3 words ✓]
- **Sub-headline:** vs PROOF OF STAKE [4 words ✓]
- **Col 1 header:** PoW [1 word ✓]
- **Col 2 header:** PoS [1 word ✓]
- **Row 1 label:** HOW IT WORKS [3 words ✓]
- **Row 1 PoW:** Solve a hash puzzle [4 words ✓]
- **Row 1 PoS:** Lock ETH as collateral [4 words ✓]
- **Row 2 label:** ENERGY USE [2 words ✓]
- **Row 2 PoW:** Very high (~150 TWh/yr) [3 words ✓]
- **Row 2 PoS:** −99.9% after The Merge [4 words ✓]
- **Row 3 label:** SECURITY MODEL [2 words ✓]
- **Row 3 PoW:** Energy cost = attack cost [5 words ✓]
- **Row 3 PoS:** Cheating burns your stake [4 words ✓]
- **Row 4 label:** USED BY [2 words ✓]
- **Row 4 PoW:** Bitcoin [1 word ✓]
- **Row 4 PoS:** Ethereum (since Sept 2022) [4 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline "PROOF OF WORK" | White | #FFFFFF |
| "vs PROOF OF STAKE" | Electric Teal | #00D4AA |
| PoW column header | Deep Gold | #F5A623 |
| PoW column border | Deep Gold | #F5A623 |
| PoS column header | Electric Violet | #7B5CF0 |
| PoS column border | Electric Violet | #7B5CF0 |
| Row labels | Slate | #8B9BB4 |
| Row content text | White | #FFFFFF |
| "−99.9%" stat | Electric Teal | #00D4AA |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline typewriters in (80ms/word)
4. PoW column slides in from left (0.4s)
5. PoS column slides in from right (0.4s, 0.2s stagger)
6. Row content reveals row-by-row (0.3s stagger, 0.15s between rows)
7. "−99.9%" stat counts up with color (0.6s)

---

## CARD 02 — "BITCOIN'S 21 MILLION HARD CAP"

**Export format:** Instagram Post 1080×1080px · Stories 1080×1920px
**Script reference:** Section 3
**Layout type:** Halving timeline + dominant stat

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  21,000,000          ← giant counter, teal, 120px  │
│  MAXIMUM BTC. EVER.  ← sub (gold, 52px)            │
│                                                     │
│  HALVING TIMELINE                                   │
│  ─────────────────────────────────────────────    │
│  2009   2012   2016   2020   2024   ~2140          │
│   50     25    12.5   6.25  3.125    0             │
│  BTC/   BTC/  BTC/   BTC/  BTC/  (last            │
│  block  block block  block block  coin)            │
│                                                     │
│  ═══════════════════════════════════════════════  │
│  ~19.7M already mined · 1.3M remaining            │
│  ═══════════════════════════════════════════════  │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content

- **Big stat:** 21,000,000 [counter animation]
- **Stat label:** MAXIMUM BTC. EVER. [3 words ✓]
- **Section head:** HALVING TIMELINE [2 words ✓]
- **Timeline years:** 2009 · 2012 · 2016 · 2020 · 2024 · ~2140 [JetBrains Mono]
- **Rewards:** 50 · 25 · 12.5 · 6.25 · 3.125 [JetBrains Mono, gold]
- **Sub-label per year:** BTC/block [2 words ✓]
- **~2140 label:** last coin [2 words ✓]
- **Footer stat line 1:** ~19.7M already mined [4 words ✓]
- **Footer stat line 2:** 1.3M remaining [2 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| 21M stat number | Electric Teal | #00D4AA |
| "MAXIMUM BTC. EVER." | Deep Gold | #F5A623 |
| Timeline bar | Electric Teal | #00D4AA |
| Year labels | Slate | #8B9BB4 |
| Reward values | Deep Gold | #F5A623 (JetBrains Mono) |
| "BTC/block" labels | Slate | #8B9BB4 |
| ~2140 label | Electric Violet | #7B5CF0 |
| Footer strip bg | rgba(#F5A623, 6%) | — |
| Footer text | Slate | #8B9BB4 |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. "21,000,000" counts up from 0 (1.2s easeOutCubic)
4. "MAXIMUM BTC. EVER." typewriters in word-by-word (80ms/word)
5. Timeline bar draws left-to-right (0.8s ease-out)
6. Year + reward labels appear left-to-right with stagger (0.12s between each)
7. ~2140 "last coin" label bounces in (0.3s spring)
8. Footer stat strip slides up (0.4s)

---

## CARD 03 — "BITCOIN = MONEY · ETHEREUM = COMPUTER"

**Export format:** Instagram Post 1080×1080px · YouTube Thumbnail 1280×720px
**Script reference:** Section 4
**Layout type:** Side-by-side comparison with visual metaphor

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  TWO TOOLS.          ← headline (white, 88px)      │
│  DIFFERENT JOBS.     ← sub (teal, 88px)            │
│                                                     │
│  ┌─────────────────┐   ┌─────────────────────────┐ │
│  │    [BTC hex]    │   │     [ETH hex]           │ │
│  │    gold stroke  │   │     violet stroke       │ │
│  │                 │   │                         │ │
│  │   BITCOIN       │   │   ETHEREUM              │ │
│  │                 │   │                         │ │
│  │  Send & receive │   │  Run code on-chain      │ │
│  │  value          │   │                         │ │
│  │                 │   │  Smart contracts:       │ │
│  │  Fixed supply   │   │  IF/THEN logic          │ │
│  │  Currency       │   │  runs automatically     │ │
│  └─────────────────┘   └─────────────────────────┘ │
│                                                     │
│  ═══════════════════════════════════════════════  │
│  ETHEREUM ADDED THE IF/THEN   ← violet callout    │
│  ═══════════════════════════════════════════════  │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content

- **Headline:** TWO TOOLS. [2 words ✓]
- **Sub-headline:** DIFFERENT JOBS. [2 words ✓]
- **BTC panel title:** BITCOIN [1 word ✓]
- **BTC line 1:** Send & receive value [4 words ✓]
- **BTC line 2:** Fixed supply [2 words ✓]
- **BTC line 3:** Currency only [2 words ✓]
- **ETH panel title:** ETHEREUM [1 word ✓]
- **ETH line 1:** Run code on-chain [4 words ✓]
- **ETH line 2:** IF/THEN logic runs [4 words ✓]
- **ETH line 3:** automatically, no server [3 words ✓]
- **Callout:** ETHEREUM ADDED THE IF/THEN [5 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline "TWO TOOLS." | White | #FFFFFF |
| "DIFFERENT JOBS." | Electric Teal | #00D4AA |
| Bitcoin hex border | Deep Gold | #F5A623 |
| Bitcoin hex fill | rgba(#F5A623, 6%) | — |
| "BITCOIN" label | Deep Gold | #F5A623 |
| Bitcoin content text | Slate | #8B9BB4 |
| Ethereum hex border | Electric Violet | #7B5CF0 |
| Ethereum hex fill | rgba(#7B5CF0, 6%) | — |
| "ETHEREUM" label | Electric Violet | #7B5CF0 |
| Ethereum content text | Slate | #8B9BB4 |
| "IF/THEN" highlights | Electric Teal | #00D4AA |
| Callout text | Electric Violet | #7B5CF0 |
| Callout bg | rgba(#7B5CF0, 10%) | — |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline typewriters in (80ms/word)
4. Bitcoin hex outline draws in (stroke, 0.5s)
5. "BITCOIN" label + content slides up (0.4s)
6. Ethereum hex outline draws in (stroke, 0.5s, 0.3s stagger after BTC)
7. "ETHEREUM" label + content slides up (0.4s, 0.15s stagger)
8. Callout strip bounces in (0.3s spring)

---

**Next Step:** `🖼️ INFOGRAPHIC DESIGNER complete → 🎨 /preview 2 (Agent 12)`
